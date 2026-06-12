"""Experiment EXP-045: Phase 011 Track B Per-Cell Exit Training (37 Cells).

Implements the approved analysis plan (analysis-plan.md). For each of the 37
COVERED cells certified by EXP-044 (TRAIN stratum only, F01 file-order rows):

1. regenerate the frozen-baseline events bit-for-bit and assert the event
   count matches EXP-043 (consistency gate; source-identity binding);
2. simulate per-event exits for both G0-frozen families — FH(H) over
   {2,3,4,6,8,11,16,23} and MAD-band-target(m) over the P6 grid — in one
   causal pass; net returns under the frozen P2 CONSERVATIVE cost model;
3. select θ* per family by the n-neighbour stability plane (k=1,
   interior-only), apply the tunability rule (1×SE separation + split-half
   agreement) and the P4 membership floor S(θ*) ≥ +1×SE;
4. report the membership set and the G2 composition readout (P5: ≥5 member
   cells over ≥3 instruments);
5. determinism replay: two predeclared cells fully re-run and compared.

TRAIN-only; the TEST stratum and the final-30% global holdout are never
loaded. 0 TEST reads; no market-edge claim is made here.

Outputs: ``results/exit_selection.csv``, ``results/score_curves.csv``,
``results/split_half.csv``, ``results/membership.csv``,
``results/run_metadata.json``, and five plots from the bounded summaries.
"""
from __future__ import annotations

import json
import logging
import math
import sys
import time
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from tqdm.auto import tqdm

# --------------------------------------------------------------------------- #
# Path setup
# --------------------------------------------------------------------------- #
EXP_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = EXP_DIR.parents[2]
SRC_DIR = PROJECT_ROOT / "python" / "src"
CODE_DIR = EXP_DIR / "code"
for extra in (str(SRC_DIR), str(CODE_DIR)):
    if extra not in sys.path:
        sys.path.insert(0, extra)

import cell_exits as cx  # noqa: E402
from xen.avwap import generate_avwap_events  # noqa: E402
from xen.bar_aggregator import aggregate_ohlc  # noqa: E402
from xen.referee_calibration import seed_for  # noqa: E402

# --------------------------------------------------------------------------- #
# Constants (frozen by scope / analysis plan / D0 — no tuning levers)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-045"
DATA_DIR = PROJECT_ROOT / "data" / "timebars"
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"
EXP043_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-043" / "results"
EXP044_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-044" / "results"

DOMAINS: dict[str, int] = {"1h": 60, "2h": 120, "4h": 240}
MIN_COVERAGE = 0.90
ANALYSIS_FRACTION = 0.7
TRAIN_FRACTION = 0.7
EXCLUDED_FILE_MARKERS = ("analysis70", "analysis_slice", "first70")

EXPECTED_COVERED_CELLS = 37
G2_MIN_CELLS = 5
G2_MIN_INSTRUMENTS = 3
N_BOOT = 1_000
REPLAY_CELLS: tuple[tuple[str, str], ...] = (("GBPUSD", "1h"), ("JP225", "4h"))

# D0 P2 cost model (CONSERVATIVE RT bps, financing bps/day) — frozen, incl.
# the EURUSD 3.0 RT transcription-error correction.
COSTS: dict[str, tuple[float, float]] = {
    "EURUSD": (3.0, 0.6), "USTEC": (5.0, 1.2), "XAUUSD": (6.0, 1.2),
    "BTCUSD": (16.0, 10.0), "GBPUSD": (4.0, 0.8), "USDJPY": (3.6, 0.7),
    "USDCHF": (4.4, 0.7), "USDCAD": (4.4, 0.7), "AUDUSD": (4.0, 0.7),
    "NZDUSD": (5.2, 0.8), "EURJPY": (4.4, 0.8), "GBPJPY": (5.6, 1.0),
    "AUDJPY": (5.2, 0.9), "US500": (3.2, 1.2), "US2000": (6.0, 1.2),
    "DE30": (4.0, 1.2), "JP225": (4.8, 1.2),
}

DE30_DISCLOSURE = (
    "DE30 truncated history: broker history ends 2026-01-16 (~5 months short); "
    "70/30/holdout boundaries derive from its own realized timeline (D0 P8)."
)

LOGGER = logging.getLogger(EXPERIMENT_ID)


# --------------------------------------------------------------------------- #
# I/O helpers (EXP-043/044 loader pattern, unchanged)
# --------------------------------------------------------------------------- #
def find_source_file(instrument: str) -> Path:
    """Return the newest full (non-derivative) 1-minute Parquet for one symbol."""
    matches = sorted(
        p for p in DATA_DIR.glob(f"timebars_{instrument.lower()}_*.parquet")
        if not any(marker in p.name for marker in EXCLUDED_FILE_MARKERS)
    )
    if not matches:
        raise FileNotFoundError(f"no 1-minute source file for {instrument} under {DATA_DIR}")
    return matches[-1]


def load_train_frame(instrument: str, expected: dict[str, Any]) -> pl.DataFrame:
    """Load exactly the TRAIN 1-minute rows (F01 pattern), bound to EXP-043."""
    path = find_source_file(instrument)
    if path.name != expected["source_file"]:
        raise RuntimeError(
            f"{instrument}: source file {path.name} != EXP-043 certified "
            f"{expected['source_file']}"
        )
    total = int(pl.scan_parquet(path).select(pl.len()).collect().item())
    if total != int(expected["total_rows_1m"]):
        raise RuntimeError(f"{instrument}: total rows {total} != EXP-043 "
                           f"{expected['total_rows_1m']}")
    train_rows = int(math.floor(TRAIN_FRACTION * math.floor(ANALYSIS_FRACTION * total)))
    if train_rows != int(expected["train_rows_1m"]):
        raise RuntimeError(f"{instrument}: train rows {train_rows} != EXP-043 "
                           f"{expected['train_rows_1m']}")
    frame = (
        pl.scan_parquet(path)
        .select("Symbol", "OpenTime", "CloseTime", "Open", "High", "Low", "Close", "TickVolume")
        .head(train_rows)
        .collect()
    )
    if frame.height != train_rows:
        raise RuntimeError(f"{instrument}: collected {frame.height} != train_rows {train_rows}")
    close_time = frame.get_column("CloseTime")
    if not close_time.is_sorted() or close_time.n_unique() != frame.height:
        raise RuntimeError(f"{instrument}: TRAIN slice not strictly chronological")
    if str(close_time.max()) != str(expected["train_end_ts"]):
        raise RuntimeError(f"{instrument}: TRAIN end {close_time.max()} != EXP-043 "
                           f"{expected['train_end_ts']}")
    return frame


def load_covered_cells() -> tuple[list[tuple[str, str, int]], dict[str, dict[str, Any]]]:
    """Dependency gates: EXP-044 COVERED grid + EXP-043 counts and boundaries."""
    meta44 = json.loads((EXP044_RESULTS / "run_metadata.json").read_text())
    if meta44.get("verdict") != "CALIBRATION_DELIVERED":
        raise RuntimeError(f"EXP-044 gate failed: verdict={meta44.get('verdict')}")
    coverage = pl.read_csv(EXP044_RESULTS / "coverage_map.csv")
    covered = coverage.filter(pl.col("verdict") == "COVERED").sort(["instrument", "domain"])
    if covered.height != EXPECTED_COVERED_CELLS:
        raise RuntimeError(f"COVERED cells {covered.height} != {EXPECTED_COVERED_CELLS}")
    meta43 = json.loads((EXP043_RESULTS / "run_metadata.json").read_text())
    boundaries: dict[str, dict[str, Any]] = meta43["boundaries"]
    power = pl.read_csv(EXP043_RESULTS / "power_statement.csv")
    counts = {(r["instrument"], r["domain"]): int(r["train_events"])
              for r in power.to_dicts()}
    cells = []
    for r in covered.to_dicts():
        key = (r["instrument"], r["domain"])
        if key not in counts:
            raise RuntimeError(f"{key}: missing from EXP-043 power_statement")
        cells.append((r["instrument"], r["domain"], counts[key]))
    missing = {c[0] for c in cells} - set(boundaries)
    if missing:
        raise RuntimeError(f"EXP-043 boundary record missing instruments: {sorted(missing)}")
    return cells, boundaries


# --------------------------------------------------------------------------- #
# Per-cell substrate (frozen events -> exit-simulation arrays)
# --------------------------------------------------------------------------- #
def build_cell(
    instrument: str, domain: str, expected_events: int, frame_1m: pl.DataFrame
) -> tuple[cx.CellEvents, np.ndarray]:
    """Regenerate the frozen events for one cell and assemble exit arrays.

    Hard-fails if the regenerated event count differs from the EXP-043
    realized count. Returns the cell arrays plus per-event trigger times
    (epoch microseconds) for the chronological split-half rule.
    """
    bars = aggregate_ohlc(frame_1m, period_minutes=DOMAINS[domain],
                          min_coverage=MIN_COVERAGE)
    result = generate_avwap_events(
        bars.select("CloseTime", "Open", "High", "Low", "Close", "TickVolume"),
        instrument=instrument, domain=domain,
    )
    if result.events.height != expected_events:
        raise RuntimeError(
            f"{instrument}-{domain}: regenerated event count "
            f"{result.events.height} != EXP-043 realized {expected_events}"
        )
    ev = result.events
    rg = result.regimes.sort("confirm_idx")
    n = bars.height
    trigger_idx = ev.get_column("trigger_idx").to_numpy()
    direction = ev.get_column("direction").to_numpy()
    trend = cx.trend_change_lookup(
        trigger_idx, direction,
        rg.get_column("confirm_idx").to_numpy(),
        rg.get_column("direction").to_numpy(),
        n,
    )
    rt_cost, financing = COSTS[instrument]
    cell = cx.CellEvents(
        instrument=instrument,
        domain=domain,
        n_bars=n,
        close=bars.get_column("Close").to_numpy(),
        close_time_ns=bars.get_column("CloseTime").cast(pl.Int64).to_numpy(),  # ns epoch
        trigger_idx=trigger_idx,
        direction=direction,
        regime_id=ev.get_column("regime_id").to_numpy(),
        avwap=ev.get_column("avwap_at_trigger").to_numpy(),
        spread=ev.get_column("band_spread_at_trigger").to_numpy(),
        trend_change_idx=trend,
        rt_cost_bps=rt_cost,
        financing_bps_day=financing,
    )
    trigger_time_ns = ev.get_column("trigger_time").cast(pl.Int64).to_numpy()  # ns epoch
    return cell, trigger_time_ns


# --------------------------------------------------------------------------- #
# Per-cell training (pure computation over the cell arrays)
# --------------------------------------------------------------------------- #
def run_cell(
    cell: cx.CellEvents, trigger_time_ns: np.ndarray
) -> tuple[dict[str, Any], list[dict], list[dict]]:
    """Train both families in one cell; return selection row + curve/half rows."""
    outcomes = {cx.FAMILY_FH: cx.simulate_fh(cell), cx.FAMILY_MAD: cx.simulate_mad(cell)}
    verdicts: dict[str, cx.FamilyVerdict] = {}
    curve_rows, half_rows = [], []
    for family, outcome in outcomes.items():
        rng = np.random.default_rng(
            seed_for(EXPERIMENT_ID, cell.instrument, cell.domain, family, "se")
        )
        verdict = cx.classify_family(outcome, cell, trigger_time_ns, rng)
        verdicts[family] = verdict
        scores = cx.score_curve(outcome.net_bps)
        plane = cx.stability_plane(scores)
        forced_frac = outcome.forced.mean(axis=0)
        for j, theta in enumerate(outcome.grid):
            curve_rows.append({
                "instrument": cell.instrument, "domain": cell.domain,
                "disclosure": DE30_DISCLOSURE if cell.instrument == "DE30" else "",
                "family": family, "theta": theta,
                "interior": bool(cx.interior_mask(len(outcome.grid))[j]),
                "net_mean_bps": float(scores[j]),
                "stability_s": float(plane[j]),
                "n_events": int(outcome.net_bps.shape[0]),
                "forced_close_frac": float(forced_frac[j]),
                "forced_disclosure": bool(
                    forced_frac[j] > cx.FORCED_CLOSE_DISCLOSURE_FRAC
                ),
            })
        half_rows.append({
            "instrument": cell.instrument, "domain": cell.domain,
            "disclosure": DE30_DISCLOSURE if cell.instrument == "DE30" else "",
            "family": family,
            "full_pos": verdict.theta_star_pos,
            "half1_pos": verdict.half1_pos, "half2_pos": verdict.half2_pos,
            # Direct agreement: both halves populated and within +/-1 grid
            # step of the full-TRAIN position — independent of which failure
            # reason (if any) bound first.
            "agree": (verdict.half1_pos is not None
                      and verdict.half2_pos is not None
                      and abs(verdict.half1_pos - verdict.theta_star_pos) <= 1
                      and abs(verdict.half2_pos - verdict.theta_star_pos) <= 1),
        })
    chosen_family, leader = cx.select_cell_exit(
        verdicts[cx.FAMILY_FH], verdicts[cx.FAMILY_MAD]
    )
    member = cx.is_member(leader)
    fh, mad = verdicts[cx.FAMILY_FH], verdicts[cx.FAMILY_MAD]
    selection = {
        "instrument": cell.instrument, "domain": cell.domain,
        "disclosure": DE30_DISCLOSURE if cell.instrument == "DE30" else "",
        "n_events": int(cell.trigger_idx.shape[0]),
        "fh_theta_star": fh.theta_star, "fh_s_at_star": fh.s_at_star,
        "fh_se": fh.se, "fh_tunable": fh.tunable, "fh_reason": fh.reason,
        "mad_theta_star": mad.theta_star, "mad_s_at_star": mad.s_at_star,
        "mad_se": mad.se, "mad_tunable": mad.tunable, "mad_reason": mad.reason,
        "selected_family": chosen_family,
        "selected_theta": leader.theta_star if leader else None,
        "selected_s": leader.s_at_star if leader else None,
        "selected_se": leader.se if leader else None,
        "member": member,
        "cell_verdict": ("MEMBER" if member
                         else "FLOOR_FAIL" if chosen_family else "NON_TUNABLE"),
    }
    return selection, curve_rows, half_rows


def run_all_cells(
    cells: list[tuple[str, str, int]], boundaries: dict[str, dict[str, Any]], desc: str
) -> tuple[list[dict], list[dict], list[dict]]:
    """Train every cell, loading each instrument's 1-minute frame once."""
    selections, curves, halves = [], [], []
    by_instrument: dict[str, list[tuple[str, str, int]]] = {}
    for spec in cells:
        by_instrument.setdefault(spec[0], []).append(spec)
    with tqdm(total=len(cells), desc=desc) as progress:
        for instrument, specs in by_instrument.items():
            frame_1m = load_train_frame(instrument, boundaries[instrument])
            for inst, domain, expected in specs:
                progress.set_postfix_str(f"{inst}-{domain}")
                cell, trig_ns = build_cell(inst, domain, expected, frame_1m)
                sel, cur, hal = run_cell(cell, trig_ns)
                selections.append(sel)
                curves.extend(cur)
                halves.extend(hal)
                progress.update(1)
            del frame_1m
    return selections, curves, halves


def determinism_replay(
    cells: list[tuple[str, str, int]], boundaries: dict[str, dict[str, Any]],
    selections: list[dict], curves: list[dict],
) -> bool:
    """Fully re-run the two predeclared replay cells and compare exactly."""
    replay_specs = [c for c in cells if (c[0], c[1]) in REPLAY_CELLS]
    if {(c[0], c[1]) for c in replay_specs} != set(REPLAY_CELLS):
        raise RuntimeError(
            f"replay cells {sorted(REPLAY_CELLS)} not all present in the "
            f"COVERED grid: found {sorted((c[0], c[1]) for c in replay_specs)}"
        )
    re_sel, re_cur, _ = run_all_cells(replay_specs, boundaries,
                                      "EXP-045 determinism replay (2 cells)")
    sel_by_key = {(s["instrument"], s["domain"]): s for s in selections}
    for s in re_sel:
        if sel_by_key[(s["instrument"], s["domain"])] != s:
            LOGGER.warning("determinism replay MISMATCH (selection) on %s-%s",
                           s["instrument"], s["domain"])
            return False
    cur_by_key = {(c["instrument"], c["domain"], c["family"], c["theta"]): c
                  for c in curves}
    for c in re_cur:
        if cur_by_key[(c["instrument"], c["domain"], c["family"], c["theta"])] != c:
            LOGGER.warning("determinism replay MISMATCH (curve) on %s-%s",
                           c["instrument"], c["domain"])
            return False
    return True


# --------------------------------------------------------------------------- #
# Plotting (inputs: bounded summary rows only)
# --------------------------------------------------------------------------- #
def _plane_small_multiples(
    curves: list[dict], family: str, selections: list[dict], path: Path
) -> None:
    """Small-multiple stability planes for one family across all cells."""
    cells = sorted({(c["instrument"], c["domain"]) for c in curves})
    ncols = 6
    nrows = math.ceil(len(cells) / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(2.6 * ncols, 1.9 * nrows),
                             squeeze=False)
    sel_by_key = {(s["instrument"], s["domain"]): s for s in selections}
    for ax in axes.flat:
        ax.set_visible(False)
    for idx, (inst, dom) in enumerate(cells):
        ax = axes[idx // ncols][idx % ncols]
        ax.set_visible(True)
        rows = sorted((c for c in curves
                       if c["instrument"] == inst and c["domain"] == dom
                       and c["family"] == family), key=lambda c: c["theta"])
        thetas = [c["theta"] for c in rows]
        ax.plot(thetas, [c["net_mean_bps"] for c in rows], "o-", ms=2.5, lw=0.8,
                color="grey", label="score")
        ax.plot(thetas, [c["stability_s"] for c in rows], "s-", ms=2.5, lw=1.0,
                color="steelblue", label="S")
        sel = sel_by_key.get((inst, dom), {})
        star = sel.get(f"{family.lower()}_theta_star")
        if star is not None:
            ax.axvline(star, color="seagreen", lw=0.8, linestyle="--")
        ax.axhline(0, color="black", lw=0.5)
        ax.set_xscale("log")
        ax.set_title(f"{inst}-{dom}", fontsize=7)
        ax.tick_params(labelsize=5)
    fig.suptitle(f"EXP-045 {family} stability planes (37 cells)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_membership_map(selections: list[dict], path: Path) -> None:
    """17x3 map of selected exits / verdicts; excluded cells hatched."""
    instruments = sorted(COSTS)
    domains = list(DOMAINS)
    fig, ax = plt.subplots(figsize=(7, 10))
    color = {"MEMBER": "seagreen", "FLOOR_FAIL": "goldenrod", "NON_TUNABLE": "indianred"}
    sel_by_key = {(s["instrument"], s["domain"]): s for s in selections}
    for i, inst in enumerate(instruments):
        for j, dom in enumerate(domains):
            s = sel_by_key.get((inst, dom))
            if s is None:
                ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1,
                                           fill=False, hatch="///",
                                           edgecolor="grey", lw=0.3))
                continue
            ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1,
                                       color=color[s["cell_verdict"]], alpha=0.75))
            label = (f"{s['selected_family']} {s['selected_theta']:g}"
                     if s["selected_family"] else "—")
            ax.text(j, i, label, ha="center", va="center", fontsize=6)
    ax.set_xlim(-0.5, len(domains) - 0.5)
    ax.set_ylim(len(instruments) - 0.5, -0.5)
    ax.set_xticks(range(len(domains)), domains)
    ax.set_yticks(range(len(instruments)), instruments, fontsize=7)
    ax.set_title("EXP-045 selected exits and membership "
                 "(green=member, gold=floor fail, red=non-tunable, hatch=excluded)\n"
                 "DE30: truncated history (D0 P8 disclosure)", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_stability_vs_se(selections: list[dict], path: Path) -> None:
    """S(θ*) vs SE per cell, by domain, with the P4 floor line S = SE."""
    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    markers = {"1h": "o", "2h": "s", "4h": "^"}
    for dom in DOMAINS:
        xs, ys, labels = [], [], []
        for s in selections:
            if s["domain"] == dom and s["selected_family"]:
                xs.append(s["selected_se"])
                ys.append(s["selected_s"])
                labels.append(s["instrument"])
        if xs:
            ax.scatter(xs, ys, marker=markers[dom], alpha=0.8, label=dom)
            for x, y, lab in zip(xs, ys, labels):
                ax.annotate(lab, (x, y), fontsize=4.5, alpha=0.7)
    lim = ax.get_xlim()
    grid = np.linspace(0, lim[1], 50)
    ax.plot(grid, grid, color="red", lw=1, linestyle="--", label="P4 floor S = SE")
    ax.axhline(0, color="black", lw=0.5)
    ax.set_xlabel("bootstrap SE at θ* (bps)")
    ax.set_ylabel("S(θ*) (bps)")
    ax.set_title("EXP-045 stability score vs SE (selected family per cell)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_membership_summary(
    selections: list[dict], g2_met: bool, path: Path
) -> None:
    """Member counts by domain/instrument and the G2 readout headline."""
    members = [s for s in selections if s["member"]]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    dom_counts = {d: sum(1 for s in members if s["domain"] == d) for d in DOMAINS}
    axes[0].bar(list(dom_counts), list(dom_counts.values()), color="seagreen")
    axes[0].set_title("member cells by domain")
    inst_counts: dict[str, int] = {}
    for s in members:
        inst_counts[s["instrument"]] = inst_counts.get(s["instrument"], 0) + 1
    axes[1].bar(list(inst_counts), list(inst_counts.values()), color="steelblue")
    axes[1].tick_params(axis="x", rotation=70, labelsize=7)
    axes[1].set_title("member cells by instrument")
    fig.suptitle(
        f"EXP-045 membership: {len(members)} cells / "
        f"{len(inst_counts)} instruments — G2 composition "
        f"{'MET' if g2_met else 'NOT MET'} (P5: ≥{G2_MIN_CELLS} cells, "
        f"≥{G2_MIN_INSTRUMENTS} instruments)"
    )
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    """Run the 37-cell Track B exit training end to end (TRAIN-only)."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()
    cx.verify_mad_scan()
    cx.verify_financing()
    cells, boundaries = load_covered_cells()
    LOGGER.info("dependency gates PASS: %d COVERED cells (EXP-044) bound to "
                "EXP-043 boundaries", len(cells))

    selections, curves, halves = run_all_cells(
        cells, boundaries, f"EXP-045 exit training ({len(cells)} cells)")
    determinism_pass = determinism_replay(cells, boundaries, selections, curves)

    members = [s for s in selections if s["member"]]
    member_instruments = sorted({s["instrument"] for s in members})
    g2_met = (len(members) >= G2_MIN_CELLS
              and len(member_instruments) >= G2_MIN_INSTRUMENTS)
    complete = all(s["cell_verdict"] in ("MEMBER", "FLOOR_FAIL", "NON_TUNABLE")
                   for s in selections)
    verdict = ("TRAINING_DELIVERED" if complete and determinism_pass
               else "INCONCLUSIVE")

    pl.DataFrame(selections).write_csv(RESULTS_DIR / "exit_selection.csv")
    pl.DataFrame(curves).write_csv(RESULTS_DIR / "score_curves.csv")
    pl.DataFrame(halves).write_csv(RESULTS_DIR / "split_half.csv")
    membership_rows = [
        {"instrument": s["instrument"], "domain": s["domain"],
         "disclosure": s["disclosure"],
         "selected_family": s["selected_family"],
         "selected_theta": s["selected_theta"],
         "selected_s_bps": s["selected_s"], "selected_se_bps": s["selected_se"]}
        for s in members
    ]
    pl.DataFrame(
        membership_rows
        or {"instrument": [], "domain": [], "disclosure": [], "selected_family": [],
            "selected_theta": [], "selected_s_bps": [], "selected_se_bps": []}
    ).write_csv(RESULTS_DIR / "membership.csv")

    verdict_counts: dict[str, int] = {}
    for s in selections:
        verdict_counts[s["cell_verdict"]] = verdict_counts.get(s["cell_verdict"], 0) + 1
    metadata = {
        "experiment": EXPERIMENT_ID,
        "verdict": verdict,
        "determinism_pass": determinism_pass,
        "cell_verdict_counts": verdict_counts,
        "membership": {"n_cells": len(members),
                       "instruments": member_instruments,
                       "G2_COMPOSITION_MET": g2_met,
                       "g2_rule": f">= {G2_MIN_CELLS} cells over "
                                  f">= {G2_MIN_INSTRUMENTS} instruments (P5)"},
        "elapsed_seconds": round(time.perf_counter() - started, 1),
        "method": {
            "fh_grid": list(cx.FH_GRID),
            "mad_grid": list(cx.MAD_GRID),
            "neighbour_k": cx.NEIGHBOUR_K,
            "se_separation_mult": cx.SE_SEPARATION_MULT,
            "p4_floor_mult": cx.P4_FLOOR_MULT,
            "split_half_min_events": cx.SPLIT_HALF_MIN_EVENTS,
            "forced_close_disclosure_frac": cx.FORCED_CLOSE_DISCLOSURE_FRAC,
            "n_bootstrap": N_BOOT,
            "tie_breaks": "theta ties -> smaller theta; family ties -> FH",
            "cost_model": "D0 P2 CONSERVATIVE (EURUSD RT 3.0 correction)",
        },
        "dependency": {"exp044_verdict": "CALIBRATION_DELIVERED",
                       "covered_cells": len(cells)},
        "replay_cells": [f"{i}-{d}" for i, d in REPLAY_CELLS],
        "disclosures": {"DE30": DE30_DISCLOSURE},
        "holdout_fence": "F01 TRAIN rows only (first 70% of first 70%, file order); "
                         "TEST and global holdout never loaded",
        "test_reads": 0,
    }
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(metadata, indent=2))

    _plane_small_multiples(curves, cx.FAMILY_FH, selections,
                           PLOTS_DIR / "fh_stability_planes.png")
    _plane_small_multiples(curves, cx.FAMILY_MAD, selections,
                           PLOTS_DIR / "mad_stability_planes.png")
    plot_membership_map(selections, PLOTS_DIR / "exit_membership_map.png")
    plot_stability_vs_se(selections, PLOTS_DIR / "stability_vs_se.png")
    plot_membership_summary(selections, g2_met,
                            PLOTS_DIR / "membership_summary.png")

    LOGGER.info("verdict: %s; cells: %s; members=%d over %d instruments; "
                "G2_COMPOSITION_MET=%s; determinism_pass=%s",
                verdict, verdict_counts, len(members), len(member_instruments),
                g2_met, determinism_pass)
    LOGGER.info("outputs written under %s and %s", RESULTS_DIR, PLOTS_DIR)


if __name__ == "__main__":
    main()
