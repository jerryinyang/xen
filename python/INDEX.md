# Xen — Intraday-Trading Research Base

A neutral base environment for testing trading theses and running research on
intraday market data. **No specific thesis is currently loaded** — the prior
research programmes that used this directory are closed, and only their
thesis-agnostic infrastructure has been retained.

## What this provides

- **Data layer (`python/src/xen/`)** — thesis-agnostic core infrastructure:
  deterministic, streaming-compatible chart-type generators (Line Break, Renko,
  Heiken Ashi) and OHLC resampling on a 1-minute time-bar base. Installed as the
  editable `xen` package.
- **Research pipeline (skills)** — a gated experiment lifecycle (scope → analysis
  plan → implementation → governance → manual execution → audit → interpretation
  → documentation) enforced by the `research-pipeline` and `experiment-*` skills.
- **Experiments (`python/experiments/`)** — one directory per experiment; running
  index in `python/experiments/INDEX.md`, comprehensive index in
  `docs/experiments-docs/INDEX.md`.

## Architecture & data

- Architecture: `docs/references/architecture.md`
- Dataset reference: `docs/references/dataset-reference.md`
- Base data: 1-minute time bars under `data/timebars/` (EURUSD, XAUUSD, BTCUSD, USTEC).

## Package

```bash
cd python
uv pip install -e .      # installs the editable `xen` data-layer package
uv run pytest            # run the test suite
```

`python/src/xen/` modules: `linebreak_generator`, `renko_generator`,
`heiken_ashi_generator`, `bar_aggregator`, plus the optional `indicators/`
subpackage. The generator functions are re-exported from the package root, e.g.
`from xen import generate_renko`.

## Invariants carried over as infrastructure

- **Holdout discipline:** the final 30% global holdout is never inspected;
  analysis uses the first 70%, with a nested 70/30 chronological train/test split
  inside it.
- **Synthetic-price discipline:** returns are evaluated on real time-bar prices,
  never on Heiken Ashi or Renko construction prices.
- **Deterministic, streaming-compatible generation; no look-ahead.**
- **One falsifiable question per experiment; non-parametric methods by default.**
