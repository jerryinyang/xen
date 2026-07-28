"""Re-derive `at_parent_target_precision` with the precision target expressed in SIGMA units.

Carrying SPDR-013/014's ABSOLUTE 10 bps MDE rule from a sigma = 73 bps universe into a
sigma = 13 bps universe silently loosened it 5.6x — inflating every powered count and, per the
analyst, manufacturing a `trail` selection artifact. The target is a NOISE quantity, so it is
deflated by the sigma ratio, not by the payoff ratio used for cost.
"""
from __future__ import annotations
import numpy as np, pandas as pd
from deflators import sigma_ratio

ABS_TARGET_BPS = {"B": 10.0, "C": 10.0}


def apply(df: pd.DataFrame) -> pd.DataFrame:
    r = sigma_ratio()
    d = df.copy()
    if "arm" not in d:
        return d
    mde = pd.to_numeric(d.get("net_block_mde_mean_bps"), errors="coerce")
    n = pd.to_numeric(d.get("n"), errors="coerce")
    nd = pd.to_numeric(d.get("n_dates"), errors="coerce")
    d["target_mde_bps_absolute__SUPERSEDED"] = d.get("target_mde")
    scaled = d["arm"].map(lambda a: ABS_TARGET_BPS.get(a, np.nan)) * r
    d["target_mde_bps_sigma_scaled"] = scaled
    d["sigma_target_deflator"] = r
    ok = (mde <= scaled) & (nd >= 30)
    ok &= np.where(d["arm"].eq("C"), n >= 80, n >= 0)
    d["at_parent_target_precision_absolute__SUPERSEDED"] = d.get("at_parent_target_precision")
    d.loc[d["arm"].isin(["B", "C"]), "at_parent_target_precision"] = ok[d["arm"].isin(["B", "C"])]
    d["precision_basis"] = np.where(d["arm"].isin(["B", "C"]), "SIGMA_SCALED", "parent_absolute")
    return d
