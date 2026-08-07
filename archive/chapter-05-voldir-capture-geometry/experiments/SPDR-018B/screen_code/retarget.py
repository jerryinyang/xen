"""Point the parents' own code at the cTrader catalog, without editing a line of parent source.

Design §4: no parent screen ever ran on cTrader, so no parent panel exists to re-score. Every
object here is BUILT by the parents' own modules against cTrader bars. The only thing that
changes is where the bars come from and which calendar bounds the bands use.

Mechanism. Each parent module does ``from config import DESIGN_START, CATALOG_BAR_DIR, ...`` at
import time, which binds those names into *that module's* globals. Patching the parent's
``config`` alone therefore misses every module that already copied the value. So the rebind walks
**every loaded module of the parent** and replaces the name wherever it appears.

This is a data retarget, not an object change — and design §5 makes that claim checkable: the
same retargeted path is run against a Bybit symbol and must reproduce SPDR-018's cells exactly.
"""
from __future__ import annotations

import contextlib
from datetime import datetime, timezone

import parents          # SPDR-018's loader, reused unchanged
from config18b import (
    CTRADER_BAR_DIR,
    CTRADER_BAR_TYPE_SUFFIX,
    CTRADER_CONFIRM_END,
    CTRADER_CONFIRM_START,
    CTRADER_DESIGN_END,
    CTRADER_DESIGN_START,
    CTRADER_HOLDOUT_START,
)

#: Names rebound on every module of a parent that carries them.
_BAND_NAMES = {
    "DESIGN_START": CTRADER_DESIGN_START,
    "DESIGN_END": CTRADER_DESIGN_END,
    "CONFIRM_START": CTRADER_CONFIRM_START,
    "CONFIRM_END": CTRADER_CONFIRM_END,
    "TRAIN_END": CTRADER_CONFIRM_END,
    "TEST_START": CTRADER_CONFIRM_END,
    "HOLDOUT_START": CTRADER_HOLDOUT_START,
}
_CATALOG_NAMES = {
    "CATALOG_BAR_DIR": CTRADER_BAR_DIR,
    "BAR_TYPE_SUFFIX": CTRADER_BAR_TYPE_SUFFIX,
}


def _bands_dict() -> dict:
    return {"DESIGN": (CTRADER_DESIGN_START, CTRADER_DESIGN_END),
            "CONFIRM": (CTRADER_CONFIRM_START, CTRADER_CONFIRM_END)}


def rebind(parent: str) -> dict:
    """Rebind catalog + band constants across every loaded module of ``parent``.

    Returns the map of what was changed, per module, so the retarget is auditable rather than
    invisible. Idempotent.
    """
    mods = parents.load(parent)
    changed: dict[str, list[str]] = {}
    targets = {**_BAND_NAMES, **_CATALOG_NAMES}
    for mod_name, mod in mods.items():
        hits = []
        for name, value in targets.items():
            if hasattr(mod, name):
                setattr(mod, name, value)
                hits.append(name)
        if hasattr(mod, "BANDS"):
            setattr(mod, "BANDS", _bands_dict())
            hits.append("BANDS")
        if hits:
            changed[mod_name] = sorted(hits)
    return changed


def ctrader_manifest():
    """The cTrader fence, loaded from its EXPLICIT path and hash-verified (never the Bybit default)."""
    from config18b import CTRADER_FENCE_PATH, CTRADER_FENCE_SHA256
    from xen.nautilus.catalog_fence import load_fence_manifest
    m = load_fence_manifest(CTRADER_FENCE_PATH)
    if m.sha256 != CTRADER_FENCE_SHA256:
        raise AssertionError(
            f"cTrader fence sha256 mismatch: expected {CTRADER_FENCE_SHA256}, got {m.sha256}")
    return m


@contextlib.contextmanager
def bybit_original(parent: str):
    """Temporarily restore a parent's own Bybit constants — used by the §5 identity guard.

    The cross-universe guard has to run the SAME retargeted code path against Bybit data, so it
    needs the original bindings back for the duration of that check.
    """
    mods = parents.load(parent)
    cfg = mods["config"]
    # the parent's config module still holds its own literals only if it was not rebound; so the
    # canonical Bybit values are taken from SPDR-018's config, which is never retargeted.
    import config as c18
    original = {
        "DESIGN_START": c18.DESIGN_START, "DESIGN_END": c18.DESIGN_END,
        "CONFIRM_START": c18.CONFIRM_START, "CONFIRM_END": c18.CONFIRM_END,
        "TRAIN_END": c18.TRAIN_END, "TEST_START": c18.TEST_START,
        "HOLDOUT_START": c18.HOLDOUT_START,
        "CATALOG_BAR_DIR": c18.CATALOG_BAR_DIR, "BAR_TYPE_SUFFIX": c18.BAR_TYPE_SUFFIX,
    }
    bands = {"DESIGN": (c18.DESIGN_START, c18.DESIGN_END),
             "CONFIRM": (c18.CONFIRM_START, c18.CONFIRM_END)}
    saved: dict[str, dict] = {}
    for mod_name, mod in mods.items():
        saved[mod_name] = {}
        for name, value in original.items():
            if hasattr(mod, name):
                saved[mod_name][name] = getattr(mod, name)
                setattr(mod, name, value)
        if hasattr(mod, "BANDS"):
            saved[mod_name]["BANDS"] = getattr(mod, "BANDS")
            setattr(mod, "BANDS", bands)
    del cfg
    try:
        yield
    finally:
        for mod_name, mod in mods.items():
            for name, value in saved.get(mod_name, {}).items():
                setattr(mod, name, value)


def verify(parent: str) -> dict:
    """Confirm the rebind actually took on the modules that matter."""
    mods = parents.load(parent)
    out = {}
    for mod_name, mod in mods.items():
        row = {}
        for name in ("DESIGN_START", "CONFIRM_END", "CATALOG_BAR_DIR", "BAR_TYPE_SUFFIX"):
            if hasattr(mod, name):
                v = getattr(mod, name)
                row[name] = str(v)
        if row:
            out[mod_name] = row
    return out


def assert_ctrader_only(ts_ns, *, where: str) -> None:
    """HARD: nothing at or beyond the cTrader train_end, and the cTrader holdout never touched."""
    import numpy as np
    from config18b import CTRADER_HOLDOUT_START_NS, CTRADER_TRAIN_END_NS
    ts = np.asarray(ts_ns, dtype="int64")
    ts = ts[ts > 0]
    if ts.size == 0:
        return
    hi = int(ts.max())
    if hi >= CTRADER_TRAIN_END_NS:
        raise AssertionError(f"{where}: crossed the cTrader TRAIN fence ({hi})")
    if hi >= CTRADER_HOLDOUT_START_NS:
        raise AssertionError(f"{where}: touched the sealed cTrader holdout")


UTC = timezone.utc
_ = datetime  # re-exported for callers building band bounds
