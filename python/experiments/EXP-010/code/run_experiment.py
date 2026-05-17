"""
Experiment EXP-010: Line Break as a Confirmation Layer Over Renko Signals.
Implements the approved scope and analysis plan.
"""
import sys
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = PYTHON_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from signal_quality import run_signal_quality_experiment


def main() -> None:
    """Run the experiment."""
    run_signal_quality_experiment("EXP-010")


if __name__ == "__main__":
    main()
