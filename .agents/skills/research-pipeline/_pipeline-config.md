# Xen Research Pipeline - Shared Configuration

This file is the single source of truth for constants, conventions, and shared knowledge used by all skills in the Xen research pipeline. **Do not duplicate this content in individual skills — reference this file instead.**

---

## Project Paths

All paths are relative to the project root (`{project-root}`).

| Resource | Path |
|----------|------|
| Experiment Directory | `python/experiments/<EXP-ID>/` |
| Analysis Modules | `python/src/` |
| Data Files | `data/` |
| Experiment Index (brief) | `python/experiments/INDEX.md` |
| Comprehensive Index | `docs/experiments-docs/INDEX.md` |
| Checkpoint Directory | `docs/experiments-docs/checkpoints/` |
| Reference Documents | `docs/references/` |
| Code Reviews | `docs/code-reviews/` |
| Architecture Doc | `docs/references/architecture.md` |
| Dataset Reference | `docs/references/dataset-reference.md` |

### Per-Experiment Structure

```
python/experiments/<EXP-ID>/
├── scope.md                    # Experiment scope (Stage 1)
├── analysis-plan.md            # Analysis methodology (Stage 2)
├── code/
│   └── run_experiment.py       # Implementation (Stage 3)
├── plots/                      # Generated visualisations
├── results/                    # Raw output data
├── governance/
│   ├── pre-execution-review.md # Pre-exec governance verdict
│   └── post-experiment-review.md # Post-exec governance verdict
├── audit.md                    # Code/results audit (Stage 5)
├── results.md                  # Results interpretation (Stage 6)
└── report.md                   # Final experiment report (Stage 7)
```

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
| Line Break | `python/src/linebreak_generator.py` | `level` (default: 3) |
| Renko | `python/src/renko_generator.py` | `atr_period` (default: 14); generated from 1-minute source bars |
| Heiken Ashi | `python/src/heiken_ashi_generator.py` | None |

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
   - Each experiment follows the 8-stage pipeline
   - Update `python/experiments/INDEX.md` as experiments complete
   - Update `docs/experiments-docs/INDEX.md` with comprehensive findings

3. **Retrospective Phase**: Create `retrospective.md` after phase completes
   - Summarize outcomes vs. objectives
   - Document lessons learned
   - Propose next phase's research direction
   - Update comprehensive index with key findings

### Checkpoint Naming Convention

```
docs/experiments-docs/checkpoints/YYYY-MM-DD-###-descriptive-name/
```

- Date: When the phase design was finalized
- Number: Sequential phase number (001, 002, etc.)
- Name: Brief descriptive slug

---

## Available Instruments

| Symbol | Name | Type | Notes |
|--------|------|------|-------|
| EURUSD | Euro/US Dollar | Forex | Major pair, high liquidity |
| XAUUSD | Gold/US Dollar | Commodity | Volatile, good for trend analysis |
| BTCUSD | Bitcoin/US Dollar | Crypto | 24/7, high volatility |
| USTEC | NASDAQ-100 | Index | Tech-heavy, liquid |

Other cTrader symbols may be added as the research progresses. Observations may lead to focusing on subsets.

---

## Governance Verdicts

All governance reviews produce one of three verdicts:

| Verdict | Meaning | Action |
|---------|---------|--------|
| **APPROVE** | All checks pass. Pipeline advances. | Proceed to next stage. |
| **REVISE** | Issues found. Specific changes required. | Route to failing skill with issues. Allow up to 2 revision cycles. |
| **REJECT** | Fundamental issues. Cannot proceed as-is. | Hard stop. Present rationale. Cannot be overridden. |

### REVISE Routing

When governance issues REVISE, the verdict identifies:
- `FAILING_ARTIFACT`: which file needs fixing (scope.md, analysis-plan.md, code, audit.md, results.md, report.md)
- `REQUIRED_SKILL`: which skill should fix it (experiment-quant-analyst, experiment-developer, experiment-auditor, experiment-documenter)

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
| **research-pipeline** | run experiment, execute pipeline, go end-to-end, start experiment, automate, run the pipeline, no interruptions, full run, run from scope, continue experiment |
| **experiment-quant-analyst** | analysis plan, statistical method, methodology, interpret results, what test, how to analyse, what do these results mean |
| **experiment-developer** | implement, write code, create script, code the analysis, build module |
| **experiment-auditor** | audit, validate, check code, verify results, test correctness, numerical check |
| **experiment-documenter** | document, write report, summarise, update docs, experiment report, findings, write up results |

---

## Existing Analysis Modules

Before creating new modules, check these existing reusable functions:

| Module | Path | Purpose |
|--------|------|---------|
| Optional chart-type generators | `python/src/linebreak_generator.py` | Line Break bar generation |
| Optional chart-type generators | `python/src/renko_generator.py` | Renko brick generation |
| Optional chart-type generators | `python/src/heiken_ashi_generator.py` | Heiken Ashi candle generation |
| *(More to be added as analysis modules are developed)* | `python/src/` | Reusable analysis code |

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
- **Import side effects**: no directory creation, file writes, data loads, or plotting at module import time
- **Logging/output**: concise progress output; helper functions return data instead of printing
- **Performance**: lazy Polars scans, timestamp sort before first-70-percent slicing, column projection where practical, and bounded pandas conversions for plots
- **Plot reuse**: do not rerun heavy loads or chart generation solely for plotting when the analysis pass can return bounded plot inputs
