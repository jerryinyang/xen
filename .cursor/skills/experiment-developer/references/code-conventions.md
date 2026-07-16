# Code Conventions

Project-specific code conventions for the Xen research pipeline.

---

## Standard Data Loading Pattern

All experiment scripts should use this lazy loading pattern. It is the default
unless an approved analysis plan documents why a smaller explicit file read is
safe.

```python
"""
Experiment EXP-XXX: <Title>
Implements the analysis plan from design.md.
"""
from pathlib import Path

import numpy as np
import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns

DATA_DIR = Path("data")

# Chapter 04: ALL catalog bar reads go through the A6 fence wrapper — never raw catalog.bars().
# Legacy chapter-03 VAL carve-out only — time bars under archive:
# timebars_path = sorted(DATA_DIR.glob("timebars/timebars_*.parquet"))[-1]
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from xen.nautilus.catalog_fence import fenced_bar_query, load_fence_manifest

catalog = ParquetDataCatalog(DATA_DIR / "catalog")
fence = load_fence_manifest()  # hash-pinned absolute dates (INFR-011 A6 fence-manifest.json)
train_bars = fenced_bar_query(
    catalog,
    ["BTCUSDT-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL"],
    start=fence.analysis_start_utc,
    end=fence.train_end_utc,
    band="TRAIN",
)
# TEST band: band="TEST" with start/end inside [train_end_utc, holdout_start_utc] —
# counted governance events, operator approval required before any TEST read.
# HOLDOUT (fence.holdout_start_utc onward): never queryable — wrapper raises FenceViolation.
# Emission attestation: xen.nautilus.catalog_fence.fence_attestation_payload(fence).

# Generate chart types on-demand from the scoped source data.
# `xen` is installed editable (`uv pip install -e .` in python/), so no sys.path hack.
from xen.linebreak_generator import generate_linebreak
lb_bars = generate_linebreak(analysis_set, level=3)

# Apply experiment-specific filtering from scope document
# e.g., eurusd_data = analysis_set.filter(pl.col("Symbol") == "EURUSD")
```

**Important**:
- `Direction` is an **int32 column** (`+1` for Up, `-1` for Down). Handle accordingly.
- Use `CloseTime` for temporal ordering of time bars, event timestamps for
  time-bar-native events, and `SourceCloseTime` for chart-type bars.
- Apply the global holdout split in the lazy plan before collecting analysis rows. Do not `read_parquet()` the full dataset for experiments unless the approved plan explicitly permits it.
- Do not call `.unique()` in loaders unless the scope requires deduplication and the code reports pre/post row counts. Silent dedupe changes the 70% analysis boundary.
- For cross-view comparisons, align by timestamp — never by bar index.
- Strategy P&L and signal outcomes must use real prices. Heiken Ashi returns use `RealClose` (never `HAClose`); Renko and Line Break signals use `SourceCloseTime` to align to real time-bar prices.
- Derived-view generators and feature builders are deterministic: same input + same parameters = same output, unless the approved scope explicitly requires seeded randomness.
- Use `tqdm.auto.tqdm` for long-running outer loops over files,
  instruments, parameter grids, validation windows, chart views, or repeated
  simulations. Keep progress descriptions stable and use `tqdm.write()` or the
  logger for occasional status lines.
- Computational optimization is required for large project datasets, but it
  must not change sample membership, temporal ordering, denominators, metric
  definitions, statistical interpretation, or reproducibility.
- Prefer Polars lazy expressions, joins, group/window operations, and NumPy
  vectorization over Python row loops only when the vectorized version preserves
  causal and streaming semantics. Keep explicit loops for genuinely sequential
  algorithms, stateful chart generation, or bounded validation probes.

---

## Causal Provenance & Leak Resistance (mandatory)

The Chapter-01 false positive (L-01) was a one-bar look-ahead in a shared outcome module
(`rct_target[di]` used as the intrabar limit *during* bar `di`; live-actable is `[di-1]`),
invisible because the audit re-derived from the same module. Code rules:

- **Price-primary signal logic is Nautilus, not analysis Python.** Edge generation runs in
  `BacktestNode`. Python ingests `data/nautilus_runs/<run_id>/` via
  `xen.nautilus.adjudication_shim` and never re-generates a signal. No vectorised
  price-strategy backtest.
- **Provenance contract on outcome modules.** Any `xen` function emitting an outcome / target /
  excursion / fill column documents, in its docstring, which timestamps each output reads. Never
  use a bar's own close as that bar's intrabar limit. The next-bar-action convention is `[di-1]`.
- **Evaluate-on-bar-open, lagged reference only.** Every decision (signal, filter, regime label,
  indicator read, exit arm) is taken at a bar's **open** and may read only **previous confirmed
  (closed) bars** — data through `t-1`. The forming bar's own OHLC is unknown at decision time;
  reading it is look-ahead. The C# `OnBar` model gives this by construction (it never sees a future
  bar); Python analysis must apply the `[t-1]` lag explicitly and align on the **open** of the
  action bar.
- **Open-to-open returns only.** Measure strategy / signal / P&L returns **open-to-open**. An
  `OnClose` fill cannot happen live (the close is unknown until the bar completes), so an
  open-to-close return is non-tradable — allowed only as an explicitly labelled diagnostic, never
  for an edge / P&L / deployability claim.
- **Ship the leak tripwire.** Implement the design's future-destroying control (future-shuffle /
  time-reversal / outcome-label permutation) so the audit can confirm the edge collapses. Make it
  a runnable mode/flag of `run_experiment.py`, not a manual afterthought.
- **Booked-vs-real (ports).** Charge binding-leg slippage/cost; keep any look-ahead favourable
  view explicitly labelled non-tradable (L-02).

## Existing Analysis Modules

Check these modules before creating new reusable functions:

| Module | Import | Key Functions |
|--------|--------|--------------|
| Line Break Generator | `xen.linebreak_generator` | `generate_linebreak()`, `LineBreakGenerator` |
| Renko Generator | `xen.renko_generator` | `generate_renko()`, `RenkoGenerator` |
| Heiken Ashi Generator | `xen.heiken_ashi_generator` | `generate_heiken_ashi()`, `HeikenAshiGenerator` |
| OHLC Resampling | `xen.bar_aggregator` | `aggregate_ohlc()`, `coverage_summary()` |

The data-layer generators above (also re-exported from the `xen` package root,
e.g. `from xen import generate_renko`) are the only reusable modules guaranteed
to exist on a fresh base. Optional indicator ports live under `xen.indicators`.
Reusable analysis helpers introduced by experiments belong in `python/src/xen/`.
If a function you need already exists, import and use it. Do not re-implement.

**Xen Data Access Pattern**:
```python
from pathlib import Path

import polars as pl

from xen.linebreak_generator import generate_linebreak
from xen.renko_generator import generate_renko
from xen.heiken_ashi_generator import generate_heiken_ashi

DATA_DIR = Path("data")

def load_time_bars(
    instrument: str | None = None,
) -> pl.DataFrame:
    """Load time bars with optional instrument filtering."""
    path = sorted(DATA_DIR.glob("timebars/timebars_*.parquet"))[-1]
    scan = pl.scan_parquet(path).sort("CloseTime")
    
    if instrument:
        # Filter by symbol in filename or column if available
        pass
    
    total_rows = int(scan.select(pl.len()).collect().item())
    return scan.slice(0, int(total_rows * 0.7)).collect()


def generate_chart_type(
    chart_type: str,
    time_bars: pl.DataFrame,
    **params,
) -> pl.DataFrame:
    """Generate chart-type data on-demand from time bars."""
    if chart_type == "linebreak":
        return generate_linebreak(time_bars, level=params.get("level", 3))
    elif chart_type == "renko":
        return generate_renko(time_bars, atr_period=params.get("atr_period", 14))
    elif chart_type == "heiken_ashi":
        return generate_heiken_ashi(time_bars)
    else:
        raise ValueError(f"Unknown chart type: {chart_type}")
```

---

## Function Template

```python
def function_name(
    param1: type,
    param2: type = default,
) -> return_type:
    """One-line summary.

    Longer description if needed.

    Parameters
    ----------
    param1 : type
        Description.
    param2 : type
        Description.

    Returns
    -------
    return_type
        Description of return value.
    """
    # Validate inputs
    # ...

    # Core computation
    # ...

    # Return result
    return result
```

---

## Plot Template

```python
def plot_<name>(
    data: pd.DataFrame | np.ndarray,
    save_path: str | None = None,
    **kwargs,
) -> plt.Figure:
    """One-line description of what the plot shows.

    Parameters
    ----------
    data : ...
        Description.
    save_path : str, optional
        Path to save the figure. If None, display only.

    Returns
    -------
    plt.Figure
        The figure object.
    """
    sns.set_theme(style='whitegrid')
    fig, ax = plt.subplots(figsize=(8, 5))

    # Create plot
    # ...

    ax.set_title(f"<Descriptive Title> (n = {len(data):,})", fontsize=12)
    ax.set_xlabel("<X label>")
    ax.set_ylabel("<Y label>")
    ax.legend()
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return fig
```

---

## Experiment Script Structure

```python
"""
Experiment EXP-XXX: <Title>
Implements the analysis plan from design.md.
"""
from pathlib import Path

import numpy as np
import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns
# from tqdm.auto import tqdm  # Use when orchestration has long outer loops.

from xen.linebreak_generator import generate_linebreak
from xen.renko_generator import generate_renko
from xen.heiken_ashi_generator import generate_heiken_ashi

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
DATA_DIR = Path("data")
timebars_path = sorted(DATA_DIR.glob("timebars/timebars_*.parquet"))[-1]

# --------------------------------------------------------------------------- #
# Load scoped analysis data
# --------------------------------------------------------------------------- #
scan = pl.scan_parquet(timebars_path).sort("CloseTime")

# Apply global holdout — first 70% of CloseTime-ordered data.
total_rows = int(scan.select(pl.len()).collect().item())
analysis_cutoff = int(total_rows * 0.7)
df = scan.slice(0, analysis_cutoff).collect()

# Generate derived views on-demand if needed
# lb_bars = generate_linebreak(df, level=3)
# renko_bars = generate_renko(df, atr_period=14)
# ha_candles = generate_heiken_ashi(df)

# --------------------------------------------------------------------------- #
# Apply scope filtering
# --------------------------------------------------------------------------- #
# Filter by instrument, chart type, etc. per scope document
# e.g., eurusd_data = df.filter(pl.col("Symbol") == "EURUSD")

# --------------------------------------------------------------------------- #
# Execute analysis steps
# --------------------------------------------------------------------------- #
# Call analysis functions in plan order
# result_1 = compute_something(df)

# --------------------------------------------------------------------------- #
# Produce visualisations
# --------------------------------------------------------------------------- #
# fig = plot_something(df)
# fig.savefig("python/experiments/EXP-XXX/plots/<name>.png", dpi=150, bbox_inches='tight')

# --------------------------------------------------------------------------- #
# Output results
# --------------------------------------------------------------------------- #
# Print or save numerical results
# print(f"Result: {result_1}")
```

---

## Organisation, Logging, and Performance Standards

Current expectations:

- Put imports first, then path setup, constants, small I/O helpers, pure
  computation helpers, plotting helpers, orchestration, and `main()`.
- Use clear section separators for non-trivial scripts, following the VAL-001
  style: constants, dataclasses/types, small helpers, pure computation,
  plotting/output, orchestration, and `main()`.
- Keep file I/O in orchestration. Reusable functions accept and return
  DataFrames, arrays, dictionaries, or figures.
- Create `plots/` and `results/` directories in orchestration, not as a side
  effect of importing the module.
- Use concise progress logging. Prefer `logging.getLogger(__name__)` for new
  code; `print()` is acceptable only for short manual-run summaries in legacy
  experiment scripts.
- Use `tqdm.auto.tqdm` for expensive outer loops and repeated iterations. Do
  not emit one log line per row or per tiny operation; surface section headers,
  progress bars, key counts, and final summaries.
- Resolve input files dynamically from `DATA_DIR` unless the approved scope
  pins exact files for reproducibility. If exact files are pinned, fail loudly
  when they are missing.
- Use lazy Polars scans for large Parquet inputs, select only required columns,
  sort by the governing timestamp before slicing, and collect only the analysis
  set.
- Use Polars efficiently: push filters/projections into lazy scans, aggregate
  before collection when possible, avoid `iter_rows()` on large frames, avoid
  repeated `pl.concat()` inside loops, and prefer joins/window expressions over
  Python loops when that is semantically equivalent.
- Reuse already-loaded/generated analysis data for plots by returning bounded
  plot inputs from the analysis pass. Do not run a second full load/generation
  pass just to build visualisations.
- Avoid row-wise Python loops over large arrays when Polars, NumPy, or
  `searchsorted` can express the computation directly.
- Do not vectorize by changing the problem. Optimizations must not introduce
  look-ahead bias, use rows after the event timestamp, treat a batch-only
  operation as if it were streaming-safe, silently sample or deduplicate data,
  or alter duplicate-event denominators.
- Bound plotting memory by aggregating first or by deterministic sampling with a
  fixed seed. Do not convert millions of rows to pandas solely for plotting.
- For zero-baseline metrics, do not report percentage improvement. Emit absolute
  differences or a separate metric kind so plots and threshold tables remain
  finite and interpretable.
- For event streams that can emit multiple rows at the same timestamp,
  define whether same-source rows are excluded, merged, or counted before
  computing rates. Do not let zero-duration duplicate-source rows silently
  dominate denominators.
- Heiken Ashi `HAClose` returns are allowed only for approved synthetic-price
  distortion diagnostics. Label them as non-tradable and keep them separate from
  strategy returns, signal validation, and P&L.

### Self-Check Before Completion

Before marking an experiment implementation complete, verify:

1. Imports/path setup/constants/helper sections match the sample organization.
2. Output directories are created in `main()` or orchestration only.
3. Every large Parquet read uses lazy scan -> timestamp sort -> first-70% slice
   -> collect, with column projection when possible.
4. No loader uses `.unique()` without scope approval and pre/post row counts.
5. Plotting inputs are aggregated or deterministically sampled before pandas
   conversion.
6. Expensive generated chart data is not recomputed for plotting if the
   analysis pass already computed it.
7. Long-running loops use `tqdm` progress tracking, while helper functions stay
   quiet and return structured data.
8. Python row loops over large frames are replaced with Polars/NumPy/vectorized
   logic where the replacement is causally equivalent.
9. Any remaining heavy loop is genuinely sequential or stateful, explicitly
   bounded, and does not inspect holdout rows.
10. Zero-baseline ratios are finite or explicitly marked undefined.
11. Duplicate-source or duplicate-event timestamp denominators are explicitly defined when relevant.
12. Logging/output is concise and progress-oriented.
13. Any HA synthetic returns are scope-approved diagnostics, not tradable
    returns.

---

## Error Handling Patterns

```python
def safe_computation(data: np.ndarray) -> float:
    """Compute something safely with edge case handling."""
    if len(data) == 0:
        raise ValueError("Input array is empty")
    if np.all(np.isnan(data)):
        raise ValueError("All values are NaN")
    if len(data) < 3:
        raise ValueError(f"Need at least 3 data points, got {len(data)}")

    # Proceed with computation
    ...
```

---

## Anti-Patterns (Avoid)

| Pattern | Why Avoid | Correct Approach |
|---------|-----------|-----------------|
| Hardcoded absolute paths like `/Users/...` | Breaks on other machines | Use `DATA_DIR = Path("data")` relative path |
| `data.dropna()` without checking | Silent data loss | Explicit NaN handling with warnings |
| Mixing computation with plotting | Violates separation of concerns | Separate analysis functions from plot functions |
| Print statements in analysis functions | Side effects | Return data structures, let caller format |
| No progress for multi-minute loops | Manual runs look stalled | Use `tqdm` around expensive outer loops |
| Magic numbers in thresholds | Undocumented assumptions | Derive from data or document explicitly |
| Lines > 100 characters | Readability | Break into multiple lines |
| Functions > 30 lines | Complexity | Split into sub-functions |
| `iter_rows()` or Python row loops on large frames | Slow and memory-inefficient | Use Polars expressions, joins, windows, or NumPy when causally equivalent |
| Unsafe vectorization of sequential logic | Introduces look-ahead or streamed-data violations | Keep a bounded explicit loop or implement a true sequential generator |
| Using synthetic chart prices for P&L | Incorrect P&L | Use real prices aligned by `CloseTime`, event timestamp, or `SourceCloseTime` |
| Acting on the forming bar | Look-ahead bias | Decide at bar **open** on confirmed bars only (`[t-1]`); never read the action bar's own OHLC |
| Open-to-close returns for P&L | `OnClose` not executable live | Use **open-to-open** returns; open-to-close is a labelled non-tradable diagnostic only |
| Aligning data views by bar count | Look-ahead bias | Always align by timestamp (`CloseTime`, event timestamp, or `SourceCloseTime`) |
| Assuming same event count across data views | Logical error | Different event definitions can produce different counts for the same period |
