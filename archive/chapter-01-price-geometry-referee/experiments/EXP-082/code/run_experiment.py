"""EXP-082 — Mechanical exit derivation from the frozen D3 rule (Phase 018, CF-CAPGEO-001).

HYP-003 "derive" step. Deterministic transformation of EXP-081's locked per-cell TRAIN statistics
into triple-barrier exit candidates. **0 statistical tests, 0 RNG, 0 candidate slots, 0 counted TEST
reads, NO market-data read.** For each of the 184 member substrate-cells, the frozen D0 §D3 rule
(``xen.capgeo_exits.derive_barriers``) emits ``(T_fav, S_adv, H_cap)`` for the three registered
``/EXIT-DERIVED`` candidates D1-MEDIAN-CAPTURE / D2-TAIL-ROBUST / D3-CAPTURE-EFFICIENT.

This script orchestrates only: it (1) asserts the EXP-081 provenance fingerprint, (2) applies the
pure derivation function per cell, (3) runs the validity / estimability / degeneracy gates,
(4) asserts the harami-substrate triple identity, (5) replays the derivation for byte-identical
determinism, (6) computes the disclosure-only structural-guard read (NO returns / hit-rates /
expectancy), (7) accounts the D1==D2 coincidence, and (8) hash-pins the derivation module. No exit
is applied, no P&L computed, no screen / separability gate / WF fold / ASS adjudication run — those
are EXP-083.

Inputs (read-only): EXP-081/results/substrate_cell_summary.parquet (+ run_metadata.json). No
data/timebars/ read; no domain-bar build; no substrate regeneration.

Run:
    cd python && python experiments/EXP-082/code/run_experiment.py
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                       # noqa: E402
import polars as pl                      # noqa: E402
import seaborn as sns                    # noqa: E402

from xen.capgeo_exits import (           # noqa: E402
    CANDIDATES,
    D1_MEDIAN_CAPTURE,
    D2_TAIL_ROBUST,
    CellStats,
    derive_barriers,
)

LOGGER = logging.getLogger("EXP-082")

# --------------------------------------------------------------------------- #
# Path setup
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-082"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
EXPERIMENT_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
EXP081_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-081" / "results"
EXP081_SUMMARY = EXP081_RESULTS / "substrate_cell_summary.parquet"
EXP081_META = EXP081_RESULTS / "run_metadata.json"
EXITS_MODULE = PROJECT_ROOT / "python" / "src" / "xen" / "capgeo_exits.py"

# --------------------------------------------------------------------------- #
# Constants (frozen; no free parameters in the rule itself)
# --------------------------------------------------------------------------- #
EVENT_FLOOR = 30                         # D9: usable-event floor; below -> UNDERPOWERED_DISCLOSED
N_MEMBER_CELLS = 184                     # 4 substrates x 46 EXP-080-READY instrument x domain cells
N_INSTR_DOMAIN = 46                      # member instrument x domain cells (harami identity pairs)
SUB_AVWAP = "SUB-AVWAP"
SUB_HARAMI_PARTIAL_V2A = "SUB-HARAMI-PARTIAL-V2A"
SUB_HARAMI_V2A_ADVNONE = "SUB-HARAMI-V2A-ADVNONE"
SUB_RANDOM = "SUB-RANDOM"
DOMAIN_ORDER = ["15m", "1h", "4h"]
SUBSTRATE_ORDER = [SUB_AVWAP, SUB_HARAMI_PARTIAL_V2A, SUB_HARAMI_V2A_ADVNONE, SUB_RANDOM]
# D3 input columns consumed from EXP-081 (ass_* deliberately excluded).
D3_INPUT_COLS = ["instrument", "domain", "substrate", "n_usable", "mfe_med", "mfe_q40",
                 "ttp_med", "ttp_q75", "mae_q90", "m_anti", "dip_p", "tailmass", "q05",
                 "tail_boundary"]


# --------------------------------------------------------------------------- #
# I/O helpers
# --------------------------------------------------------------------------- #
def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_exp081_inputs() -> tuple[pl.DataFrame, dict]:
    """Load the EXP-081 summary + metadata (read-only); no market data is touched."""
    meta = json.loads(EXP081_META.read_text())
    cells = pl.read_parquet(EXP081_SUMMARY).select(D3_INPUT_COLS)
    return cells, meta


# --------------------------------------------------------------------------- #
# Pure checks / computation
# --------------------------------------------------------------------------- #
def assert_provenance(cells: pl.DataFrame, meta: dict) -> dict:
    """Assert the EXP-081 fingerprint (Step 1); return a recorded provenance block.

    HALT on any mismatch — EXP-082 must derive from the audited CHARACTERISATION_DELIVERED result.
    """
    checks = {
        "verdict": meta.get("verdict") == "CHARACTERISATION_DELIVERED",
        "n_substrate_cells": meta.get("n_substrate_cells") == N_MEMBER_CELLS,
        "n_underpowered_cells": meta.get("n_underpowered_cells") == 0,
        "holdout_untouched": meta.get("holdout_untouched") is True,
        "counted_test_reads": meta.get("counted_test_reads") == 0,
        "summary_height": cells.height == N_MEMBER_CELLS,
        "n_usable_floor": int(cells.get_column("n_usable").min()) >= EVENT_FLOOR,
        "substrate_set": sorted(cells.get_column("substrate").unique().to_list())
        == sorted(SUBSTRATE_ORDER),
    }
    failed = [k for k, ok in checks.items() if not ok]
    if failed:
        raise RuntimeError(f"EXP-081 provenance assertion failed: {failed}")
    return {
        "exp081_verdict": meta["verdict"],
        "exp081_n_substrate_cells": meta["n_substrate_cells"],
        "exp081_module_hashes": meta.get("module_hashes", {}),
        "exp081_summary_sha256": _hash_file(EXP081_SUMMARY),
        "checks": checks,
    }


def _row_to_stats(row: dict) -> CellStats:
    return CellStats(
        mfe_med=float(row["mfe_med"]), mfe_q40=float(row["mfe_q40"]),
        ttp_med=float(row["ttp_med"]), ttp_q75=float(row["ttp_q75"]),
        mae_q90=float(row["mae_q90"]), m_anti=float(row["m_anti"]))


def _disposition(row: dict, t_fav: float, s_adv: float, h_cap: int) -> str:
    """Validity gate (Step 3): OK / UNDERPOWERED_DISCLOSED / DEGENERATE_DISCLOSED."""
    if int(row["n_usable"]) < EVENT_FLOOR:
        return "UNDERPOWERED_DISCLOSED"
    if not (np.isfinite(t_fav) and t_fav > 0.0):
        return "DEGENERATE_DISCLOSED"
    if not (np.isfinite(s_adv) and s_adv > 0.0):
        return "DEGENERATE_DISCLOSED"
    if h_cap < 1:
        return "DEGENERATE_DISCLOSED"
    return "OK"


def derive_table(cells: pl.DataFrame) -> pl.DataFrame:
    """Apply the frozen rule per cell -> 552-row (cell x candidate) derived-candidate table.

    Disclosure-only structural-guard fields (Step 7: t_fav/s_adv ratio, s_adv vs |q05| and
    |tail_boundary|) are descriptive comparisons of derived barriers to EXP-081 statistics — no
    realized return, hit-rate, or expectancy is computed.
    """
    out: list[dict] = []
    for row in cells.iter_rows(named=True):                       # 184 rows — clear per-row apply
        stats = _row_to_stats(row)
        barriers = derive_barriers(stats)
        q05_abs = abs(float(row["q05"]))
        tb_abs = abs(float(row["tail_boundary"]))
        for cand in CANDIDATES:
            b = barriers[cand]
            disp = _disposition(row, b.t_fav, b.s_adv, b.h_cap)
            out.append({
                "instrument": row["instrument"], "domain": row["domain"],
                "substrate": row["substrate"], "candidate": cand,
                "T_fav": b.t_fav, "S_adv": b.s_adv, "H_cap": b.h_cap,
                "s_adv_source": b.s_adv_source, "h_cap_pre_round": b.h_cap_pre_round,
                "n_usable": int(row["n_usable"]), "valid": disp == "OK", "disposition": disp,
                # structural-guard disclosure (non-adjudicative):
                "t_over_s": (b.t_fav / b.s_adv) if b.s_adv > 0 else float("nan"),
                "s_adv_minus_absq05": b.s_adv - q05_abs,
                "s_adv_minus_abstailboundary": b.s_adv - tb_abs,
                "tailmass": float(row["tailmass"]),
            })
    return pl.DataFrame(out)


def canonical_fingerprint(table: pl.DataFrame) -> str:
    """Order-independent sha256 of the derived triples (determinism comparator, Step 5)."""
    key = ["instrument", "domain", "substrate", "candidate"]
    sub = table.select(key + ["T_fav", "S_adv", "H_cap", "s_adv_source"]).sort(key)
    recs = [{k: (round(v, 12) if isinstance(v, float) and np.isfinite(v) else v)
             for k, v in r.items()} for r in sub.iter_rows(named=True)]
    return hashlib.sha256(json.dumps(recs, sort_keys=True, default=str).encode()).hexdigest()


def assert_harami_identity(table: pl.DataFrame) -> bool:
    """Step 4: the two harami substrates share one entry population -> identical triples per pair."""
    key = ["instrument", "domain", "candidate"]
    cols = ["T_fav", "S_adv", "H_cap", "s_adv_source"]
    a = table.filter(pl.col("substrate") == SUB_HARAMI_PARTIAL_V2A).sort(key).select(key + cols)
    b = table.filter(pl.col("substrate") == SUB_HARAMI_V2A_ADVNONE).sort(key).select(key + cols)
    if a.height != N_INSTR_DOMAIN * len(CANDIDATES) or not a.equals(b):
        raise RuntimeError("harami-substrate triple identity assertion failed")
    return True


def d1_d2_accounting(table: pl.DataFrame) -> dict:
    """Step 8: count cells where D1 and D2 emit identical vs divergent triples + the mechanism."""
    key = ["instrument", "domain", "substrate"]
    cols = ["T_fav", "S_adv", "H_cap"]
    d1 = table.filter(pl.col("candidate") == D1_MEDIAN_CAPTURE).sort(key).select(key + cols)
    d2 = table.filter(pl.col("candidate") == D2_TAIL_ROBUST).sort(key).select(key + cols)
    merged = d1.join(d2, on=key, suffix="_d2")
    same = merged.filter(
        (pl.col("S_adv") == pl.col("S_adv_d2")) & (pl.col("T_fav") == pl.col("T_fav_d2"))
        & (pl.col("H_cap") == pl.col("H_cap_d2")))
    return {
        "n_cells": d1.height,
        "n_d1_eq_d2": same.height,
        "n_d1_ne_d2": d1.height - same.height,
        "mechanism": "D2 'tightened to the dip' = min(m_anti, MAE_q90); diverges iff "
                     "m_anti > MAE_q90. On this TRAIN snapshot m_anti resolves rarely and below "
                     "MAE_q90, so D1==D2 numerically (disclosed; distinct functions for EXP-083 "
                     "per-fold re-fit).",
    }


def s_adv_source_accounting(table: pl.DataFrame) -> dict:
    """Per-candidate m_anti-resolved vs MAE_q90-fallback split (Step 2/3 accounting)."""
    acc: dict[str, dict] = {}
    for cand in CANDIDATES:
        sub = table.filter(pl.col("candidate") == cand)
        acc[cand] = {
            "n": sub.height,
            "m_anti": int(sub.filter(pl.col("s_adv_source") == "m_anti").height),
            "mae_q90": int(sub.filter(pl.col("s_adv_source") == "mae_q90").height),
            "n_valid": int(sub.filter(pl.col("valid")).height),
        }
    return acc


# --------------------------------------------------------------------------- #
# Plotting (<=3; descriptive disclosure of derived definitions — not results)
# --------------------------------------------------------------------------- #
def _pivot_heatmap(table: pl.DataFrame, substrate: str, value: str) -> "tuple":
    sub = table.filter((pl.col("substrate") == substrate)
                       & (pl.col("candidate") == D1_MEDIAN_CAPTURE))
    instruments = sub.get_column("instrument").unique().sort().to_list()
    mat = np.full((len(instruments), len(DOMAIN_ORDER)), np.nan)
    idx = {ins: i for i, ins in enumerate(instruments)}
    for r in sub.iter_rows(named=True):
        if r["domain"] in DOMAIN_ORDER:
            mat[idx[r["instrument"]], DOMAIN_ORDER.index(r["domain"])] = r[value]
    return instruments, mat


def plot_barrier_panel(table: pl.DataFrame, save_path: Path) -> None:
    """Plot 1: D1 barrier-triple heatmaps (T_fav, S_adv, H_cap) by substrate x domain."""
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(3, 4, figsize=(16, 11))
    for col, sub in enumerate(SUBSTRATE_ORDER):
        for row_i, (val, label) in enumerate(
                [("T_fav", "T_fav (ATR)"), ("S_adv", "S_adv (ATR)"), ("H_cap", "H_cap (bars)")]):
            instruments, mat = _pivot_heatmap(table, sub, val)
            ax = axes[row_i, col]
            sns.heatmap(mat, ax=ax, cmap="viridis", cbar=True,
                        xticklabels=DOMAIN_ORDER,
                        yticklabels=instruments if col == 0 else False,
                        annot=False)
            if row_i == 0:
                ax.set_title(sub.replace("SUB-", ""), fontsize=10)
            if col == 0:
                ax.set_ylabel(label, fontsize=9)
    fig.suptitle("EXP-082 D1-MEDIAN-CAPTURE derived barriers by substrate x domain", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.98))
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_s_adv_source(table: pl.DataFrame, save_path: Path) -> None:
    """Plot 2: m_anti-resolved vs MAE_q90-fallback split across the member set (D1)."""
    sns.set_theme(style="whitegrid")
    sub = table.filter(pl.col("candidate") == D1_MEDIAN_CAPTURE)
    counts = (sub.group_by("substrate")
              .agg([(pl.col("s_adv_source") == "m_anti").sum().alias("m_anti"),
                    (pl.col("s_adv_source") == "mae_q90").sum().alias("mae_q90")])
              .sort("substrate"))
    subs = counts.get_column("substrate").to_list()
    m_anti = counts.get_column("m_anti").to_list()
    mae = counts.get_column("mae_q90").to_list()
    x = np.arange(len(subs))
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(x, mae, label="MAE_q90 fallback", color="#4c72b0")
    ax.bar(x, m_anti, bottom=mae, label="m_anti (dip-resolved)", color="#dd8452")
    ax.set_xticks(x)
    ax.set_xticklabels([s.replace("SUB-", "") for s in subs], rotation=15)
    ax.set_ylabel("member cells")
    ax.set_title("EXP-082 adverse-leg source split (D1; m_anti dormant by D0 §D9)", fontsize=12)
    ax.legend()
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_tfav_vs_sadv(table: pl.DataFrame, save_path: Path) -> None:
    """Plot 3: T_fav vs S_adv (ATR) by substrate, |q05| overlaid (structural-guard disclosure)."""
    sns.set_theme(style="whitegrid")
    sub = table.filter(pl.col("candidate") == D1_MEDIAN_CAPTURE).to_pandas()
    sub["abs_q05"] = (sub["S_adv"] - sub["s_adv_minus_absq05"])  # = |q05| recovered for sizing
    fig, ax = plt.subplots(figsize=(9, 7))
    palette = dict(zip(SUBSTRATE_ORDER, sns.color_palette("deep", len(SUBSTRATE_ORDER))))
    for s in SUBSTRATE_ORDER:
        d = sub[sub["substrate"] == s]
        ax.scatter(d["T_fav"], d["S_adv"], s=18 + 6 * d["abs_q05"].clip(0, 20),
                   alpha=0.7, label=s.replace("SUB-", ""), color=palette[s])
    lim = max(float(sub["T_fav"].max()), float(sub["S_adv"].max())) * 1.05
    ax.plot([0, lim], [0, lim], ls="--", color="grey", lw=1, label="T_fav = S_adv")
    ax.set_xlabel("T_fav — favourable target (ATR)")
    ax.set_ylabel("S_adv — adverse stop (ATR)")
    ax.set_title("EXP-082 derived target vs stop (D1); point size ~ |q05| catastrophe (disclosure)",
                 fontsize=11)
    ax.legend(title="substrate", fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGGER.info("EXP-082 — mechanical exit derivation from the frozen D3 rule")

    cells, exp081_meta = load_exp081_inputs()
    provenance = assert_provenance(cells, exp081_meta)
    LOGGER.info("EXP-081 provenance OK (verdict=%s, cells=%d)",
                provenance["exp081_verdict"], cells.height)

    table = derive_table(cells)
    table2 = derive_table(cells)                                  # determinism replay (Step 5)
    fp1, fp2 = canonical_fingerprint(table), canonical_fingerprint(table2)
    determinism_ok = fp1 == fp2

    harami_ok = assert_harami_identity(table)
    d1d2 = d1_d2_accounting(table)
    src_acc = s_adv_source_accounting(table)

    n_rows = table.height
    n_valid = int(table.filter(pl.col("valid")).height)
    n_underpowered = int(table.filter(pl.col("disposition") == "UNDERPOWERED_DISCLOSED").height)
    n_degenerate = int(table.filter(pl.col("disposition") == "DEGENERATE_DISCLOSED").height)
    verdict = ("DERIVATION_DELIVERED"
               if determinism_ok and harami_ok and n_valid == n_rows
               else "HALT")

    # Persist results.
    table.write_parquet(RESULTS_DIR / "derived_candidates.parquet")
    table.write_csv(RESULTS_DIR / "derived_candidates.csv")

    validity = {
        "verdict": verdict,
        "n_triples": n_rows,
        "n_valid": n_valid,
        "n_underpowered_disclosed": n_underpowered,
        "n_degenerate_disclosed": n_degenerate,
        "determinism_replay_byte_identical": determinism_ok,
        "harami_identity_ok": harami_ok,
        "s_adv_source_accounting": src_acc,
        "d1_eq_d2_accounting": d1d2,
        "provenance": provenance,
    }
    (RESULTS_DIR / "derivation_validity.json").write_text(json.dumps(validity, indent=2, default=str))

    meta = {
        "experiment": EXPERIMENT_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "n_member_cells": cells.height,
        "n_triples": n_rows,
        "derive_barriers_module_sha256": _hash_file(EXITS_MODULE),
        "determinism_fingerprint": fp1,
        "frozen_constants": {
            "rule": "D0 §D3 verbatim (D1/D2/D3 triple-barrier; barriers are EXP-081 quantiles)",
            "EVENT_FLOOR": EVENT_FLOOR,
            "h_cap_integerization": "max(1, round-half-even(ttp_quantile))",
            "d2_tightened_to_dip": "min(m_anti, MAE_q90) if isfinite(m_anti) else MAE_q90",
            "units": "T_fav/S_adv in ATR (EXP-081 norm); H_cap in domain bars",
        },
        "exp081_input": {
            "summary_parquet": str(EXP081_SUMMARY.relative_to(PROJECT_ROOT)),
            "summary_sha256": provenance["exp081_summary_sha256"],
            "exp081_module_hashes": provenance["exp081_module_hashes"],
        },
        "holdout_untouched": True,
        "counted_test_reads": 0,
        "candidate_slots": 0,
    }
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(meta, indent=2, default=str))

    # Plots (bounded; from the derived table only).
    plot_barrier_panel(table, PLOTS_DIR / "01_barrier_triples.png")
    plot_s_adv_source(table, PLOTS_DIR / "02_s_adv_source_split.png")
    plot_tfav_vs_sadv(table, PLOTS_DIR / "03_tfav_vs_sadv.png")

    LOGGER.info("verdict=%s triples=%d valid=%d underpowered=%d degenerate=%d",
                verdict, n_rows, n_valid, n_underpowered, n_degenerate)
    LOGGER.info("D1==D2 cells: %d/%d (diverge %d); s_adv m_anti-resolved per candidate: %s",
                d1d2["n_d1_eq_d2"], d1d2["n_cells"], d1d2["n_d1_ne_d2"],
                {c: src_acc[c]["m_anti"] for c in CANDIDATES})
    LOGGER.info("determinism=%s harami_identity=%s; results -> %s",
                determinism_ok, harami_ok, RESULTS_DIR)


if __name__ == "__main__":
    main()
