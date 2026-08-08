# Xen Research Pipeline - Shared Configuration

This file is the single source of truth for constants, conventions, and shared knowledge used by all skills in the Xen research pipeline. **Do not duplicate this content in individual skills — reference this file instead.**

---

## Project Paths

All paths are relative to the project root (`{project-root}`).

| Resource | Path |
|----------|------|
| Experiment Directory | `python/experiments/<EXP-ID>/` |
| Analysis Package (`xen`) | `python/src/xen/` |
| Data Files | `data/` |
| Nautilus catalog (primary OHLCV) | `data/catalog/` (ParquetDataCatalog, INFR-011) |
| Strategy-run emissions (Nautilus) | `data/nautilus_runs/<run_id>/` (emission contract v1) |
| Nautilus runner / smoke | `archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-010/scripts/run_phase_b.py`; per-EXP runners under `python/experiments/<ID>/code/` |
| Fence manifest (A6, hash-pinned) | `archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-011/artifacts/fence-manifest.json` |
| Universe census (910 USDT perps) | `archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-011/artifacts/universe-census.md` |
| Archived cTrader emissions | `archive/chapter-03-xena-mtfctx/data/strategy_runs/` (VAL carve-out only) |
| **Knowledge Base (read first)** | `docs/knowledge-base/` (INDEX, lessons-and-amendments, pitfalls-ledger, …) |
| Signal Registry (live ledgers) | `docs/signal-registry/` (multiplicity, test-read, candidate-families) |
| Experiment Index (brief) | `python/experiments/INDEX.md` |
| Master Index (nav + live status) | `docs/experiments-docs/INDEX.md` |
| Family Detail Indexes | `docs/experiments-docs/families/<family>/INDEX.md` |
| Checkpoint Directory | `docs/experiments-docs/checkpoints/` |
| Reference Documents | `docs/references/` |
| Architecture Doc | `docs/references/architecture.md` |
| Dataset Reference | `docs/references/dataset-reference.md` |

### Per-Experiment Structure (INFR-001)

```
python/experiments/<EXP-ID>/
├── design.md          # quant-designer: mechanism-first scope + plan (mandatory declaration blocks)
├── qa-review.md       # qa-compliance: fresh-context pre-exec review — APPEND-ONLY across reruns
├── code/              # developer: Nautilus strategy/runner refs + config notes (NO Python analysis code)
├── analysis_code/     # data-analyst's own interrogation scripts (canonical xen estimands only)
├── results/           # incl. estimand_validation.json (blocking gate artifact)
├── plots/
├── analysis.md        # data-analyst: evidence FOR+AGAINST + recommended verdict — UNCAPPED
└── report.md          # documenter: record incl. the OPERATOR's final verdict
```

Governance: QA runs pre-execution in a **fresh context** (subagent or new operator session;
rerunnable; append-only `qa-review.md`). The **execution approval and the final experiment
verdict are operator gates**. Hard blocks are integrity-only (tripwire, holdout, causality,
estimand reconciliation); all quality reads are informative — the operator judges value.

### Artifact verbosity discipline (format, not length)

The guard is **density**, not a line count: wordy prose, hedging, and restated
points waste input tokens and bury the signal. Prefer tables, bullets, fragments, and
named facts over paragraphs. The line figures below are budgets that flag *bloat to
compress*, not hard truncation — a dense artifact may exceed them; a padded one must be
compressed, never thinned of substance.

| Artifact | Budget | Density rule |
|----------|--------|--------------|
| `design.md` | ~300 lines | merged scope+plan; tables/bullets, no prose padding |
| `report.md` | ~400 lines | operator verdict + evidence record; key plots only |
| `analysis.md` | **uncapped** | interrogation/evidence work needs room — but still terse |
| `qa-review.md` | per-run sections | append-only; table-format traces |
| registry updates | concise rows only | evidence rows only mid-experiment; no status transitions |

**Compression tool (mandatory on prose-heavy artifacts).** When `design.md` / `report.md`
(or a KB doc) reads wordy, run the `caveman` plugin: `/caveman-compress <abs-path>`. It
strips articles/filler/hedging and compresses prose to terse format while preserving
**code, tables, file paths, numbers, and headings exactly** (it writes a `<file>.original.md`
backup — delete it before commit; do not commit backups). Never run it on `code/` or other
non-prose files. Compression is a formatting pass — it must not drop a fact, a number, or a
verdict.

### Operator-facing communication (binding — all skills, all stages)

Applies to **every message meant for the human operator**: questions asking for a decision
or opinion, status updates, progress reports, stage handoffs, gate prompts, summaries,
recommendations, and completion notes.

Does **not** force on-disk technical artifacts (`design.md`, `analysis.md`, code, QA tables)
to drop domain terms — those stay precise for the record. When you **tell the operator**
about those artifacts, **translate**.

| Rule | Requirement |
|------|-------------|
| **Plain first** | Lead with what happened and what it means for the decision. Process/skill jargon is never the lead. |
| **Concise** | Status default ≤8 short lines; summary default ≤15 unless the operator asked for depth. Bullets over paragraphs. |
| **De-jargonify** | Replace internal labels with plain meaning. If a label is needed once, put it in parentheses after the plain phrase. |
| **Decisions, not dumps** | For a gate: state the decision needed; give 2–4 options with one-line consequences; mark the recommendation. |
| **One ask at a time** | One plain sentence per question (or a short list of independent questions). No compound nested questions. |
| **Keep useful numbers** | Effect sizes, sample sizes, costs stay — but say what they mean in words first. |
| **20-second test** | Before send: could a smart non-specialist who owns this project understand it in ~20 seconds? If not, rewrite. |

**Bad:** "estimand_validation `blocking_pass` failed on provenance; SPREAD-SCALE-ROUTING
`t1_undecidable`; awaiting operator gate before LAHC."

**Good:** "The integrity check failed: we cannot prove decisions only used past data. Results
are not clean yet. I need your call: (A) fix and re-run — recommended, or (B) stop here."

**Status / summary template:**
```
**Where we are:** <one line>
**What happened:** <1–3 plain bullets>
**What it means:** <1–2 bullets>
**Need from you:** <decision, or "nothing — continuing">
```

**Question template:**
```
**Question:** <one plain sentence>
**Options:**
- A — <one-line consequence>  ← recommended
- B — <one-line consequence>
**Why A:** <one line>
```

If a question cannot be stated plainly, the asker does not understand it yet — investigate
first; do not dump jargon on the operator.

### Checkpoint Structure (Phase-Based Documentation)

```
docs/experiments-docs/checkpoints/<phase-timestamp>-<phase-name>/
├── design.md                   # Phase objectives, plans, methodology
└── retrospective.md            # Phase outcomes, lessons learned
```

The `design.md` of the latest checkpoint serves as the guide for the current phase's experimentation pipeline execution.

---

## Data Architecture (v2 — Nautilus + Bybit catalog)

Two-lane model (INFR-010 §4):

| Lane | Tier | Data | Path |
|------|------|------|------|
| **Primary** | T1 | 1m OHLCV from Bybit trades; **zero-cost model** (no fees/funding/spread charged) | `data/catalog/` |
| **Signed-volume** | T1 | Exact taker buy/sell volume plus quarantined mean-price skew | `data/catalog/` |

Secondary MBP/L2 data is unavailable and is not an active branch. **Zero-cost model
(INFR-022, binding):** no spread, commission, or swap enters any calculation in any
experiment type unless an explicit operator cost directive requests costs (recorded in the
experiment's design.md before execution). Every report, analysis, screen and results
artifact carries the zero-cost caveat verbatim (§ Zero-cost model below).

- **Universe:** 910 USDT linear perpetuals (listed + delisted), census at INFR-011 A1.
- **InstrumentId:** `{SYMBOL}-LINEAR.BYBIT` via `xen.nautilus.instrument_ids`.
- **History cap:** trailing 4 years per symbol; global calendar fence (A6).
- **Chart-type generators:** dormant on new stack until ported.

Full schemas: `docs/references/dataset-reference.md` v2, `docs/references/architecture.md` v2.

### Emission contract v1 (strategy runs)

`data/nautilus_runs/<run_id>/` — `bar_marks.parquet`, `positions_ledger.parquet`, fills,
orders, `event_log.jsonl`, `fence_attestation.json`. Shim: `xen.nautilus.adjudication_shim`.
Spec: `archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-010/code/emission_contract_v1.md`.

**STUB fence attestations (Phase B smokes) fail estimand gate v2** — production runs require
INFR-011 A6 hash-pinned manifest.

## Zero-cost model (binding — INFR-022 directive 1)

Programme-wide (all lanes — XENA, SPDR, EXP): **no spread, commission, or swap enters any
calculation in any experiment type**, unless an explicit operator directive requests costs.

* "Zero" is a *model*, not a measurement: absence of cost is never reported as "measured
  zero cost"; the caveat text below is mandatory instead.
* A cost directive is experiment-scoped: it may not be inferred from any other experiment's
  directive, and it is recorded in the design before execution (QA traces it).
* Deployability/tradability claims remain refused by rule — the zero-cost model does not
  loosen them.
* The retired cost stack lives in `xen/evaluation_cost_legacy.py` (ARCHIVED banner; not
  callable from any live research path).
* Live mechanics: `cost_bps`/`charge_costs`/`spread_*` parameters are inert (pinned 0 /
  False) and enforced by code asserts; non-zero `--cost-bps` / `charge_costs=True` require
  `operator_cost_directive.json` (operator-signed reason + scope).

**Canonical caveat text (must appear VERBATIM on every report/analysis/results document):**

```text
ZERO-COST-DISCLOSURE
  cost_model: NO_COST_CHARGED
  spread: not modeled
  commissions: not modeled
  swaps/funding: not modeled
  implication: every figure in this document is gross and cost-free; no spread,
    commission, or swap enters any calculation. Realised results would differ
    (likely worse) under any real cost schedule.
  prohibited_claims: fully-net, cost-complete, tradable, deployable
  lifting: only an explicit operator directive may introduce a cost model for a
    scoped experiment; the directive is recorded in that experiment's design.md.
```

## Neutrality standard (binding — INFR-022 directive 2)

The extracted chapter-05 neutrality canon is codified in **`docs/references/neutrality-standard.md`**
(N1–N11). It is **binding** on every analysis, screen, report and results artifact: no-verdict
boundary statements, observed-vs-inference labelling, counts as context (never hide/drop
rules), direct comparisons against a pre-specified comparator only, populations named and
separated, controls informative (the leak tripwire is the only blocking control, on the
SE-family `INTEGRITY_Z × bootstrap_SE` scale — never an MDE), symmetric evidence, analyst
independence, the zero-cost caveat on every document, completeness, and operator-only value
labels. Skill files bind N1–N11 in their own contracts; this file binds them globally.

## Powering strip (binding — INFR-022 directive 3)

**Retained (the only powering-adjacent methods):** sample-size *context* (expected counts,
optional minimum-n notes for primary-inference language — never a hide/drop rule, never a
resolve rule) and DIRECT comparisons against a pre-specified baseline model. **Stripped:**
MDE, detection floors (`2.8/√n`, `MDE_Z × SE`), mechanism ceilings, power curves, "at
power"/"unpowered" language, and every machine-assigned power/resolution label. PSR is
evidence, never a gate.

---

## OOS Holdout Rules

**These rules are non-negotiable and enforced by governance at every stage.**

Xen data is temporally ordered. The holdout split must respect chronological ordering.

### Nested Chronological Split

```
Full admitted catalog range (ordered by ts_event / SourceCloseTime)
├── First 70% = ANALYSIS SET (used for all experiments)
│   ├── First 70% of analysis set = TRAIN SET
│   └── Last 30% of analysis set = TEST SET
└── Final 30% = GLOBAL HOLDOUT (never used)
```

### Rules

1. **Never load, inspect, or use the final 30%** of the dataset in any capacity.
2. All analysis, training, testing, and validation uses only the first 70%.
3. Within the analysis set, use a 70/30 chronological train/test split.
4. The holdout is a **global reserve** — it persists across all experiments.
5. Any experiment that touches the holdout set is a **governance violation**.
6. **Never use future data** — when analyzing a chart-type event, only use data available at or before that event's timestamp.

### Code Pattern

```python
# Use INFR-011 A6 fence manifest — absolute calendar dates, not ad-hoc row fractions.
# Catalog query wrapper enforces holdout_start_utc; never read past it.
from pathlib import Path
import json

manifest = json.loads(
    Path("archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-011/artifacts/fence-manifest.json").read_text()
)
train_end = manifest["train_end_utc"]
holdout_start = manifest["holdout_start_utc"]
# Query catalog with ts_event <= train_end for TRAIN; TEST band between train_end and holdout_start
# holdout_start → NEVER QUERY
```

---

## Programme Principles

These binding constraints apply to all Xen research.

| Principle | Description |
|-----------|-------------|
| **Simplicity over complexity** | Always choose the simplest, most robust approach that answers the question. Justify complexity before using it. |
| **No academic-finance pitfalls** | Reject techniques relying on assumptions known to fail in real markets (normality, stationarity, i.i.d., constant volatility). Prefer empirical/bootstrap/permutation methods. |
| **Data-driven** | Conclusions emerge from data, not assumptions. No pre-conceived shapes or distributions. |
| **Non-parametric by default** | Distribution-free methods first. Parametric only with non-parametric cross-validation. |
| **Real-price outcome discipline** | Strategy, signal-quality, and return outcomes use real time-bar prices unless a scope explicitly defines a non-tradable diagnostic. Heiken Ashi prices and Renko brick prices are synthetic and never valid for strategy P&L. |
| **Timestamp alignment over bar count** | Cross-view comparisons align by timestamp, never by bar index. |
| **Deterministic generation** | Derived views and feature tables produce identical output from identical input. Randomness is allowed only when the scope requires it and fixes the seed. |
| **Streaming compatibility** | All generators must work as sequential stateful functions (no look-ahead). |
| **Human-in-the-loop** | All plans, designs, implementations, and conclusions require explicit approval (standard mode) or clear governance verdicts (executor mode). |
| **Single hypothesis per experiment** | Each experiment answers exactly one question. Scope creep is a governance violation. **Carve-out — exploratory SPDR characterisation:** an SPDR may traverse a predeclared grid of components, devices and combinations, under the SPDR characterisation contract in `docs/references/spdr-lane.md`. The carve-out buys breadth, not looseness: every stratum still names its exact comparison and emits its own direct estimate and uncertainty. |
| **Complexity budget enforced** | Every experiment has defined limits on statistical tests, visualisations, and new code modules. |
| **No premature optimisation** | Characterisation phases must not tune strategy parameters, windows, filters, stops, or targets against analysis-set performance. Optimisation requires an explicit phase and scope. |
| **Causal-by-construction execution** | Price-primary experiments run in the **Nautilus event-driven engine** only (`BacktestNode`); Python is analysis-only on emitted runs. A vectorised Python backtest of a price strategy is rejected. (Principle = event sequencing, not C#.) |
| **Evaluate-on-bar-open + lagged reference only** | Every decision at bar **open**, conditioned on **confirmed data ≤ t−1**; `ts_event` ns discipline. Nautilus single-threaded replay enforces sequencing; analysis uses `[t-1]` lag on bar marks. |
| **Open-to-open returns only** | Strategy / signal / P&L returns are measured **open-to-open**, never open-to-close — an `OnClose` execution is impossible in real time (the close is unknown until the bar completes). Close-referenced returns are a non-tradable diagnostic and must be labelled as such. |
| **Leak resistance is audited independently of the numbers** | Numeric reproduction reproduces a leak. Every price-primary experiment ships a future-destroying control that must collapse the edge; the audit traces verdict-bearing columns' input timestamps. A surviving edge under that control is a leak → REJECT. |
| **Knowledge-base-first** | Read `docs/knowledge-base/` before designing. Never re-run a `pitfalls-ledger.md` dead end; never re-learn a `lessons-and-amendments.md` mechanism. |
| **Integrity gates hard, value reads informative** | Only integrity checks block (**future-destroy** leak survival, holdout, causality/provenance, estimand reconciliation, zero-cost compliance). Quality/materiality/significance reads are evidence for the operator — no auto-verdicts, no threshold stacks, no auto-RETIRE, no power floors, no MDE. |
| **Validity attests; value reports (INFR-016/INFR-022)** | The value chain has **two disjoint layers**. (a) **VALIDITY attestations** — holdout fence, causal ≤t-1, estimand reconciliation, non-STUB fence, no-local-accounting, zero-cost compliance, **future-destroy** leak survival (integrity bite = pre-declared `INTEGRITY_Z × bootstrap_SE` of the same estimator — never an MDE) — stay HARD; a failure means *emission invalid → fix the data*, never *no edge*. (b) **VALUE reads** — sample-size layer, cadence, search score, fold stability, stage-2 bounds (ALL subsets + per-cell), **within-sample attribution** collapse, sign battery, PSR — are **report layers** (`observed/ideal/interpretation` per candidate, nothing machine-dropped); the operator authorises progression. Interpretation bands (STRONG/SUPPORTED/SUGGESTIVE/WASH and similar) are **operator-only tags, never machine-assigned, never gates** (N11). No cost floors, no leg-power MDE, no cost/funding sensitivity, no spread-scale routing, no net deployability reads on the live path — the retired cost stack is `evaluation_cost_legacy` (ARCHIVED). `docs/references/xena-lane.md`. |
| **PSR pairing (INFR-022 directive 4)** | Probabilistic Sharpe Ratio (Bailey & López de Prado 2012, skew/kurt-adjusted) is reported beside every mean per-trade/leg bps read, on the SAME trade series and population: columns `psr` + `psr_n` beside the mean column. Empirical moments only (no normality); `n < 2` or non-finite moments → `psr = NaN` with `psr_n` stated, row still reported (N3). PSR is evidence, never a gate. Default `SR* = 0` (design may override). |
| **Estimand before hypothesis** | No verdict, control read, or TEST read on an emission without a passing `xen.estimand_validation` gate. Controls that validate a hypothesis on an unvalidated estimand certify artifacts (critical-017). |
| **Experiment ≠ family** | Experiments produce evidence and experiment-level verdicts. Family open/retire/promote decisions happen only at checkpoint retrospectives, operator-signed. Checkpoints group multiple experiments. |
| **Protocols, not directives** | Every lesson is codified as a checkable protocol, script, or structural separation — directives ("interrogate raw data") recur; protocols do not. |
| **Operator-facing chat is plain** | Every question, status, summary, or gate prompt to the human is concise and de-jargonified (see § Operator-facing communication). Technical artifacts stay precise; operator messages translate. |

### XENA Lane — the DEFAULT route (binding, INFR-006, 2026-07-10)

**Incoming ideas route to XENA by default** (operator decision Q3): candidates run once in
**Nautilus**, selected at portfolio level by `xen.xena.*`. **Frozen registry VOID on new
stack** (INFR-010 R4) — fresh CAL cycle required before any crypto universe. EXP/SPDR
operator-invoked only. Fills contract from Nautilus emissions (`positions_ledger` +
`bar_marks` via shim; `SlPrice` field on legs). Full spec: `docs/references/xena-lane.md` v2.

### Chapter 06 standing route (live)

Standing enforcement: `docs/references/chapter-06-governance.md` +
`docs/experiments-docs/INDEX.md`. Programme frame: INFR-022 (§ Zero-cost model, Neutrality,
Powering strip above). Chapter-05 governance/preflight packs were removed from live
`docs/references/`; historical material is under `archive/chapter-05-voldir-capture-geometry/`
only.
### Every Experiment Is Price-Primary (binding, INFR-001)

- All strategy logic runs in **NautilusTrader** (`BacktestNode`), emitting
  `data/nautilus_runs/<run_id>/` under the catalog fence + `fence_attestation.json`.
  No vectorised Python backtest of a price strategy. Analysis is `data-analyst` only.
- **VAL carve-out** — re-analysis of already-emitted, still-valid data enters at the estimand
  gate → `data-analyst` directly (no design/QA/execute stages). If the prior emission is
  invalidated by an identified defect, a rerun through the full pipeline is required first.
- **Estimand gate** — no analysis, verdict, control read, or counted TEST read on any emission
  without a passing `results/estimand_validation.json`
  (`python -m xen.estimand_validation ...`, blocking: reconciliation/schema/fence/manifest/
  zero-cost compliance — non-zero commission/fee columns or non-zero `--cost-bps` without an
  `operator_cost_directive.json` fail the gate).
- Accounting primitives live only in `xen.adjudication`; defining them in experiment dirs
  fails `check_no_local_accounting` (L-18 / critical-017).

---

## Checkpoint System & Phase-Based Research

Xen research is organized into **phases**, each with a checkpoint in `docs/experiments-docs/checkpoints/`.

### Phase Lifecycle

1. **Design Phase**: Create `design.md` before any experiments begin
   - Define phase objectives and research questions
   - List planned experiments with rationale
   - Specify methodology and success criteria
   - Reference previous phase's `retrospective.md` if applicable

2. **Execution Phase**: Run experiments according to `design.md`
   - Each experiment follows the lean pipeline (4 artifacts, inline governance, autonomous execution)
   - Update `python/experiments/INDEX.md` as experiments complete
   - Update the relevant `docs/experiments-docs/families/<family>/INDEX.md` with the detailed experiment card; update `docs/experiments-docs/INDEX.md` (master) live status only

3. **Retrospective Phase**: Create `retrospective.md` after phase completes
   - Summarize outcomes vs. objectives
   - Document lessons learned
   - Propose next phase's research direction
   - Update the master index live status and the relevant family detail index with key findings

### Checkpoint Naming Convention

```
docs/experiments-docs/checkpoints/YYYY-MM-DD-###-descriptive-name/
```

- Date: When the phase design was finalized
- Number: Sequential phase number (001, 002, etc.)
- Name: Brief descriptive slug

---

## Available Instruments (Bybit USDT perp universe)

**Primary universe (chapter 04):** 910 USDT linear perpetuals from INFR-011 census
(listed + delisted). Default liquid anchors: BTCUSDT, ETHUSDT, SOLUSDT.

| Status | Meaning |
|--------|---------|
| `CENSUS_COMPLETE` | 910 symbols enumerated (A1 done) |
| `INGEST_IN_FLIGHT` | streaming pipeline populating catalog |
| `ADMITTED` | VAL-style admission PASS (A5) — readable for experiments |
| `SPEC_INCOMPLETE` | tick/lot unrecoverable — return-level reads only |

MBP/L2 is unavailable for the active programme. No T2 confirmation branch is permitted.

**Archived FX/indices universe** (chapter 03): see
`archive/chapter-03-xena-mtfctx/docs/references/dataset-reference.md` — holdout
obligations on that data remain binding; not used for new experiments.

---

## Governance Verdicts

All governance reviews produce one of three verdicts:

| Verdict | Meaning | Action |
|---------|---------|--------|
| **APPROVE** | All checks pass. Pipeline advances. | Proceed to next stage. |
| **REVISE** | Issues found. Specific changes required. | Route to failing skill with issues. Allow up to 2 revision cycles. |
| **REJECT** | Fundamental issues. Cannot proceed as-is. | Hard stop. Present rationale. Cannot be overridden. |

### REVISE Routing

When QA issues REVISE, the verdict identifies:
- `FAILING_ARTIFACT`: which file needs fixing (`design.md`, `code/`, `analysis.md`, `report.md`)
- `REQUIRED_SKILL`: which skill should fix it (quant-designer, experiment-developer, data-analyst, experiment-documenter)

---

## Experiment ID Assignment

- Check `python/experiments/INDEX.md` for the latest experiment ID.
- IDs are zero-padded to 3 digits: `EXP-001`, `EXP-002`, etc.
- Once assigned, an ID is **never reused**, even if the experiment is abandoned.
- If no index exists, start with `EXP-001`.
- VAL-series experiments (validation reruns) use `VAL-001`, `VAL-002`, etc. — same structure, different prefix.
- SPDR-series speed-runs (TRAIN-only availability screens) use `SPDR-001`, etc. — lean screen lane (design.md + screen.md + analysis.md, no QA subagent), no cTrader/estimand gate, disposition-only. Spec: `docs/references/spdr-lane.md`.
- **SPDR allocation floor (raised 2026-08-05 on issuing `SPDR-024`): the next SPDR identifier to issue is `SPDR-025`.** Identifiers below that floor are spent — some by experiments that ran, some by registrations that were withdrawn — and **none is reused**, so the index is not a reliable high-water mark on its own. Raise this floor when an ID is issued; never lower it.

---

## Skill Invocation Triggers

Use these trigger phrases to identify which skill to invoke:

| Skill | Trigger Phrases |
|-------|-----------------|
| **research-pipeline** | run experiment, execute pipeline, go end-to-end, start experiment, automate, run the pipeline, full run, continue experiment |
| **quant-designer** | design the experiment, analysis plan, statistical method, methodology, what test, scope this idea |
| **experiment-developer** | implement, write code, build the model, code the strategy, add the conf |
| **qa-compliance** | QA, pre-exec review, fidelity check, compliance review, ready to run? (fresh context only) |
| **data-analyst** | analyse the data, audit, validate, interrogate, verify results, what does the data say |
| **experiment-documenter** | document, write report, summarise, update docs, write up results |

---

## Existing Analysis Modules

Before creating new modules, check these existing reusable functions:

| Module | Path | Purpose |
|--------|------|---------|
| Chart-type generator | `xen.linebreak_generator` | Line Break bar generation |
| Chart-type generator | `xen.renko_generator` | Renko brick generation |
| Chart-type generator | `xen.heiken_ashi_generator` | Heiken Ashi candle generation |
| OHLC resampling | `xen.bar_aggregator` | N-minute clock-aligned OHLC aggregation |
| **Canonical P&L estimands** | `xen.adjudication` | Multi-leg-correct per-bar/per-leg/episode P&L; reconciliation invariant (L-18) — the ONLY permitted accounting path; `check_no_cost_charged` (zero-cost compliance) |
| **Estimand validation gate** | `xen.estimand_validation` | Blocking pre-analysis gate: reconciliation, schema, fence, manifest, zero-cost compliance + physicality report (with `psr_summary`); `check_no_local_accounting` |
| **Signal-quality toolbox** | `xen.evaluation` | Informative-only evidence: block-bootstrap CIs (INFR-004: circular block capped < n → no zero-width CI on sparse strata; 5-seed battery with `ci_low_seed_range`; `block_sensitivity` sweep; `trimmed_mean` robust stat; report "CI excludes zero", not a p-value — L-20), `psr`/`psr_row` (INFR-022 directive 4), zero-cost caveat + `assert_zero_cost`, exposure-honest economics (avg+peak normalizations, B&H exposure-matched), collapse fractions, splits. **No MDE, no UNPOWERED labels, no cost curves** (retired — L-63). Composed per candidate by the Quant Designer — no fixed stack. |
| ~~Frozen referee stack~~ | `xen.referee_*`, `xen.incremental_referee` | **RETIRED FROM SERVICE (INFR-001 WS-7, 2026-07-04)** — byte-frozen for Chapter-01/02 reproducibility only. Never used for new adjudication: its gate conjunctions/readiness floors select fragile gate-threaders (L-17, B-5/B-7). New evaluation = `xen.evaluation` + operator judgment. |
| **Nautilus foundation** | `xen.nautilus.{emission,adjudication_shim,instrument_ids,backtest_util}` | Emission v1, shim → adjudication, InstrumentId convention, BacktestNode helpers |
| Run ingestion (legacy) | `xen.signals.ingestion` | Archived cTrader emissions only |
| ~~Bybit T1 cost + routing~~ | `xen.evaluation_cost_legacy` | **ARCHIVED (INFR-022)** — `bybit_round_trip_cost_bps`, `spread_scale_route`, `t1_round_trip_spread_bps`, `FTMO_COSTS`, `round_trip_cost_bps` and friends moved here with an ARCHIVED banner; not callable from any live research path (only an operator cost directive may re-enable, recorded in the design) |
| **XENA portfolio framework** | `xen.xena.{oracle,ingest,search,certify,final_gate,calibration}` | The DEFAULT adjudication route (INFR-006/INFR-022): shared-capital oracle (gross-only; `charge_costs=True` requires an operator cost directive), blocking candidate gate, LAHC search (zero-cost compliance guard), plateau+fold certification, single **gross** final gate, frozen-registry verification. Spec: `docs/references/xena-lane.md` |
| **XENA report layers (INFR-016/INFR-022)** | `xen.xena.report_layer`, `xen.xena.controls` | Value/quality/significance reads as **report layers** (`observed / ideal / interpretation` per candidate, no `pass` field), not gates: `LayerReport` schema + renderer, `sample_size_layer` (n_legs + per-leg vol + design minimum-n NOTE — replaces `power_layer`; no MDE/powered/UNPOWERED), `psr_layer` (PSR + n beside mean-trade bps), `stage2_bounds_layer` (all subsets), `sign_battery` (≥2000 seeds, effect+p+CI+n — no `at_or_above_p95`, no power labels), `attribution_derangement` (reported collapse fraction — no `hard_fail_leak`), `final_gate.final_report_layer` (gross walk-forward, no `passed`). Value labels (STRONG/SUPPORTED/…) are operator-only tags (N11). |
| *(More to be added as analysis modules are developed)* | `python/src/xen/` | Reusable analysis code |

---

## Complexity Budget Guidelines

| Experiment Type | Stat Tests | Visualisations | Code Modules |
|----------------|-----------|----------------|-------------|
| Descriptive / EDA | 0 | 2-4 | 0-1 |
| Single hypothesis test | 1-2 | 2-3 | 1 |
| Comparative (across data views/instruments) | 2-4 | 3-5 | 1-2 |
| Multi-feature relationship | 2-3 | 3-5 | 1-2 |
| Cross-view alignment | 2-4 | 3-5 | 1-2 |

If an experiment needs more, it should be **split into multiple experiments**.

---

## Code Standards

- **Style**: PEP 8, max 100 char line length, f-strings, import grouping (stdlib -> third-party -> local)
- **Type hints**: Required on all public function parameters and return values
- **Docstrings**: Required with Parameters and Returns sections
- **Separation**: Analysis functions (pure computation) != Plotting functions (figures) != Experiment scripts (orchestration)
- **Data handling**: Polars preferred for performance with Parquet; pandas acceptable for tabular; numpy for numerical
- **NaN handling**: Explicit — never let NaN propagate silently
- **Function size**: Split if exceeding ~30 lines
- **Look-ahead bias**: Never use data from after the event timestamp when analyzing an event
- **Real-price outcome discipline**: Use real time-bar prices for strategy, signal-quality, and return outcomes. If Heiken Ashi or Renko is in scope, never use HA prices or Renko brick prices for strategy P&L. `HAClose` returns are allowed only for explicitly scoped, non-tradable HA distortion diagnostics.
- **Timestamp alignment**: Cross-view comparisons align by timestamp (`CloseTime` or `SourceCloseTime`), never by bar index
- **Organization**: imports -> path setup -> constants -> I/O helpers -> pure computation -> plotting -> orchestration -> `main()`
- **Sectioning**: non-trivial scripts use VAL-001-style separators for constants, dataclasses/types, helpers, pure checks/computation, plotting/output, orchestration, and `main()`
- **Import side effects**: no directory creation, file writes, data loads, or plotting at module import time
- **Logging/output**: concise progress output; helper functions return data instead of printing
- **Progress tracking**: use `tqdm` for long-running outer loops over files, instruments, chart views, parameter grids, validation windows, or simulations
- **Performance**: lazy Polars scans, timestamp sort before first-70-percent slicing, column projection where practical, aggregation before collection where possible, efficient joins/window expressions, and bounded pandas conversions for plots
- **Plot reuse**: do not rerun heavy loads or chart generation solely for plotting when the analysis pass can return bounded plot inputs
- **Safe optimization**: computational optimizations must not change sample membership, temporal ordering, denominators, metric definitions, statistical interpretation, reproducibility, or streaming/causal semantics
- **Vectorization discipline**: replace Python row loops with Polars/NumPy/vectorized logic only when the replacement is causally equivalent; keep genuinely sequential algorithms explicit and bounded
