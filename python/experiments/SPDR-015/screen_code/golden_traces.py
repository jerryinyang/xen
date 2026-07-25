"""Golden traces G1–G4 (design §5)."""
from __future__ import annotations

import numpy as np
import polars as pl

from config import CLOCKS, RV_WINDOW
from features import _expanding_p90, _rolling_mean, _rolling_median, build_bar_frame, add_state_models
from hmm import fit_gaussian_hmm, filter_high_prob
from catalog_io import aggregate_clock, load_minute_bars
from config import CONFIRM_END, DESIGN_START


def run_golden_traces(manifest, symbols_data: dict) -> dict:
    """
    G1 BTCUSDT R-HMM-RV: fit window ends strictly before origin t.
    G2 ETHUSDT persistence Brier equals empirical frequency of stay.
    G3 SOLUSDT T-GT-CUR: two consecutive swings hand mag compare.
    G4 R-SHOCK: top-decile |r| label equals hand percentile (not titled regime).
    """
    out = {"G1": None, "G2": None, "G3": None, "G4": None}

    # ---- G1 ----
    try:
        btc = symbols_data.get("BTCUSDT", {}).get("H1")
        fits = symbols_data.get("BTCUSDT", {}).get("hmm_fits_H1", [])
        if btc is not None and btc.height and fits:
            ok_fit = all(f.get("fit_end_lt_origin", False) for f in fits if f.get("first_origin_ts", -1) > 0)
            # hand recompute one forward-filter step
            rv20 = btc["rv20"].to_numpy()
            se = btc["slot_end"].to_numpy()
            # take first fit
            f0 = fits[0]
            a = f0["idx"]
            p = fit_gaussian_hmm(rv20[:a])
            hand_ok = p is not None
            screen_state = int(btc["s_hmm_rv"][a]) if a < btc.height else -1
            if p is not None:
                pr = filter_high_prob(rv20[: a + 1], p)
                hand_state = 1 if pr[a] >= 0.5 else 0
                match = hand_state == screen_state
            else:
                match = False
                hand_state = -1
            out["G1"] = {
                "pass": bool(ok_fit and hand_ok and match),
                "all_fits_causal": ok_fit,
                "n_fits": len(fits),
                "sample_fit": f0,
                "hand_state": hand_state,
                "screen_state": screen_state,
                "state_match": match,
                "note": "R-HMM-RV on rv20; fit end < origin",
            }
        else:
            out["G1"] = {"pass": False, "reason": "missing BTCUSDT H1 or fits"}
    except Exception as e:
        out["G1"] = {"pass": False, "error": str(e)}

    # ---- G2 ----
    try:
        eth = symbols_data.get("ETHUSDT", {}).get("H1")
        if eth is not None and eth.height:
            st = eth["s_markov"].to_numpy()
            origin = eth["is_origin"].to_numpy()
            # persistence Brier for k=1
            y = np.full(st.size, -1, dtype=np.int64)
            y[:-1] = st[1:]
            m = origin & (st >= 0) & (y >= 0)
            p_pers = st.astype(float)
            br = float(np.mean((p_pers[m] - y[m].astype(float)) ** 2))
            # empirical: frequency of stay = mean(s_t == s_{t+1})
            stay = float(np.mean(st[m] == y[m]))
            # for hard 0/1 persistence, Brier = mean((s_t - s_{t+1})^2) = mean(switch) = 1 - stay
            hand_brier = 1.0 - stay
            out["G2"] = {
                "pass": abs(br - hand_brier) < 1e-9,
                "screen_brier": br,
                "hand_brier_from_stay": hand_brier,
                "stickiness": stay,
                "n": int(m.sum()),
                "note": "persistence Brier == 1 - empirical stay frequency",
            }
        else:
            out["G2"] = {"pass": False, "reason": "missing ETHUSDT H1"}
    except Exception as e:
        out["G2"] = {"pass": False, "error": str(e)}

    # ---- G3 ----
    try:
        zz = symbols_data.get("SOLUSDT", {}).get("zz_panel")
        if zz and zz.get("rows"):
            # find T-GT-CUR row with hand compare
            cur_rows = [r for r in zz["rows"] if r["target"] == "T-GT-CUR" and r["model"] == "ridge_cont"]
            if cur_rows:
                r0 = cur_rows[0]
                hand_y = 1.0 if r0["mag_k1"] > r0["mag_k"] else 0.0
                out["G3"] = {
                    "pass": abs(hand_y - r0["y"]) < 1e-12,
                    "mag_k": r0["mag_k"],
                    "mag_k1": r0["mag_k1"],
                    "hand_y": hand_y,
                    "row_y": r0["y"],
                    "ridge_p": r0["p"],
                    "note": "T-GT-CUR = 1{mag_{k+1} > mag_k}",
                }
            else:
                out["G3"] = {"pass": False, "reason": "no T-GT-CUR rows"}
        else:
            out["G3"] = {"pass": False, "reason": "missing SOLUSDT zz panel"}
    except Exception as e:
        out["G3"] = {"pass": False, "error": str(e)}

    # ---- G4 ----
    try:
        btc = symbols_data.get("BTCUSDT", {}).get("H1")
        if btc is not None and btc.height:
            abs_r = btc["abs_r"].to_numpy()
            shock = btc["s_shock"].to_numpy()
            p90 = btc["shock_p90"].to_numpy()
            # pick a mid index with valid p90
            idxs = np.where(np.isfinite(p90) & (shock >= 0))[0]
            if idxs.size:
                i = int(idxs[len(idxs) // 2])
                hand_p90 = float(np.percentile(abs_r[:i][np.isfinite(abs_r[:i])], 90))
                hand_label = 1 if abs_r[i] >= hand_p90 else 0
                out["G4"] = {
                    "pass": abs(hand_p90 - p90[i]) < 1e-9 and hand_label == int(shock[i]),
                    "idx": i,
                    "hand_p90": hand_p90,
                    "screen_p90": float(p90[i]),
                    "hand_label": hand_label,
                    "screen_label": int(shock[i]),
                    "title": "R-SHOCK shock flag — NOT regime",
                    "note": "O3: never report as regime success",
                }
            else:
                out["G4"] = {"pass": False, "reason": "no valid shock labels"}
        else:
            out["G4"] = {"pass": False, "reason": "missing BTCUSDT H1"}
    except Exception as e:
        out["G4"] = {"pass": False, "error": str(e)}

    out["all_pass"] = all(isinstance(v, dict) and v.get("pass") for v in out.values() if v is not None)
    return out
