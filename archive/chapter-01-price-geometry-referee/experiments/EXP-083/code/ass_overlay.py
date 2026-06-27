"""EXP-083 — NON-BINDING `ASS` discovery overlay across ALL strata (G-017 `DISCOVERY_ONLY`).

Disclosure-only addendum to the EXP-083 TRAIN-only candidate screen. It re-resolves **every** member
``{substrate × instrument × domain × candidate}`` row that formed a candidate (n_resolved ≥ 30) — the full
screen population, not just the survivors — using the **exact same frozen machinery the screen used**
(imported from ``run_experiment.py``), then scores each stratum's post-exit real-price ATR-return
distribution with the **real `ASS` transform**: adaptive-KDE + **empirical-Bayes shrinkage** toward a
cross-cell pooled prior + the D2.5 tail/bimodality diagnostic.

The point of `ASS` is the shrinkage: it produces a **shrunk per-stratum estimate** (the quantity a *binding*
`ASS` would hand the referee), pulling small-n strata toward the pool. This overlay shows that shrunk
estimate beside the raw screen statistic across all strata, so the raw-vs-`ASS` delta — where the demoted
qualifier would **disagree** with the screen — is visible. The shrinkage pool is **cross-cell within
``{substrate, candidate}``** (operator decision): each cell's estimate for an exit shrinks toward that
exit's cross-cell typical within its substrate, with ``k = median-n`` across the pool (the EXP-076 deployed
convention).

NON-BINDING (G-017): no screen decision reads `ASS`; the frozen referee suite (G-018a screen + separability
gate) is the binding gate. `ASS` shrinkage POOLS across strata, which is exactly the per-stratum-discipline
tension (LESSON-001) that demoted it — so these shrunk estimates are discovery, never a binding per-stratum
verdict. This script reads the frozen ``screen_results.parquet``/``valid_candidate_set.json`` and **does not
touch or regenerate** any binding artifact; it emits only the ``ass_overlay.*`` disclosure files. TRAIN-only,
holdout sealed, 0 counted reads. A per-row reconciliation guard asserts each re-resolved array reproduces the
screen (n_resolved exact, raw mean within 1e-9).

Run:
    cd python && python experiments/EXP-083/code/ass_overlay.py
"""
from __future__ import annotations

import importlib.util
import json
import logging
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                       # noqa: E402
import polars as pl                      # noqa: E402
import seaborn as sns                    # noqa: E402
from tqdm.auto import tqdm               # noqa: E402

import xen.ass as ass                    # noqa: E402  (validated qualifier; non-binding overlay)
from xen.ass import DIP_ALPHA, TAU_GAP   # noqa: E402

LOGGER = logging.getLogger("EXP-083-ass-overlay")

# --------------------------------------------------------------------------- #
# Path setup + reuse of the frozen screen orchestration
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-083"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
EXPERIMENT_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
CODE_DIR = EXPERIMENT_DIR / "code"
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
_RUN_EXPERIMENT = CODE_DIR / "run_experiment.py"
_SCREEN_RESULTS = RESULTS_DIR / "screen_results.parquet"

EVENT_FLOOR = 30                      # form a candidate / score only when n_resolved >= 30
RECON_TOL = 1e-9                      # raw-mean reconciliation tolerance vs the screen
GUARD_I_N = 60                        # §D6 Guard (i): defer expectancy to median at effective-n ≤ 60
GUARD_II_THRESHOLD = 2.0            # §D6 Guard (ii): P(>2R) span used for the slope-inapplicable flag
GUARD_II_PGT_FLOOR = 0.05          # compressed predicted P(>2R) -> reliability slope inapplicable


def _load_run_experiment():
    """Import the frozen screen orchestration as a module (import-safe: main() is guarded)."""
    spec = importlib.util.spec_from_file_location("exp083_run_experiment", _RUN_EXPERIMENT)
    if spec is None or spec.loader is None:                       # pragma: no cover - defensive
        raise ImportError(f"Could not load run_experiment from {_RUN_EXPERIMENT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------- #
# Pure computation — re-resolve one cell's per-stratum return arrays (reuses rx.*)
# --------------------------------------------------------------------------- #
def resolve_cell_returns(rx, train_frame: pl.DataFrame, instrument: str, period: int,
                         cell_index: int, summary: pl.DataFrame) -> dict:
    """Re-resolve every ``{substrate, candidate}`` post-exit ATR-return array for one cell.

    Mirrors the screen's per-cell assembly (``run_experiment.process_cell``) but returns the resolved
    candidate return arrays instead of the gate verdicts, reusing every frozen building block from ``rx``
    so the distributions are byte-identical to the screen's. The matched-random *gate control* is not
    needed here (`ASS` scores each stratum's own distribution).

    Returns ``{(substrate, candidate): candidate_returns}`` (finite ATR returns).
    """
    domain = rx.DOMAIN_LABEL[period]
    bars = rx.build_domain_bars(train_frame, period)
    ohlc = rx._real_ohlc(bars)
    if "TickVolume" in bars.columns:
        ohlc["volume"] = bars.get_column("TickVolume").to_numpy().astype(np.float64)
    atr = rx.wilder_atr(ohlc["high"], ohlc["low"], ohlc["close"], rx.ATR_PERIOD)
    es = rx.make_entrysets(bars, instrument, domain, cell_index)

    out: dict[tuple[str, str], np.ndarray] = {}
    for sub in rx.SUBSTRATE_ORDER:
        srow = summary.filter((pl.col("instrument") == instrument) & (pl.col("domain") == domain)
                              & (pl.col("substrate") == rx._SUMMARY_SUBSTRATE[sub]))
        if srow.height == 0:
            continue
        stats = rx._cell_stats_from_summary(srow.row(0, named=True))
        pin = rx._path_inputs(bars, instrument, domain, sub, es[sub], ohlc, atr)
        atr_med = float(np.median(pin.atr_entry)) if pin.atr_entry.size else float("nan")
        cand_map = rx.build_candidates(pin, stats, atr_med)
        for cid, (cand_full, _nostop) in cand_map.items():
            out[(sub, cid)] = cand_full.ret[cand_full.resolved]
    return out


def ass_row(x: np.ndarray, pool: np.ndarray, k_shrink: float) -> dict:
    """Non-binding `ASS` read of one stratum: un-pooled + shrunk (EB) estimates + D2.5 shape diagnostic."""
    unp = ass.score(x, shrink=False)
    shr = ass.score(x, shrink=True, pool=pool, k_shrink=k_shrink)
    shp = ass.shape_diagnostic(x)                       # raw-sample tail/bimodality (deterministic)
    return {
        "ass_exp_unpooled": unp.expectancy_direct, "ass_med_unpooled": unp.median,
        "ass_exp_shrunk": shr.expectancy_direct, "ass_med_shrunk": shr.median,
        "shrink_weight": shr.weight, "k_shrink": float(k_shrink),
        "ass_tail": shp.gap, "ass_dip_p": shp.dip_p, "ass_shape_flag": bool(shp.flag),
        "p_gt_2r": float(shr.p_gt.get(GUARD_II_THRESHOLD, float("nan"))),
    }


# --------------------------------------------------------------------------- #
# Plotting (bounded; from the overlay table only)
# --------------------------------------------------------------------------- #
def _status(valid: bool, s2_def: bool) -> str:
    if valid and not s2_def:
        return "valid-S2pass"
    if valid and s2_def:
        return "valid-S2deferred"
    return "fail"


def plot_ass_overlay(df: pl.DataFrame, path: Path) -> None:
    """Plot 6 — ASS-shrunk vs raw screen expectancy across all strata + sign-disagreement summary."""
    sns.set_theme(style="whitegrid")
    colours = {"valid-S2pass": "tab:green", "valid-S2deferred": "tab:orange", "fail": "lightgrey"}
    pdf = df.with_columns(
        pl.struct(["valid", "s2_deferred"]).map_elements(
            lambda s: _status(s["valid"], s["s2_deferred"]), return_dtype=pl.Utf8).alias("status")
    ).to_pandas()

    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(15, 6.5))
    # Panel A — ASS-shrunk vs raw screen expectancy (shrinkage pull); y=x is "ASS agrees with screen".
    for st in ["fail", "valid-S2deferred", "valid-S2pass"]:
        d = pdf[pdf["status"] == st]
        ax0.scatter(d["gross_exp"], d["ass_exp_shrunk"], s=8 + np.sqrt(d["n_resolved"]),
                    c=colours[st], alpha=0.45 if st == "fail" else 0.85, edgecolors="none",
                    label=f"{st} (n={len(d)})", zorder=2 if st == "fail" else 3)
    lim = [min(pdf["gross_exp"].min(), pdf["ass_exp_shrunk"].min()) - 0.1,
           max(pdf["gross_exp"].max(), pdf["ass_exp_shrunk"].max()) + 0.1]
    ax0.plot(lim, lim, color="black", ls="--", lw=1, label="y = x (ASS = screen)")
    ax0.axhline(0, color="grey", ls=":", lw=0.8)
    ax0.axvline(0, color="grey", ls=":", lw=0.8)
    ax0.set_xlim(lim)
    ax0.set_ylim(lim)
    ax0.set_xlabel("raw screen expectancy (ATR)")
    ax0.set_ylabel("ASS-shrunk expectancy (ATR)")
    ax0.set_title("Panel A: ASS empirical-Bayes shrinkage vs the raw screen\n"
                  "(point size ~ sqrt(n); pool = cross-cell within {substrate,candidate})")
    ax0.legend(fontsize=7, loc="upper left")
    # Panel B — where ASS would flip the expectancy sign vs the raw screen, by status.
    flip = pdf[np.sign(pdf["ass_exp_shrunk"]) != np.sign(pdf["gross_exp"])]
    order = ["valid-S2pass", "valid-S2deferred", "fail"]
    counts = [int((flip["status"] == st).sum()) for st in order]
    totals = [int((pdf["status"] == st).sum()) for st in order]
    ax1.bar(order, counts, color=[colours[s] for s in order], edgecolor="black")
    for i, (c, t) in enumerate(zip(counts, totals)):
        ax1.text(i, c, f"{c}/{t}", ha="center", va="bottom", fontsize=9)
    ax1.set_ylabel("strata where ASS-shrunk flips the expectancy SIGN vs screen")
    ax1.set_title(f"Panel B: ASS-vs-screen sign disagreements (NON-BINDING)\n"
                  f"shape-flagged strata: {int(pdf['ass_shape_flag'].sum())}/{len(pdf)}")
    plt.setp(ax1.get_xticklabels(), rotation=15)
    fig.suptitle("EXP-083 ASS discovery overlay (NON-BINDING, G-017 DISCOVERY_ONLY) — all member strata",
                 fontsize=12, y=1.02)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def _screen_lookup() -> dict:
    """{(sub,inst,dom,cand): (n_resolved, gross_exp, gross_med, valid, s2_deferred, g018a, fail_leg)}."""
    sr = pl.read_parquet(_SCREEN_RESULTS)
    out = {}
    for r in sr.iter_rows(named=True):
        out[(r["substrate"], r["instrument"], r["domain"], r["candidate"])] = (
            int(r["n_resolved"]), float(r["gross_exp"]), float(r["gross_med"]),
            bool(r["valid"]), bool(r["s2_deferred"]), bool(r["g018a_pass"]), str(r["fail_leg"]))
    return out


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGGER.info("EXP-083 ASS discovery overlay (NON-BINDING) — all member strata")

    rx = _load_run_experiment()
    screen = _screen_lookup()

    # Rebuild the exact member grid + loaded instruments so cell_index/seeds match the screen.
    val005 = rx._load_val005()
    found, _missing = val005.discover_infr003_files()
    members = rx._member_set()
    summary = pl.read_parquet(rx._EXP081_SUMMARY)
    instruments = [s for s in val005.TARGET_SYMBOLS if s in found]
    loaded: dict[str, object] = {}
    for inst in instruments:
        li, _seal, _status = val005.load_first70(found[inst])
        if li is not None:
            loaded[inst] = li
    instruments = [s for s in instruments if s in loaded]
    full_grid = [(inst, p) for inst in instruments for p in val005.DOMAINS]
    member_grid = [(ci, inst, p) for ci, (inst, p) in enumerate(full_grid)
                   if (inst, rx.DOMAIN_LABEL[p]) in members]

    # --- Pass 1: resolve every member stratum's return array (n_resolved >= EVENT_FLOOR). ---
    arrays: dict[tuple, np.ndarray] = {}             # (sub,inst,domain,cand) -> returns
    n_skipped = 0
    for ci, inst, period in tqdm(member_grid, desc="resolve cells"):
        domain = rx.DOMAIN_LABEL[period]
        li = loaded[inst]
        train_frame = li.frame.slice(0, int(int(li.frame.height) * 0.7))
        cell = resolve_cell_returns(rx, train_frame, inst, period, ci, summary)
        for (sub, cid), arr in cell.items():
            if arr.shape[0] < EVENT_FLOOR:
                n_skipped += 1
                continue
            arrays[(sub, inst, domain, cid)] = arr

    # --- Build cross-cell pools per (substrate, candidate); k = median-n across the pool group. ---
    groups: dict[tuple[str, str], list[tuple]] = {}
    for key in arrays:
        sub, _inst, _dom, cid = key
        groups.setdefault((sub, cid), []).append(key)
    pools: dict[tuple[str, str], np.ndarray] = {}
    k_of: dict[tuple[str, str], float] = {}
    for grp, keys in groups.items():
        pools[grp] = np.concatenate([arrays[k] for k in keys])
        k_of[grp] = float(np.median([arrays[k].shape[0] for k in keys]))

    # --- Pass 2: ASS-score each stratum (shrink toward its (substrate,candidate) pool). ---
    records: list[dict] = []
    recon_ok = True
    for (sub, inst, domain, cid), arr in tqdm(arrays.items(), desc="ass score strata"):
        n_res, gross_exp, gross_med, valid, s2_def, g018a, fail_leg = screen[(sub, inst, domain, cid)]
        if arr.shape[0] != n_res or abs(float(np.mean(arr)) - gross_exp) > RECON_TOL:
            recon_ok = False
            LOGGER.warning("RECON MISMATCH %s/%s/%s/%s: n=%d(vs %d) mean=%.12f(vs %.12f)",
                           sub, inst, domain, cid, arr.shape[0], n_res, float(np.mean(arr)), gross_exp)
        grp = (sub, cid)
        a = ass_row(arr, pools[grp], k_of[grp])
        records.append({
            "substrate": sub, "instrument": inst, "domain": domain, "candidate": cid,
            "branch": rx.CANDIDATE_BRANCH[cid], "n_resolved": int(arr.shape[0]),
            "valid": valid, "s2_deferred": s2_def, "g018a_pass": g018a, "fail_leg": fail_leg,
            "gross_exp": gross_exp, "gross_med": gross_med,
            "ass_exp_unpooled": a["ass_exp_unpooled"], "ass_med_unpooled": a["ass_med_unpooled"],
            "ass_exp_shrunk": a["ass_exp_shrunk"], "ass_med_shrunk": a["ass_med_shrunk"],
            "shrink_weight": a["shrink_weight"], "k_shrink": a["k_shrink"],
            "delta_exp_shrunk_minus_raw": a["ass_exp_shrunk"] - gross_exp,
            "ass_tail": a["ass_tail"], "ass_dip_p": a["ass_dip_p"],
            "ass_shape_flag": a["ass_shape_flag"], "pool_size_n": int(pools[grp].shape[0]),
            "guard_i_defer": bool(arr.shape[0] <= GUARD_I_N),
            "guard_ii_slope_inapplicable": bool(np.isfinite(a["p_gt_2r"])
                                                and a["p_gt_2r"] < GUARD_II_PGT_FLOOR),
        })

    df = pl.DataFrame(records).sort(["substrate", "instrument", "domain", "candidate"])
    df.write_parquet(RESULTS_DIR / "ass_overlay.parquet")
    df.write_csv(RESULTS_DIR / "ass_overlay.csv")
    plot_ass_overlay(df, PLOTS_DIR / "06_ass_overlay.png")

    n_flip = int(df.filter(
        (pl.col("ass_exp_shrunk") > 0) != (pl.col("gross_exp") > 0)).height)
    meta = {
        "experiment": EXPERIMENT_ID, "overlay": "ASS discovery (NON-BINDING; G-017 DISCOVERY_ONLY)",
        "binding": False, "n_rows": int(df.height), "n_skipped_below_floor": int(n_skipped),
        "event_floor": EVENT_FLOOR, "reconciliation_ok": bool(recon_ok), "recon_tol": RECON_TOL,
        "pool_definition": "cross-cell within {substrate, candidate} (full pool incl. the unit)",
        "k_shrink_source": "median-n across the (substrate,candidate) pool (EXP-076 deployed convention)",
        "seeds": {"SEED_RANDOM": rx.SEED_RANDOM, "SEED_BOOT": rx.SEED_BOOT},
        "ass_thresholds": {"TAU_GAP": TAU_GAP, "DIP_ALPHA": DIP_ALPHA},
        "guards": {"guard_i_defer_at_effective_n_leq": GUARD_I_N,
                   "guard_ii_pgt2r_compressed_below": GUARD_II_PGT_FLOOR},
        "n_ass_screen_sign_disagreements": n_flip,
        "holdout_untouched": True, "test_stratum_touched": False, "counted_test_reads": 0,
        "caveats": [
            "ASS shrinkage POOLS across cells -> per-stratum-discipline tension (LESSON-001); these "
            "shrunk estimates are DISCOVERY_ONLY, never a binding per-stratum verdict.",
            "EXP-078 found the shrunk edge-call FPR k-FRAGILE (flips at the 2x multiplier); k here is "
            "the deployed median-n, reported for transparency, not a binding operating point.",
        ],
        "note": "Disclosure-only. Does NOT alter the frozen valid_candidate_set.json (sha256 "
                "fa4035f3…), screen_results.*, or run_metadata.json; no screen decision reads ASS.",
    }
    (RESULTS_DIR / "ass_overlay_meta.json").write_text(json.dumps(meta, indent=2, default=str))

    LOGGER.info("ASS overlay: %d strata (skipped %d < floor), reconciliation_ok=%s",
                df.height, n_skipped, recon_ok)
    LOGGER.info("ASS-vs-screen expectancy sign disagreements: %d; shape-flagged: %d",
                n_flip, int(df.get_column("ass_shape_flag").sum()))
    LOGGER.info("results -> %s", RESULTS_DIR / "ass_overlay.parquet")


if __name__ == "__main__":
    main()
