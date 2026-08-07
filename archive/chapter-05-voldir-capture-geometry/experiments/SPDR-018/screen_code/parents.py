"""Isolated loader for the four parent screens' modules + their published results.

Design §1.1: "Reuse the parents' ``screen_code/``. 012/013/014/015 code is the substrate."

The four parents all use bare intra-package imports (``from config import ...``) and all define
modules with the SAME names (``config``, ``universe``, ``catalog_io``, ``stats_core``,
``controls``). Importing more than one of them into a single interpreter therefore needs an
isolated loader: each parent is imported under a private module-name prefix with its own
``sys.path`` entry, and the modules it pulls in are re-keyed so the next parent cannot collide
with it.

Nothing here re-implements a parent object. It only makes the parents' constants and pure
helpers importable, and locates their published artifacts for the parent-parity check (§12).
"""
from __future__ import annotations

import importlib
import sys
import threading
from pathlib import Path
from types import ModuleType

from config import EXPERIMENTS_DIR, PARENTS

_LOCK = threading.Lock()
_CACHE: dict[str, dict[str, ModuleType]] = {}

# Modules worth loading per parent. Kept explicit so an accidental heavyweight import
# (a parent's run_screen, which executes argparse at import time in some parents) never happens.
_MODULES = {
    "SPDR-012": ("config", "stats_core", "universe", "catalog_io", "features", "hmm",
                 "models", "pipeline", "arms", "cross_section"),
    "SPDR-013": ("config", "stats_core", "universe", "catalog_io", "indicators", "arms",
                 "expectancy", "capture", "zz_forecast", "run_screen"),
    "SPDR-014": ("config", "stats_core", "universe", "catalog_io", "indicators", "costs",
                 "prepare", "engine"),
    "SPDR-015": ("config", "controls", "universe", "catalog_io", "features", "hmm",
                 "transitions", "zz_ordinal"),
}


def parent_dir(parent: str) -> Path:
    if parent not in PARENTS:
        raise KeyError(f"{parent!r} is not one of the four parents {PARENTS}")
    return EXPERIMENTS_DIR / parent


def screen_code_dir(parent: str) -> Path:
    return parent_dir(parent) / "screen_code"


def results_dir(parent: str) -> Path:
    return parent_dir(parent) / "results"


def load(parent: str) -> dict[str, ModuleType]:
    """Import ``parent``'s screen modules in isolation. Cached; thread-safe.

    Returns ``{module_name: module}``. The modules are removed from ``sys.modules`` under their
    bare names afterwards, so a later parent's ``config`` cannot be shadowed by this one's.
    """
    with _LOCK:
        if parent in _CACHE:
            return _CACHE[parent]

        code_dir = screen_code_dir(parent)
        if not code_dir.is_dir():
            raise FileNotFoundError(f"parent screen_code missing: {code_dir}")

        wanted = _MODULES[parent]
        sys.path.insert(0, str(code_dir))
        loaded: dict[str, ModuleType] = {}
        try:
            for name in wanted:
                # drop any same-named module from an earlier parent before importing
                for key in [k for k in sys.modules if k == name or k.startswith(name + ".")]:
                    del sys.modules[key]
                loaded[name] = importlib.import_module(name)
        finally:
            sys.path.remove(str(code_dir))
            # Re-key ONLY the modules that came from this parent's screen_code (identified by
            # __file__), so a later parent's same-named module cannot be shadowed. Third-party
            # modules (numpy & friends) are left in place — several cannot be re-imported.
            prefix = f"_{parent.replace('-', '_')}__"
            for key in list(sys.modules):
                mod = sys.modules[key]
                f = getattr(mod, "__file__", None)
                if f and Path(f).parent == code_dir:
                    sys.modules.pop(key)
                    sys.modules[prefix + key] = mod

        _CACHE[parent] = loaded
        return loaded


def const(parent: str, name: str):
    """One frozen constant from a parent's ``config`` — the single source of truth for it."""
    cfg = load(parent)["config"]
    if not hasattr(cfg, name):
        raise AttributeError(f"{parent} config has no {name!r}")
    return getattr(cfg, name)


def published(parent: str, filename: str) -> Path:
    """Path to a parent's published artifact (parent-parity material, §12)."""
    p = results_dir(parent) / filename
    if not p.exists():
        raise FileNotFoundError(f"{parent} published artifact missing: {p}")
    return p


ARM_PARENT = {"A": "SPDR-012", "B": "SPDR-013", "C": "SPDR-014", "D": "SPDR-015"}

#: Each arm's row-level panel — the parent's OWN emission, spanning the full TRAIN fence.
ARM_PANELS = {
    "A": ("SPDR-012", ("vol_reliability.parquet", "xs_panel.parquet")),
    "B": ("SPDR-013", ("episodes.parquet",)),
    "C": ("SPDR-014", ("post_event.parquet", "straddle.parquet")),
    "D": ("SPDR-015", ("regime_states.parquet", "zz_ordinal.parquet")),
}

#: Each parent's published cell tables — the parity targets (§12).
ARM_PARITY_TABLES = {
    "A": ("metrics_by_cell.parquet",),
    "B": ("expectancy_by_cell.parquet",),
    "C": ("expectancy_by_cell.parquet", "perstratum_final.parquet"),
    "D": ("per_stratum_2a.parquet", "per_stratum_2b.parquet",
          "transition_metrics.parquet", "run_length_metrics.parquet"),
}
