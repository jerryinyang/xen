"""EXP-008 vehicle diagnostic — is the availability/MFE-Delta stack masking a reversion edge?

Operator-requested falsification (2026-07-01): the claim "the fixed-horizon MFE-toward-anchor metric +
regime-matched-random control masks a real mean-reversion edge" is a HYPOTHESIS, not established. Test it
before redesigning. Analysis-only, TRAIN-only, 0 reads, holdout sealed.

For each (instrument, anchor-series, domain-pair) cell, on the conditioned events (screen-pass and
|z|>=2) vs two controls, compute three read metrics and their conditioned-minus-control Delta:

  * MFE_toward   — the current metric: ATR-normalized max favourable excursion toward the anchor over H.
  * frac_recov   — fraction of the entry dislocation recovered toward the anchor within H (deviation
                   series): s*(d0 - m_toward)/|d0|, where m_toward is the most-toward-zero deviation.
  * anchor_hit   — did the deviation cross zero (price reach the anchor) within H (0/1).

Two controls:
  * C1 REGIME  — current null: regime-matched random timing (any |z|).
  * C2 DISLOC  — dislocation-matched null: random timing among |z|>=2 bars (same dislocation band, no
                 screen). Answers the strategy-native question "among equally-dislocated bars, does the
                 MR-screen identify better reversion?"

Decision rule (predeclared): if a native metric (frac_recov / anchor_hit) shows conditioned > control
(aggregate Delta CI excludes 0) under C2 while MFE_toward-Delta does not, the evaluation vehicle is
masking the effect. If all three agree (all ~0 or all separate), no masking — the EXONERATE stands on
the metric choice. Writes results/vehicle_diagnostic.json + plots/V_vehicle_diagnostic.png.
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from tqdm.auto import tqdm

from xen import cross_domain_mr as cdm
from xen import vol_regime as vr

sys.path.insert(0, str(Path(__file__).parent))
import run_experiment as R  # noqa: E402

logger = logging.getLogger("EXP-008.vehicle_diagnostic")

SEED = 20260701
H = R.H_EXCURSION
SERIES = ("S1_CENTER", "S4_OU", "S5_SPREAD")     # incl. the OU-native + the Holm-flagged S5
N_BOOT_AGG = 5000


def event_and_control_idx(ed: R.ExecDomain, dev: np.ndarray, z: np.ndarray, theta: np.ndarray,
                          rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Conditioned events, C1 regime-matched control, C2 dislocation-matched (|z|>=2) control."""
    events = R.detect_events(ed, dev, z, theta)
    z_lag = np.concatenate([[np.nan], z[:-1]])
    extreme = np.flatnonzero(np.isfinite(z_lag) & (np.abs(z_lag) >= cdm.Z_STAR) & np.isfinite(theta))
    counts = R._regime_counts(ed.regime_lag, events) if events.shape[0] else {}
    n = sum(counts.values())
    if n < R.N_MIN:
        return events, np.empty(0, np.int64), np.empty(0, np.int64)
    c1 = R.matched_random_idx(ed.regime_lag, counts, n, rng)
    # C2 — dislocation-matched: same regime composition but drawn only from |z|>=2 bars.
    reg_ext = ed.regime_lag.copy()
    mask = np.ones(reg_ext.shape[0], bool)
    mask[extreme] = False
    reg_ext[mask] = vr.REGIME_UNDEFINED                      # restrict candidate pool to extreme bars
    c2 = R.matched_random_idx(reg_ext, counts, n, rng)
    return events[np.isin(ed.regime_lag[events], list(counts))], c1, c2


def native_metrics(ed: R.ExecDomain, dev: np.ndarray, theta: np.ndarray, idx: np.ndarray
                   ) -> dict[str, float]:
    """MFE_toward, fraction-recovered, anchor-hit over a set of entry bars (deviation-series based)."""
    if idx.shape[0] == 0:
        return {"mfe": np.nan, "frac": np.nan, "hit": np.nan, "n": 0}
    fmin, _ = R._window_extremes(dev, H, forward=True)        # min deviation over [i..i+H-1]
    _, fmax = R._window_extremes(dev, H, forward=True)        # max deviation
    d0 = np.concatenate([[np.nan], dev[:-1]])                 # entry dislocation dev[i-1]
    s = np.sign(d0)
    m_toward = np.where(s > 0, fmin, fmax)                    # most-toward-zero deviation reached
    with np.errstate(invalid="ignore", divide="ignore"):
        frac = s * (d0 - m_toward) / np.abs(d0)              # 1.0 == reached anchor; >1 overshoot
    hit = np.where(s > 0, fmin <= 0.0, fmax >= 0.0).astype(float)
    good = idx[np.isfinite(theta[idx]) & np.isfinite(frac[idx])]
    if good.shape[0] == 0:
        return {"mfe": np.nan, "frac": np.nan, "hit": np.nan, "n": 0}
    return {"mfe": float(np.median(theta[good])), "frac": float(np.median(frac[good])),
            "hit": float(np.mean(hit[good])), "n": int(good.shape[0])}


def agg_delta_ci(deltas: np.ndarray, rng: np.random.Generator) -> tuple[float, float, float]:
    """Median Delta across cells + 90% bootstrap CI (cell-level resample)."""
    d = deltas[np.isfinite(deltas)]
    if d.shape[0] < 3:
        return float("nan"), float("nan"), float("nan")
    boot = np.array([np.median(rng.choice(d, d.shape[0], replace=True)) for _ in range(N_BOOT_AGG)])
    return float(np.median(d)), float(np.quantile(boot, 0.05)), float(np.quantile(boot, 0.95))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    rng = np.random.default_rng(SEED)
    insts = R.ALL_INSTRUMENTS
    train = {s: R.load_train_1m(s) for s in tqdm(insts, desc="load 1m TRAIN")}
    exec_mins = sorted({e for (_, e) in cdm.DOMAIN_PAIRS.values()})
    baskets = {e: R.build_baskets(train, e, insts) for e in exec_mins}

    rows: list[dict] = []
    for series in tqdm(SERIES, desc="series"):
        for pair, (a_min, e_min) in cdm.DOMAIN_PAIRS.items():
            for sym in insts:
                ed = R.build_exec_domain(train[sym], e_min)
                anc = R.anchor_arrays(train[sym], a_min)
                basket = baskets[e_min][sym] if series == "S5_SPREAD" else None
                asr = cdm.anchor_series(series, ed.close, ed.ct, anc, basket)
                if not np.any(np.isfinite(asr.dev)):
                    continue
                theta = R.excursion_series(ed, asr.dev)
                ev, c1, c2 = event_and_control_idx(ed, asr.dev, asr.z, theta, rng)
                if ev.shape[0] < R.N_MIN or c1.shape[0] == 0 or c2.shape[0] == 0:
                    continue
                mc = native_metrics(ed, asr.dev, theta, ev)
                m1 = native_metrics(ed, asr.dev, theta, c1)
                m2 = native_metrics(ed, asr.dev, theta, c2)
                rows.append({"axis": f"{series}|{pair}", "instrument": sym, "n_events": mc["n"],
                             "mfe_d_C1": mc["mfe"] - m1["mfe"], "mfe_d_C2": mc["mfe"] - m2["mfe"],
                             "frac_d_C1": mc["frac"] - m1["frac"], "frac_d_C2": mc["frac"] - m2["frac"],
                             "hit_d_C1": mc["hit"] - m1["hit"], "hit_d_C2": mc["hit"] - m2["hit"],
                             "frac_cond": mc["frac"], "hit_cond": mc["hit"], "mfe_cond": mc["mfe"]})

    R.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    R.PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    agg = {}
    for key in ("mfe_d_C1", "mfe_d_C2", "frac_d_C1", "frac_d_C2", "hit_d_C1", "hit_d_C2"):
        arr = np.array([r[key] for r in rows], float)
        med, lo, hi = agg_delta_ci(arr, rng)
        agg[key] = {"median_delta": round(med, 4), "ci90": [round(lo, 4), round(hi, 4)],
                    "frac_cells_pos": round(float(np.mean(arr[np.isfinite(arr)] > 0)), 3),
                    "n_cells": int(np.isfinite(arr).sum())}

    def sep(k: str) -> bool:
        return np.isfinite(agg[k]["ci90"][0]) and agg[k]["ci90"][0] > 0

    verdict = {
        "masking_demonstrated": bool((sep("frac_d_C2") or sep("hit_d_C2")) and not sep("mfe_d_C2")),
        "note": ("MASKING if a native metric (frac/hit) separates under the dislocation-matched control "
                 "C2 while MFE-Delta does not. If none separate, no masking -> EXONERATE stands on the "
                 "metric. If MFE also separates, the current vehicle was not blind."),
    }
    out = {"aggregate": agg, "verdict": verdict, "n_cells": len(rows),
           "controls": {"C1": "regime-matched random timing (current)",
                        "C2": "dislocation-matched (|z|>=2, regime-matched, no screen)"}}
    (R.RESULTS_DIR / "vehicle_diagnostic.json").write_text(json.dumps(out, indent=2))

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(1, 2, figsize=(13, 5))
    for j, ctrl in enumerate(("C1", "C2")):
        keys = [f"mfe_d_{ctrl}", f"frac_d_{ctrl}", f"hit_d_{ctrl}"]
        meds = [agg[k]["median_delta"] for k in keys]
        los = [agg[k]["median_delta"] - agg[k]["ci90"][0] for k in keys]
        his = [agg[k]["ci90"][1] - agg[k]["median_delta"] for k in keys]
        ax[j].bar(["MFE", "frac_recov", "anchor_hit"], meds, yerr=[los, his], capsize=6,
                  color=["steelblue", "seagreen", "darkorange"])
        ax[j].axhline(0, color="k", lw=0.8)
        ax[j].set_title(f"Delta (cond - control) — {ctrl}={out['controls'][ctrl].split('(')[0]}")
        ax[j].set_ylabel("median cell Delta (90% CI)")
    fig.suptitle("EXP-008 vehicle diagnostic: does a native reversion metric separate where MFE does not?")
    fig.tight_layout()
    fig.savefig(R.PLOTS_DIR / "V_vehicle_diagnostic.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    logger.info("masking_demonstrated=%s | cells=%d", verdict["masking_demonstrated"], len(rows))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
