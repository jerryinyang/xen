"""Parent parity vs SPDR-014 published cells (design §2.2, §12).

Reproduce at z=1.5 / H=12 / h=12 / E-TOUCH / Z-VOL / DESIGN to |Δ| ≤ 1e-9 on
mean_r_h, p_momo, p_mr, n_decided → results/parent_parity.json.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import PARENT_014_RESULTS, PARITY_SLICE, PARITY_TOL
from event_engine import parity_cell_stats


def compare_symbol(symbol: str, posts: list[dict], parent_row: pd.Series | None) -> dict:
    mine = parity_cell_stats(posts)
    if parent_row is None or parent_row.empty:
        return {
            "symbol": symbol, "status": "NO_PARENT_ROW",
            "mine": mine, "parent": None, "reproduced": False,
        }
    checks = {}
    all_ok = True
    for col in ("mean_r_h", "p_momo", "p_mr", "n_decided"):
        mv = mine[col]
        pv = float(parent_row[col]) if np.isfinite(parent_row[col]) else float("nan")
        if col == "n_decided":
            diff = abs(float(mv) - pv) if np.isfinite(pv) else float("nan")
            ok = bool(np.isfinite(diff) and diff <= PARITY_TOL) or (mv == 0 and (not np.isfinite(pv) or pv == 0))
        else:
            if not np.isfinite(mv) and not np.isfinite(pv):
                diff, ok = 0.0, True
            elif not np.isfinite(mv) or not np.isfinite(pv):
                diff, ok = float("nan"), False
            else:
                diff = abs(float(mv) - pv)
                ok = bool(diff <= PARITY_TOL)
        checks[col] = {"mine": mv, "parent": pv, "abs_diff": diff, "ok": ok}
        all_ok = all_ok and ok
    return {
        "symbol": symbol,
        "status": "OK" if all_ok else "FAIL",
        "slice": PARITY_SLICE,
        "checks": checks,
        "reproduced": all_ok,
        "tolerance": PARITY_TOL,
    }


def load_parent_expectancy() -> pd.DataFrame:
    path = PARENT_014_RESULTS / "expectancy_by_cell.parquet"
    df = pd.read_parquet(path)
    m = (
        (df["z"] == PARITY_SLICE["z"])
        & (df["H"] == PARITY_SLICE["H"])
        & (df["h"] == PARITY_SLICE["h"])
        & (df["event"] == PARITY_SLICE["event"])
        & (df["source"] == PARITY_SLICE["source"])
        & (df["band"] == PARITY_SLICE["band"])
        & (df["clock"] == "H1")
        & (df["policy"] == "P-NONE")
    )
    return df.loc[m].copy()


def build_parity_report(per_symbol_posts: dict[str, list[dict]]) -> dict:
    """Compare only symbols we actually ran (and that have a parent row)."""
    parent = load_parent_expectancy()
    by_sym = {r.symbol: r for _, r in parent.iterrows()}
    rows = []
    for sym in sorted(per_symbol_posts.keys()):
        if sym not in by_sym:
            continue
        rows.append(compare_symbol(sym, per_symbol_posts.get(sym, []), by_sym.get(sym)))
    n_cmp = sum(1 for r in rows if r["status"] in ("OK", "FAIL"))
    n_ok = sum(1 for r in rows if r.get("reproduced"))
    max_diff = 0.0
    for r in rows:
        for c in (r.get("checks") or {}).values():
            d = c.get("abs_diff")
            if d is not None and np.isfinite(d):
                max_diff = max(max_diff, float(d))
    return {
        "parent": "SPDR-014",
        "slice": PARITY_SLICE,
        "policy": "P-NONE",
        "quantities": ["mean_r_h", "p_momo", "p_mr", "n_decided"],
        "tolerance": PARITY_TOL,
        "n_compared": n_cmp,
        "n_reproduced": n_ok,
        "max_abs_diff": max_diff,
        "hard_pass": bool(n_cmp > 0 and n_ok == n_cmp and max_diff <= PARITY_TOL),
        "rows": rows,
    }
