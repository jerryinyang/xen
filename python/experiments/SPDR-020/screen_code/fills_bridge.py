"""Import SPDR-019's M1 fill resolver — one implementation, shared by 019 and 020.

design §2.2a: L4 target/trail resolve on M1 with adverse precedence. Entry stays
parent open[j+1]. Two copies of the exit rule would be two objects.
"""
from __future__ import annotations

import importlib.util
import sys

from config import NS, PARENT_019_CODE

# Ensure SPDR-020 config is the `config` fills.py will bind (NS identical).
_fills_path = PARENT_019_CODE / "fills.py"
if not _fills_path.is_file():
    raise FileNotFoundError(f"SPDR-019 fills.py missing at {_fills_path}")

_spec = importlib.util.spec_from_file_location("spdr019_fills", _fills_path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"cannot load {_fills_path}")
fills = importlib.util.module_from_spec(_spec)
# register before exec so @dataclass can resolve cls.__module__
sys.modules["spdr019_fills"] = fills
# fills.py does `from config import NS` — SPDR-020 config already on path
_spec.loader.exec_module(fills)

# re-export the binding surface
ExitFill = fills.ExitFill
EXIT_TIME = fills.EXIT_TIME
EXIT_TARGET = fills.EXIT_TARGET
EXIT_TRAIL = fills.EXIT_TRAIL
resolve_time_exit = fills.resolve_time_exit
resolve_target_trail_time = fills.resolve_target_trail_time
signed_r_bps = fills.signed_r_bps
bps_to_price_width = fills.bps_to_price_width
both_reachable_in_bar = fills.both_reachable_in_bar

# prove we bound the same module file
FILLS_SOURCE_PATH = str(_fills_path.resolve())
assert abs(NS - 1_000_000_000) < 1, "NS must match SPDR-019 fills convention"


def first_m1_at_or_after(ts: "object", at_ns: int) -> int:
    """Index of first M1 bar with ts >= at_ns (entry open)."""
    import numpy as np
    return int(np.searchsorted(ts, at_ns, side="left"))
