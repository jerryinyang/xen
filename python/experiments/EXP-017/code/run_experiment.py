"""
EXP-017 — CF-MR-005/HYP-002 episode-native mechanism probe: orchestration (ANALYSIS-ONLY).

Sources: EXP-014c e3/e2 + EXP-014b e0 extend/z15 emissions (read-only; all end at the EXP-013
49% TRAIN fence — EXP-016 emissions are NOT loaded: their TRAIN band duplicates EXP-014c's
trades and their TEST band is already-read TEST data; deviation documented in report).
Frozen 5 labels per stratum; no frozen-referee calls (L-17).
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from tqdm.auto import tqdm

import lib

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("EXP-017")

RESULTS = lib.ROOT / "python" / "experiments" / "EXP-017" / "results"
PLOTS = lib.ROOT / "python" / "experiments" / "EXP-017" / "plots"


# --------------------------------------------------------------------------- #
# Per-stratum pass
# --------------------------------------------------------------------------- #
def run_stratum(etag: str, inst: str) -> dict | None:
    try:
        cell = lib.lib14c.load_cell(etag, "extend", inst, ztag="z15")
    except FileNotFoundError:
        return None
    cost = lib.lib14c.cost_for(inst)
    lib.lib14c.validate_provenance(cell.positions, inst)
    eps_all = lib.build_episodes(cell, cost)
    eps = lib.completed(eps_all)
    powered = len(eps) >= lib.MIN_EPISODES
    open_ = cell.positions.sort("SourceCloseTime").get_column("RealOpen").to_numpy().astype(float)
    res = {"etag": etag, "instrument": inst, "n_episodes": len(eps),
           "n_censored": len(eps_all) - len(eps), "powered": powered,
           "m2": lib.m2_increment(eps), "m2_addbar_null": lib.m2_addbar_null(eps, open_, cost),
           "m3": lib.m3_predictability(eps), "m1": lib.m1_anatomy(eps),
           "m4": lib.m4_tail(eps)}
    m2 = res["m2"]
    m3_sig = [f for f, v in res["m3"].items() if v.get("holm_significant")]
    if not powered:
        label = "UNPOWERED"
    else:
        inc_pos = m2["median_ci"][0] > 0 and m2["mean_ci"][0] > 0
        inc_null = m2["median_ci"][0] <= 0 <= m2["median_ci"][1] or m2["mean_ci"][1] < 0 \
            or m2["mean_ci"][0] <= 0
        if inc_pos and m3_sig:
            label = "MECHANISM_STATED"
        elif inc_pos:
            label = "STRUCTURE_ONLY"
        elif not inc_pos:
            label = "EXPOSURE_LIKE"      # increment not established over passive
        else:
            label = "MIXED"
    res["m3_significant_features"] = m3_sig
    res["label"] = label
    return res


# --------------------------------------------------------------------------- #
# Plots
# --------------------------------------------------------------------------- #
def plot_all(primary: list[dict]) -> None:
    import seaborn as sns
    sns.set_theme(style="whitegrid")
    # increment distribution summary
    fig, ax = plt.subplots(figsize=(9, 4.5))
    x = np.arange(len(primary))
    ax.errorbar(x, [r["m2"]["median"] for r in primary],
                yerr=[[r["m2"]["median"] - r["m2"]["median_ci"][0] for r in primary],
                      [r["m2"]["median_ci"][1] - r["m2"]["median"] for r in primary]],
                fmt="o", capsize=4, label="median Δ (ladder − passive)")
    nb = [r["m2_addbar_null"]["null_band"] for r in primary]
    ax.fill_between(x, [b[0] for b in nb], [b[1] for b in nb], alpha=0.3,
                    color="grey", label="add-bar-randomized null band")
    ax.axhline(0, color="red", ls="--", lw=1)
    ax.set_xticks(x); ax.set_xticklabels([r["instrument"] for r in primary])
    ax.set_ylabel("bps/episode"); ax.set_title("EXP-017 M2: structure increment (e3/extend/z15)")
    ax.legend(); fig.tight_layout()
    fig.savefig(PLOTS / "m2_increment.png", dpi=150); plt.close(fig)

    fig, axes = plt.subplots(1, len(primary), figsize=(4.5 * len(primary), 4), sharey=True)
    for ax, r in zip(np.atleast_1d(axes), primary):
        feats = [f for f in lib.FEATURES if "rho" in r["m3"].get(f, {})
                 and np.isfinite(r["m3"][f].get("rho", np.nan))]
        rho = [r["m3"][f]["rho"] for f in feats]
        lo = [r["m3"][f]["null_band"][0] for f in feats]
        hi = [r["m3"][f]["null_band"][1] for f in feats]
        xx = np.arange(len(feats))
        ax.fill_between(xx, lo, hi, alpha=0.25, color="grey", label="perm null 95%")
        ax.plot(xx, rho, "o", color="#c63")
        ax.set_xticks(xx); ax.set_xticklabels(feats, rotation=45, fontsize=7)
        ax.set_title(r["instrument"]); ax.axhline(0, color="k", lw=0.6)
    np.atleast_1d(axes)[0].set_ylabel("Spearman ρ (episode net)")
    fig.suptitle("EXP-017 M3: start-feature predictability vs permutation null")
    fig.tight_layout(); fig.savefig(PLOTS / "m3_predictability.png", dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4))
    for r in primary:
        yrs = sorted(r["m4"]["per_year_bps"])
        ax.plot(yrs, [r["m4"]["per_year_bps"][y] for y in yrs], marker="o",
                label=r["instrument"])
    ax.axhline(0, color="red", ls="--", lw=1); ax.legend()
    ax.set_title("EXP-017 M4: episode net per year (e3/extend/z15)")
    fig.tight_layout(); fig.savefig(PLOTS / "m4_per_year.png", dpi=150); plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    PLOTS.mkdir(parents=True, exist_ok=True)
    strata: list[dict] = []
    jobs = [("e3", i) for i in lib.ALL_CELLS] + \
           [(e, i) for e in ("e2", "e0") for i in lib.PRIMARY_CELLS]
    for etag, inst in tqdm(jobs, desc="strata"):
        r = run_stratum(etag, inst)
        if r is None:
            logger.warning("NO_DATA %s/%s", etag, inst)
            continue
        strata.append(r)
        logger.info("[%s/extend/z15] %-7s n_epi=%3d pow=%s M2 med=%7.1f [%7.1f,%7.1f] "
                    "sig=%s => %s", etag, inst, r["n_episodes"], r["powered"],
                    r["m2"]["median"], *r["m2"]["median_ci"],
                    r["m3_significant_features"], r["label"])

    primary = [r for r in strata if r["etag"] == "e3" and r["instrument"] in lib.PRIMARY_CELLS]
    powered_primary = [r for r in primary if r["powered"]]
    labels = [r["label"] for r in powered_primary]
    if len(powered_primary) < 2:
        family = "UNPOWERED"
    elif sum(lb == "MECHANISM_STATED" for lb in labels) >= 2:
        family = "MECHANISM_STATED"
    elif sum(lb in ("MECHANISM_STATED", "STRUCTURE_ONLY") for lb in labels) >= 2:
        family = "STRUCTURE_ONLY"
    elif sum(lb == "EXPOSURE_LIKE" for lb in labels) >= 2:
        family = "EXPOSURE_VERDICT"
    else:
        family = "MIXED"
    out = {"experiment": "EXP-017", "family": "CF-MR-005", "hypothesis": "HYP-002",
           "primary": [f"e3:{c}" for c in lib.PRIMARY_CELLS], "family_read": family,
           "strata": strata,
           "seeds": {"boot": lib.SEED_BOOT, "perm": lib.SEED_PERM},
           "params": {"block_episodes": lib.BLOCK_EPISODES, "min_episodes": lib.MIN_EPISODES,
                      "n_boot": lib.N_BOOT, "n_perm": lib.N_PERM}}
    (RESULTS / "episode_mechanism.json").write_text(json.dumps(out, indent=2, default=str))
    plot_all(primary)
    logger.info("FAMILY READ: %s -> results/episode_mechanism.json", family)


if __name__ == "__main__":
    main()
