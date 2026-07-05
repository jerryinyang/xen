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
| Strategy-run emissions (cTrader) | `data/strategy_runs/<EXP-ID>/` |
| cTrader-CLI harness | `tools/ctrader-cli/` (`run-experiment.sh`, `experiments/<ID>.conf`, `README.md`) |
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
├── code/              # developer: C# model refs + conf notes (NO Python analysis code)
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

### Checkpoint Structure (Phase-Based Documentation)

```
docs/experiments-docs/checkpoints/<phase-timestamp>-<phase-name>/
├── design.md                   # Phase objectives, plans, methodology
└── retrospective.md            # Phase outcomes, lessons learned
```

The `design.md` of the latest checkpoint serves as the guide for the current phase's experimentation pipeline execution.

---

## Data Architecture

Xen uses a **1-minute time-bar base data** architecture. The cAlgo robot collects and stores completed 1-minute bars only. Experiments may add deterministic derived views, such as chart-type transformations or time-bar-native feature tables, only when the approved scope requires them.

### Base Data (cAlgo Output)

Each robot session produces one base Parquet file per symbol/session:

| Dataset | Path Pattern | Description |
|---------|-------------|------------|
| 1-minute time bars | `data/timebars/timebars_<symbol>_<timestamp>_<timestamp>.parquet` | Completed OHLC time bars from cTrader/cAlgo |

### Derived Data (Python On-Demand)

Derived data is generated from 1-minute time bars. It is not stored persistently by default. Frequently reused canonical variants may be persisted under `data/<derived_view>/` only when the generator or feature version and parameters are recorded and the variant can be invalidated if logic changes.

| Generator | Module | Parameters |
|-----------|--------|------------|
| Line Break | `python/src/xen/linebreak_generator.py` | `level` (default: 3) |
| Renko | `python/src/xen/renko_generator.py` | `atr_period` (default: 14); generated from 1-minute source bars |
| Heiken Ashi | `python/src/xen/heiken_ashi_generator.py` | None |

Chart-type generators are optional derived views. Each chart-type generator produces DataFrames with a `SourceCloseTime` column (or equivalent) linking chart-type events to real-time coordinates for return evaluation.

### Time Bar Schema (8 columns)

| Column | Type | Description |
|--------|------|-------------|
| `Symbol` | string | cTrader symbol |
| `OpenTime` | datetime | Bar open timestamp |
| `CloseTime` | datetime | Bar close timestamp |
| `Open` | double | Bar open price |
| `High` | double | Bar high price |
| `Low` | double | Bar low price |
| `Close` | double | Bar close price |
| `TickVolume` | int64 | Broker-reported tick volume, if available |

### Chart-Type Schemas

See `docs/references/dataset-reference.md` for full schemas. Key columns:

- **Line Break:** `Open, High, Low, Close, Direction, Level, SourceCount, SourceCloseTime`
- **Renko:** `Open, High, Low, Close, Direction, BrickSize, ATRPeriod, SourceCount, SourceCloseTime`
- **Heiken Ashi:** `HAOpen, HAHigh, HALow, HAClose, RealOpen, RealHigh, RealLow, RealClose, Direction, SourceCount`

### Enum Encoding

| Enum | Values |
|------|--------|
| `Direction` (all chart types) | `Up=1`, `Down=-1` |

---

## OOS Holdout Rules

**These rules are non-negotiable and enforced by governance at every stage.**

Xen data is temporally ordered. The holdout split must respect chronological ordering.

### Nested Chronological Split

```
Full Dataset (ordered by CloseTime or SourceCloseTime)
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
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob("timebars/timebars_*.parquet"))[-1]

# Load and sort chronologically
df = pl.scan_parquet(path).sort("CloseTime").collect().to_pandas()

# Chronological split
analysis_cutoff = int(len(df) * 0.7)
analysis_set = df.iloc[:analysis_cutoff]
# holdout = df.iloc[analysis_cutoff:]  # DO NOT UNCOMMENT OR USE

# Within analysis set: train/test split
train_cutoff = int(len(analysis_set) * 0.7)
train_set = analysis_set.iloc[:train_cutoff]
test_set = analysis_set.iloc[train_cutoff:]
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
| **Single hypothesis per experiment** | Each experiment answers exactly one question. Scope creep is a governance violation. |
| **Complexity budget enforced** | Every experiment has defined limits on statistical tests, visualisations, and new code modules. |
| **No premature optimisation** | Characterisation phases must not tune strategy parameters, windows, filters, stops, or targets against analysis-set performance. Optimisation requires an explicit phase and scope. |
| **Causal-by-construction execution** | Price-primary (edge-generating) experiments run in the cTrader engine where look-ahead is impossible; Python is analysis-only on emitted runs. A vectorized Python backtest of a price strategy is rejected. (Structural fix for the L-01 look-ahead leak.) |
| **Evaluate-on-bar-open + lagged reference only** | Every decision is evaluated at a bar's **open**, conditioned only on **previous, confirmed (closed) bars** (data through bar `t-1`); the forming bar's own OHLC is unknown at decision time. No signal, filter, regime label, indicator, or exit may read the bar it acts in. The C# `OnBar` model enforces this by construction; analysis code must use the `[t-1]` lag. (Generalizes the L-01 `rct[di]→[di-1]` fix into a standing rule.) |
| **Open-to-open returns only** | Strategy / signal / P&L returns are measured **open-to-open**, never open-to-close — an `OnClose` execution is impossible in real time (the close is unknown until the bar completes). Close-referenced returns are a non-tradable diagnostic and must be labelled as such. |
| **Leak resistance is audited independently of the numbers** | Numeric reproduction reproduces a leak. Every price-primary experiment ships a future-destroying control that must collapse the edge; the audit traces verdict-bearing columns' input timestamps. A surviving edge under that control is a leak → REJECT. |
| **Knowledge-base-first** | Read `docs/knowledge-base/` before designing. Never re-run a `pitfalls-ledger.md` dead end; never re-learn a `lessons-and-amendments.md` mechanism. |
| **Integrity gates hard, value reads informative** | Only integrity checks block (leak tripwire, holdout, causality/provenance, estimand reconciliation). Quality/materiality/significance reads are evidence for the operator — no auto-verdicts, no threshold stacks, no auto-RETIRE. |
| **Estimand before hypothesis** | No verdict, control read, or TEST read on an emission without a passing `xen.estimand_validation` gate. Controls that validate a hypothesis on an unvalidated estimand certify artifacts (critical-017). |
| **Experiment ≠ family** | Experiments produce evidence and experiment-level verdicts. Family open/retire/promote decisions happen only at checkpoint retrospectives, operator-signed. Checkpoints group multiple experiments. |
| **Protocols, not directives** | Every lesson is codified as a checkable protocol, script, or structural separation — directives ("interrogate raw data") recur; protocols do not. |

### Every Experiment Is Price-Primary (binding, INFR-001)

- All strategy logic runs in cTrader (StrategyHost) via `tools/ctrader-cli/run-experiment.sh`,
  emitting `data/strategy_runs/<ID>/` under the `AnalysisEndUtc` fence. No Python backtest of
  a price strategy, ever. No developer-side Python analysis replication — analysis of emitted
  data is the `data-analyst`'s job, with its own code on canonical `xen` estimands.
- **VAL carve-out** — re-analysis of already-emitted, still-valid data enters at the estimand
  gate → `data-analyst` directly (no design/QA/execute stages). If the prior emission is
  invalidated by an identified defect, a rerun through the full pipeline is required first.
- **Estimand gate** — no analysis, verdict, control read, or counted TEST read on any emission
  without a passing `results/estimand_validation.json`
  (`python -m xen.estimand_validation ...`, blocking: reconciliation/schema/fence/manifest).
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

## Available Instruments

The full universe (17 instruments) was admitted by VAL-003.

| Symbol | Name | Type | Notes |
|--------|------|------|-------|
| EURUSD | Euro/US Dollar | Forex | Major pair, high liquidity |
| GBPUSD | British Pound/US Dollar | Forex | Major pair |
| USDJPY | US Dollar/Japanese Yen | Forex | Major pair |
| USDCHF | US Dollar/Swiss Franc | Forex | Major pair |
| USDCAD | US Dollar/Canadian Dollar | Forex | Major pair |
| AUDUSD | Australian Dollar/US Dollar | Forex | Major pair |
| NZDUSD | New Zealand Dollar/US Dollar | Forex | Major pair |
| EURJPY | Euro/Japanese Yen | Forex | Cross pair |
| GBPJPY | British Pound/Japanese Yen | Forex | Cross pair |
| AUDJPY | Australian Dollar/Japanese Yen | Forex | Cross pair |
| XAUUSD | Gold/US Dollar | Commodity | Volatile, useful for trend analysis |
| BTCUSD | Bitcoin/US Dollar | Crypto | 24/7, high volatility |
| USTEC | NASDAQ-100 | Index | Tech-heavy, liquid |
| US500 | S&P 500 | Index | Broad US equities |
| US2000 | Russell 2000 | Index | Small-cap US equities |
| DE30 | DAX 40 | Index | German equities; broker history truncated to 2026-01-16 |
| JP225 | Nikkei 225 | Index | Japanese equities |

The original 4-instrument core (EURUSD, XAUUSD, BTCUSD, USTEC) is the default subset. Experiments using the expanded universe must justify the inclusion of new instruments in scope.

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
| **Canonical P&L estimands** | `xen.adjudication` | Multi-leg-correct per-bar/per-leg/episode P&L; reconciliation invariant (L-18) — the ONLY permitted accounting path |
| **Estimand validation gate** | `xen.estimand_validation` | Blocking pre-analysis gate: reconciliation, schema, fence, manifest + physicality report; `check_no_local_accounting` |
| **Signal-quality toolbox** | `xen.evaluation` | Informative-only evidence: block-bootstrap CIs (INFR-004: circular block capped < n → no zero-width CI on sparse strata; 5-seed battery with `ci_low_seed_range`; `block_sensitivity` sweep; `trimmed_mean` robust stat; report "CI excludes zero", not a p-value — L-20), MDE/UNPOWERED labels, exposure-honest economics (avg+peak normalizations, B&H exposure-matched), cost curves, collapse fractions, splits. Composed per candidate by the Quant Designer — no fixed stack. |
| ~~Frozen referee stack~~ | `xen.referee_*`, `xen.incremental_referee` | **RETIRED FROM SERVICE (INFR-001 WS-7, 2026-07-04)** — byte-frozen for Chapter-01/02 reproducibility only. Never used for new adjudication: its gate conjunctions/readiness floors select fragile gate-threaders (L-17, B-5/B-7). New evaluation = `xen.evaluation` + operator judgment. |
| Run ingestion | `xen.signals.ingestion` | Emitted-run loading + holdout fence assertion |
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
