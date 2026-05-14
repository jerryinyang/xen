# Code Conventions

Project-specific code conventions for the Xen research pipeline.

---

## Standard Data Loading Pattern

All experiment scripts should use this loading pattern:

```python
"""
Experiment EXP-XXX: <Title>
Implements the analysis plan from analysis-plan.md.
"""
import sys
sys.path.insert(0, "python/src")

import numpy as np
import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

DATA_DIR = Path("data")

# Load time bars — baseline for all comparisons
timebars_path = sorted(DATA_DIR.glob("timebars/timebars_*.parquet"))[-1]
df = (
    pl.scan_parquet(timebars_path)
    .sort("CloseTime")
    .collect()
)

# Apply global holdout split — only the first 70% of CloseTime-ordered data
total_rows = len(df)
analysis_cutoff = int(total_rows * 0.7)
analysis_set = df.slice(0, analysis_cutoff)

# Within analysis set: train/test chronological split
train_cutoff = int(analysis_cutoff * 0.7)
train_set = analysis_set.slice(0, train_cutoff)
test_set = analysis_set.slice(train_cutoff, analysis_cutoff - train_cutoff)

# Generate chart types on-demand from the scoped source data
from linebreak_generator import generate_linebreak
lb_bars = generate_linebreak(analysis_set, level=3)

# Apply experiment-specific filtering from scope document
# e.g., eurusd_data = analysis_set.filter(pl.col("Symbol") == "EURUSD")
```

**Important**:
- `Direction` is an **int32 column** (`+1` for Up, `-1` for Down). Handle accordingly.
- Use `CloseTime` for temporal ordering of time bars, `SourceCloseTime` for chart-type bars.
- For cross-chart-type comparisons, align by timestamp — never by bar index.
- Strategy P&L must use real prices. Heiken Ashi returns use `RealClose` (never `HAClose`); Renko and Line Break signals use `SourceCloseTime` to align to real time-bar prices.
- Chart-type generators are deterministic: same input + same parameters = same output.

---

## Existing Analysis Modules

Check these modules before creating new reusable functions:

| Module | Path | Key Functions |
|--------|------|--------------|
| Line Break Generator | `python/src/linebreak_generator.py` | `generate_linebreak()` |
| Renko Generator | `python/src/renko_generator.py` | `generate_renko()` |
| Heiken Ashi Generator | `python/src/heiken_ashi_generator.py` | `generate_heiken_ashi()` |
| Correlation | `python/src/correlation.py` | `compute_spearman_with_bootstrap()`, `compute_pearson()` |
| Mean Reversion | `python/src/mean_reversion.py` | `compute_hurst_exponent()`, `test_mean_reversion()` |
| Regression | `python/src/regression.py` | `rank_regression()`, `compute_effect_sizes()` |

If a function you need already exists, import and use it. Do not re-implement.

**Xen Data Access Pattern**:
```python
from pathlib import Path
from linebreak_generator import generate_linebreak
from renko_generator import generate_renko
from heiken_ashi_generator import generate_heiken_ashi

DATA_DIR = Path("data")

def load_time_bars(
    instrument: str | None = None,
) -> pl.DataFrame:
    """Load time bars with optional instrument filtering."""
    path = sorted(DATA_DIR.glob("timebars/timebars_*.parquet"))[-1]
    scan = pl.scan_parquet(path)
    
    if instrument:
        # Filter by symbol in filename or column if available
        pass
    
    return scan.sort("CloseTime").collect()


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
Implements the analysis plan from analysis-plan.md.
"""
import sys
sys.path.insert(0, "python/src")

import numpy as np
import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from linebreak_generator import generate_linebreak
from renko_generator import generate_renko
from heiken_ashi_generator import generate_heiken_ashi

# === 1. Load data ===
DATA_DIR = Path("data")
timebars_path = sorted(DATA_DIR.glob("timebars/timebars_*.parquet"))[-1]

df = (
    pl.scan_parquet(timebars_path)
    .sort("CloseTime")
    .collect()
)

# Apply global holdout — first 70% of CloseTime-ordered data
total_rows = len(df)
analysis_cutoff = int(total_rows * 0.7)
df = df.slice(0, analysis_cutoff)

# Generate chart types on-demand if needed
# lb_bars = generate_linebreak(df, level=3)
# renko_bars = generate_renko(df, atr_period=14)
# ha_candles = generate_heiken_ashi(df)

# === 2. Apply scope filtering ===
# Filter by instrument, chart type, etc. per scope document
# e.g., eurusd_data = df.filter(pl.col("Symbol") == "EURUSD")

# === 3. Execute analysis steps ===
# Call analysis functions in plan order
# result_1 = compute_something(df)

# === 4. Produce visualisations ===
# fig = plot_something(df)
# fig.savefig("python/experiments/EXP-XXX/plots/<name>.png", dpi=150, bbox_inches='tight')

# === 5. Output results ===
# Print or save numerical results
# print(f"Result: {result_1}")
```

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
| Magic numbers in thresholds | Undocumented assumptions | Derive from data or document explicitly |
| Lines > 100 characters | Readability | Break into multiple lines |
| Functions > 30 lines | Complexity | Split into sub-functions |
| Using synthetic chart prices for P&L | Incorrect P&L | Use real prices aligned by `CloseTime` or `SourceCloseTime` |
| Aligning chart types by bar count | Look-ahead bias | Always align by timestamp (CloseTime/SourceCloseTime) |
| Assuming same bar count across chart types | Logical error | Different chart types produce different bar counts for same period |
