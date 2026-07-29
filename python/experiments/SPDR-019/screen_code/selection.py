"""L-51 three-number selection check (design §12, chapter-06-governance §1b)."""
from __future__ import annotations

import numpy as np


def l51_three_number(selected_r: np.ndarray, excluded_r: np.ndarray) -> dict:
    """Payoff-scale ratio, sign-share differential, mean-vs-median gap in excluded set."""
    sel = np.asarray(selected_r, dtype=float)
    exc = np.asarray(excluded_r, dtype=float)
    sel = sel[np.isfinite(sel)]
    exc = exc[np.isfinite(exc)]
    out = {
        "n_selected": int(sel.size),
        "n_excluded": int(exc.size),
        "payoff_scale_ratio": float("nan"),
        "sign_share_differential": float("nan"),
        "excluded_mean_vs_median_gap": float("nan"),
    }
    if sel.size == 0 or exc.size == 0:
        return out
    # payoff-scale ratio: median(|sel|) / median(|exc|)
    ms = float(np.median(np.abs(sel)))
    me = float(np.median(np.abs(exc)))
    out["payoff_scale_ratio"] = ms / me if me > 0 else float("nan")
    # sign-share: P(r>0) selected - P(r>0) excluded (on non-flat)
    def pos_share(x):
        s = x[x != 0]
        return float(np.mean(s > 0)) if s.size else float("nan")
    out["sign_share_differential"] = pos_share(sel) - pos_share(exc)
    # mean-vs-median gap in excluded
    out["excluded_mean_vs_median_gap"] = float(np.mean(exc) - np.median(exc))
    return out


def run_selection_checks(cells: dict[str, dict]) -> dict:
    """Run L-51 on every selected subset reported separately.

    ``cells`` maps name -> {"selected_r": ndarray, "excluded_r": ndarray}.
    """
    rows = {}
    for name, pack in cells.items():
        rows[name] = l51_three_number(pack["selected_r"], pack["excluded_r"])
    return {
        "n_checks": len(rows),
        "subsets": rows,
        "note": (
            "L-51 on every selected subset the design reports separately: "
            "L1 d>=5/7/9, L2 state cells, L3 gates, cells above vs below median mde50"
        ),
    }
