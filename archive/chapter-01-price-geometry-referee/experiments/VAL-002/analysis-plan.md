# VAL-002 Analysis Plan (design.md v2)

## Method

### A. Transcription + holdout (developer smoke, `run_experiment.py`)

1. Enumerate base files with `xen.referee_calibration.list_timebar_files`.
2. Load the first 70% chronological slice with `load_analysis_data`.
3. Derive `AnalysisEndUtc = max(CloseTime in analysis slice) + 1 microsecond`.
4. Produce the C# generator/indicator CSV family via `Mode=StrategyHostParity`
   (cTrader) or the `tools/StrategyHostParity` console exporter (same shared C# code).
5. **Transcription:** compare each C# generator/indicator output to its existing
   Python reference (`generate_linebreak`, `generate_renko`, `generate_heiken_ashi`,
   `aggregate_ohlc`, `compute_market_bias`) — exact for timestamps/categoricals/
   ints/bools, tight float tolerance. (No Python MA *generation* engine is used; MA
   correctness is behavioral, step B.)
6. **Holdout:** verify every C# output timestamp is strictly before `AnalysisEndUtc`.

### B. Behavioral closure (binding, operator step)

7. Run `Mode=StrategyHost` in cTrader's engine over the analysis window to emit a
   `data/strategy_runs/.../positions.parquet` carrying the real OHLC executed on.
8. Route it through the frozen suite with the ingestion harness:
   `xen.signals.screen_emitted_run(load_emitted_run(run_dir), train_end_utc=...)`,
   which builds next-step returns from the **emitted** `RealClose` and calls
   `evaluate_referees` unchanged.
9. Confirm the EXP-004 `matched_reject` and EXP-009 gate-stack `below_MDE`
   classification reproduce (behavioral, not byte-exact).

## Acceptance

- Transcription: every generator/indicator check `PASS`.
- Holdout: every emitted timestamp before `AnalysisEndUtc`.
- Behavioral: cTrader-emitted MA positions reproduce the EXP-004/009 classification.

## Manual Commands

Transcription smoke (console exporter):

```bash
cd python
uv run python experiments/VAL-002/code/run_experiment.py --skip-suite
```

Behavioral closure (after a cTrader `Mode=StrategyHost` run):

```python
from xen.signals import load_emitted_run, screen_emitted_run
verdicts = screen_emitted_run(load_emitted_run("data/strategy_runs/<run_dir>"))
```

cTrader determinism is checked by running `Mode=StrategyHost` twice over the same
fixed data/config and confirming the suite verdict reproduces (behavioral), not by
byte-identical output.
