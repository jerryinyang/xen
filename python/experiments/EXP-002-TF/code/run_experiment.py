"""
Experiment EXP-002-TF: Timeframe Replication of Volatility & Trend Regime Representation.
Implements the approved scope and analysis plan.
"""
import sys
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = PYTHON_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from timeframe_replication import run_tf_experiment


def main() -> None:
    """Run the experiment."""
    run_tf_experiment("EXP-002-TF")


if __name__ == "__main__":
    main()
