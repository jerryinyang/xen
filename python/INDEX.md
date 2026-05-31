# Xen: Thesis-Qualification Referee Programme

## Programme Direction

Xen's object of study is the **referee** that qualifies candidate trading theses — the machinery that decides which candidates earn scarce validation resources (held-out data, paper trading, capital) — under an honest accounting of both false-positive and false-negative error. It is no longer a search for a specific market edge.

The programme refreshed in place on 2026-05-30 after three consecutive thesis closures (event-chart, ICT, and higher-timeframe state-descriptor theses; Phases 001–005) — each issued by a gate stack whose own error profile was never measured, so its "reject" verdicts could not distinguish *"no edge"* from *"an edge below the stack's unmeasured detection floor."* That ambiguity is the object Xen now studies.

**Current phase:** 006 — Thesis-Qualification Referee Calibration
**Phase design:** `docs/experiments-docs/checkpoints/2026-05-31-006-thesis-qualification-referee-calibration/design.md`
**Reference-stack spec (predeclared):** `docs/experiments-docs/checkpoints/2026-05-31-006-thesis-qualification-referee-calibration/reference-stack-spec.md`

**Founding thesis (H1):** a qualification system's operating characteristics — false-positive rate, a power *surface*, per-leg pass rates — can be measured with enough fidelity that "reject" carries trustworthy meaning. **H0:** they cannot — power is too sensitive to the synthetic effect-generator (the calibrator-needs-calibrating problem).

**Founding experiment:** a two-part calibration of the **existing Xen gate stack as the baseline referee** — the §5.6 closure stack transcribed and frozen from `python/experiments/EXP-036`. Realised as **EXP-037** (Part A null calibration → FPR + per-leg leak/over-reject, *trustworthy*) and **EXP-038** (Part B power bracketing → power surface + synthetic-family sensitivity = the H0/H1 verdict, *fragile*).

## Founding documents

- `docs/planning/thesis-qualification-system-problem-statement.md` — the seed (problem, desiderata, failure modes).
- `docs/planning/charter.md` — founding design (object of study, founding thesis, 13 binding constraints, 4 honesty clauses).
- `docs/planning/state-and-open-decisions.md` — reconciled state and resolved decisions D0–D7.

## Architecture

- **Data collection:** cAlgo robot collects completed 1-minute time bars.
- **Chart-type generation (retained, agnostic infrastructure):** Python generators produce Line Break, Renko, Heiken Ashi on demand; `bar_aggregator.py` resamples OHLC; `time_alignment.py` normalizes timestamps. Future theses ride on chart types (primarily traditional time bars); the referee does not put this infrastructure on trial.
- **Analysis modules (`python/src/`):** the existing analysis stack — `signal_quality.py` (gate inference primitives: `bootstrap_diff_ci`, `bootstrap_rate_ci`, `compare_signal_sets`, `coverage_adjusted_outcomes`), `timeframe_replication.py`, `market_bias.py`, `ict_timebar.py` — retained as the baseline referee under test and its support.
- **Experiments:** `python/experiments/`. The prior tree (EXP-001…036) is retained as the source of record for the baseline referee; closed theses stay closed (charter C1).
- **Architecture reference:** `docs/references/architecture.md`
- **Dataset reference:** `docs/references/dataset-reference.md`

## Key Constraints

- The referee is specified in two layers; **only the evidentiary layer is calibrated** — admissibility preconditions are held fixed (charter constraint 9).
- Null vs power calibration are never merged; every error rate is tagged with its species and, for power, its synthetic-family conditioning.
- No scalar MDE — sensitivity is reported as a conditioned power *surface*.
- Do not loosen any current gate before calibration (constraint 13); successor-stack design is deferred until the calibration ruling.
- Economic materiality is reported per predeclared proxy-cost regime (the data lacks spread/slippage).
- All strategy returns evaluated on time-matched real prices (synthetic-price discipline).
- No look-ahead bias in any generation or analysis; non-parametric methods by default.
- Final 30% global holdout never used.
