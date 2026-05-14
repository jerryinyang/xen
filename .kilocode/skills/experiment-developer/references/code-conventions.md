# Code Conventions

Project-specific code conventions for the TriLattice research pipeline.

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

# Load data using Polars/Parquet
DATA_DIR = Path("/Users/jerryinyang/cAlgo/Sources/Robots/TriLattice/TriLattice/data")
path = sorted(DATA_DIR.glob("features_*.parquet"))[-1]  # Latest features file

df = (
    pl.scan_parquet(path)
    .select(["ConfirmTime", "Label", "Regime", "BarReturn", "ValidationStatus"])
    .filter(pl.col("ValidationStatus") == "Valid")  # Adjust as per scope
    .sort("ConfirmTime")
    .collect()
)

# Apply global holdout split — only the first 70% of ConfirmTime-ordered data
total_rows = len(df)
analysis_cutoff = int(total_rows * 0.7)
analysis_set = df.slice(0, analysis_cutoff)

# Within analysis set: train/test chronological split
train_cutoff = int(analysis_cutoff * 0.7)
train_set = analysis_set.slice(0, train_cutoff)
test_set = analysis_set.slice(train_cutoff, analysis_cutoff - train_cutoff)

# Apply experiment-specific filtering from scope document
# e.g., eur_data = train_set.filter(pl.col("Symbol") == "EURUSD")
```

**Important**: 
- `Label` is a **string column** (`"HH"`, `"HL"`, `"LH"`, `"LL"`). Handle accordingly.
- `Regime` is a **string column** (`"Low"`, `"Medium"`, `"High"`).
- Use `ConfirmTime` for all temporal ordering, not `PeakTime` (look-ahead bias prevention).

---

## Existing Analysis Modules

Check these modules before creating new reusable functions:

| Module | Path | Key Functions |
|--------|------|--------------|
| Correlation | `python/src/correlation.py` | `compute_spearman_with_bootstrap()`, `compute_pearson()` |
| Mean Reversion | `python/src/mean_reversion.py` | `compute_hurst_exponent()`, `test_mean_reversion()` |
| Regression | `python/src/regression.py` | `rank_regression()`, `compute_effect_sizes()` |
| Structure | `python/src/structure.py` | Label transition analysis, sequence processing |

If a function you need already exists, import and use it. Do not re-implement.

**TriLattice Data Access Pattern**:
```python
from pathlib import Path

DATA_DIR = Path("/Users/jerryinyang/cAlgo/Sources/Robots/TriLattice/TriLattice/data")
FEATURES_PATH = sorted(DATA_DIR.glob("features_*.parquet"))[-1]

def load_tri_lattice_features(
    columns: list[str] | None = None,
    validation_status: str = "Valid",
) -> pl.DataFrame:
    """Load TriLattice features with optional filtering."""
    scan = pl.scan_parquet(FEATURES_PATH)
    
    if columns:
        scan = scan.select(columns)
    
    if validation_status:
        scan = scan.filter(pl.col("ValidationStatus") == validation_status)
    
    return scan.sort("ConfirmTime").collect()
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
# Import existing analysis modules as needed
# from correlation import compute_spearman_with_bootstrap

# === 1. Load data ===
DATA_DIR = Path("/Users/jerryinyang/cAlgo/Sources/Robots/TriLattice/TriLattice/data")
path = sorted(DATA_DIR.glob("features_*.parquet"))[-1]

df = (
    pl.scan_parquet(path)
    .select(["ConfirmTime", "Label", "Regime", "BarReturn", "ValidationStatus"])
    .filter(pl.col("ValidationStatus") == "Valid")
    .sort("ConfirmTime")
    .collect()
)

# Apply global holdout — first 70% of ConfirmTime-ordered data
total_rows = len(df)
analysis_cutoff = int(total_rows * 0.7)
df = df.slice(0, analysis_cutoff)

# === 2. Apply scope filtering ===
# Filter by instrument, regime, label, etc. per scope document
# e.g., df = df.filter(pl.col("Regime") == "Low")

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
| Hardcoded paths like `/Users/...` | Breaks on other machines | Use `DATA_PATH` registry or relative paths |
| `data.dropna()` without checking | Silent data loss | Explicit NaN handling with warnings |
| Mixing computation with plotting | Violates separation of concerns | Separate analysis functions from plot functions |
| Print statements in analysis functions | Side effects | Return data structures, let caller format |
| Magic numbers in thresholds | Undocumented assumptions | Derive from data or document explicitly |
| Lines > 100 characters | Readability | Break into multiple lines |
| Functions > 30 lines | Complexity | Split into sub-functions |
