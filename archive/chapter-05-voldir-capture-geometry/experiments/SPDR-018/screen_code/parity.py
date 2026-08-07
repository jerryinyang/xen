"""Parent parity (design §12) — the anti-drift check.

    "If arm C cannot reproduce SPDR-014's published cells on SPDR-014's own band, the object
     was re-specified — which this design forbids."

Each arm must reproduce its parent's PUBLISHED cell values on the parent's OWN band, to the
tolerance declared in ``config.PARITY_TOL`` before the run. The quantities compared are the ones
that are definitionally identical between parent and arm — the cell's own point estimate and its
count — because those are exactly what a silent re-specification would move.

Parity is a HARD check: a failure invalidates the emission.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import arm_b
import arm_c
import arm_d
import parents
from config import PARITY_MIN_CELLS_PER_ARM, PARITY_TOL


def _cmp(name: str, mine: np.ndarray, theirs: np.ndarray, tol: float, *,
         keys: list | None = None) -> dict:
    m = np.asarray(mine, dtype=float)
    t = np.asarray(theirs, dtype=float)
    both = np.isfinite(m) & np.isfinite(t)
    diff = np.abs(m[both] - t[both])
    worst = int(np.argmax(diff)) if diff.size else -1
    return {
        "quantity": name,
        "n_compared": int(both.sum()),
        "n_parent_cells": int(t.size),
        "tolerance": float(tol),
        "max_abs_diff": float(diff.max()) if diff.size else float("nan"),
        "mean_abs_diff": float(diff.mean()) if diff.size else float("nan"),
        "n_outside_tolerance": int((diff > tol).sum()) if diff.size else 0,
        "worst_cell": (keys[worst] if keys is not None and worst >= 0 and worst < len(keys)
                       else None),
        "reproduced": bool(diff.size > 0 and (diff <= tol).all()),
    }


def arm_b_parity() -> dict:
    """Arm B vs SPDR-013 ``expectancy_by_cell``: the cell mean and the episode count."""
    pub = pd.read_parquet(parents.published("SPDR-013", "expectancy_by_cell.parquet"))
    panel = arm_b.load_panel()
    agg = (panel.groupby(list(arm_b.KEYS), observed=True)
           .agg(mine_mean=(arm_b.NET, "mean"), mine_n=(arm_b.NET, "size"))
           .reset_index())
    j = pub.merge(agg, on=list(arm_b.KEYS), how="left")
    keys = j[list(arm_b.KEYS)].astype(str).agg("|".join, axis=1).tolist()
    return {
        "arm": "B", "parent": "SPDR-013", "band": "the parent's own DESIGN + CONFIRM cells",
        "checks": [
            _cmp("expectancy_partial (cell mean, bps)", j["mine_mean"], j["expectancy_partial"],
                 PARITY_TOL["mean_bps"], keys=keys),
            _cmp("n_episodes", j["mine_n"], j["n_episodes"], PARITY_TOL["n"], keys=keys),
        ],
    }


def arm_c_parity() -> dict:
    """Arm C vs SPDR-014 ``expectancy_by_cell``: the residual mean ``r_h`` and its count."""
    pub = pd.read_parquet(parents.published("SPDR-014", "expectancy_by_cell.parquet"))
    panel = arm_c.load_panel()
    keys = ["symbol", "source", "z", "H", "event", "h", "band", "clock", "policy"]
    # the panel's own `event` column is a counter; the parent's published `event` axis is the
    # breach type, which the panel calls `event_type`.
    p = panel.drop(columns=["event"]).rename(columns={"event_type": "event"})
    agg = (p.groupby(keys, observed=True)
           .agg(mine_mean_r_h=("r_h", "mean"), mine_n=("r_h", "size")).reset_index())
    pub2 = pub.copy()
    j = pub2.merge(agg, on=keys, how="left")
    kk = j[keys].astype(str).agg("|".join, axis=1).tolist()
    return {
        "arm": "C", "parent": "SPDR-014", "band": "the parent's own DESIGN + CONFIRM cells",
        "checks": [
            _cmp("mean_r_h (residual mean, bps)", j["mine_mean_r_h"], j["mean_r_h"],
                 PARITY_TOL["mean_bps"], keys=kk),
            _cmp("n_decided", j["mine_n"], j["n_decided"], PARITY_TOL["n"], keys=kk),
        ],
    }


def arm_d_parity() -> dict:
    """Arm D vs SPDR-015 ``per_stratum_2b``: the ordinal hit rate on the parent's own band."""
    pub = pd.read_parquet(parents.published("SPDR-015", "per_stratum_2b.parquet"))
    # SPDR-015 scored 2b over the WHOLE TRAIN span in one number — which is precisely why its
    # CONFIRM slice was never scored separately (D8). Parity is therefore taken on that span.
    z = arm_d.zz_panel()
    agg = (z.assign(hit=lambda d: ((d["p"] >= 0.5).astype(float) == d["y"].astype(float))
                    .astype(float))
           .groupby(["symbol", "target", "model"], observed=True)
           .agg(mine_hit=("hit", "mean"), mine_n=("hit", "size")).reset_index())
    j = pub.merge(agg, on=["symbol", "target", "model"], how="left")
    kk = j[["symbol", "target", "model"]].astype(str).agg("|".join, axis=1).tolist()
    return {
        "arm": "D", "parent": "SPDR-015", "band": "the parent's own scored origins (full TRAIN span — see D8)",
        "checks": [
            _cmp("hit_rate", j["mine_hit"], j["hit_rate"], PARITY_TOL["rate"], keys=kk),
            _cmp("n_oos", j["mine_n"], j["n_oos"], PARITY_TOL["n"], keys=kk),
        ],
    }


def arm_a_parity() -> dict:
    """Arm A vs SPDR-012 ``metrics_by_cell``: the V-REGIME HIGH-LOW magnitude gap."""
    pub = pd.read_parquet(parents.published("SPDR-012", "metrics_by_cell.parquet"))
    pub = pub[(pub["arm"] == "V-REGIME") & (pub["metric"] == "gap_high_low_bps")]
    import arm_a
    panel = arm_a.load_panel()
    df = panel[panel["regime_state"].notna()]
    rows = []
    for (sym, clock, band), g in df.groupby(["symbol", "clock", "band"], observed=True):
        v = g["target_abs_oo"].to_numpy(dtype=float)
        hi = g["regime_state"].to_numpy(dtype=float) == 1
        ok = np.isfinite(v)
        v, hi = v[ok], hi[ok]
        if not hi.any() or not (~hi).any():
            continue
        rows.append({"symbol": sym, "clock": clock, "band": band,
                     "mine_gap": float(v[hi].mean() - v[~hi].mean()),
                     "mine_n": int(v.size)})
    agg = pd.DataFrame(rows)
    j = pub.merge(agg, on=["symbol", "clock", "band"], how="left")
    kk = j[["symbol", "clock", "band"]].astype(str).agg("|".join, axis=1).tolist()
    return {
        "arm": "A", "parent": "SPDR-012", "band": "the parent's own DESIGN + CONFIRM cells",
        "checks": [_cmp("gap_high_low_bps", j["mine_gap"], j["value"],
                        PARITY_TOL["mean_bps"], keys=kk)],
    }


def run() -> dict:
    arms = [arm_a_parity(), arm_b_parity(), arm_c_parity(), arm_d_parity()]
    for a in arms:
        a["min_cells_required"] = PARITY_MIN_CELLS_PER_ARM
        a["enough_cells"] = all(c["n_compared"] >= PARITY_MIN_CELLS_PER_ARM for c in a["checks"])
        a["reproduced"] = bool(a["enough_cells"] and all(c["reproduced"] for c in a["checks"]))
    return {
        "check": "PARENT PARITY",
        "severity": "HARD",
        "statement": ("each arm reproduces its parent's published cell values on the parent's own "
                      "band — the proof that no object was silently re-specified (design §12)"),
        "tolerances_declared_before_run": PARITY_TOL,
        "arms": arms,
        "all_reproduced": bool(all(a["reproduced"] for a in arms)),
    }
