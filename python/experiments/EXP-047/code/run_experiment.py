"""EXP-047 — `/ANCHOR` move-size diagnostic (`CF-AVWAP-001/DIAG-007`).

Phase 013, TRAIN-only, gross-only, 0 slots, 0 TEST reads. For every cell of
the 17-instrument × {1h, 2h, 4h} grid this script:

1. enforces the P8 regression gate (pytest suite green) before any TRAIN read;
2. regenerates the frozen running-extreme baseline events and reconciles them
   against the EXP-043 realized counts and the EXP-046 baseline gross(H=8)
   rows (blocking integrity anchor, 1e-9 bps);
3. generates `/ANCHOR` ATR-prominence events (P1: ATR(14), k=1.0) and runs the
   G1a readiness checks (invariants, determinism replay, truncation
   look-ahead probe, ≥30-event floor);
4. on READY cells computes the gross lifetime MFE/MAE distributions for both
   anchors plus matched-control MFE, the P4 cost-floor reference, and the
   mechanical P5 SHIFTED_VIABLE classification.

Outputs: ``results/readiness_map.csv``, ``results/move_size_distributions.csv``,
``results/shift_classification.csv``, ``results/reconciliation.csv``,
``results/run_metadata.json`` and four plots under ``plots/``.
G1a/G1b adjudication is checkpoint desk work; nothing here is a TEST read.
"""
from __future__ import annotations

import json
import logging
import math
import subprocess
import sys
from datetime import datetime, timezone
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
CODE_DIR = Path(__file__).resolve().parent
EXPERIMENT_DIR = CODE_DIR.parent
PROJECT_ROOT = EXPERIMENT_DIR.parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "timebars"
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
EXP043_RESULTS = EXPERIMENT_DIR.parent / "EXP-043" / "results"
EXP046_RESULTS = EXPERIMENT_DIR.parent / "EXP-046" / "results"
TESTS_DIR = PROJECT_ROOT / "python" / "tests"

sys.path.insert(0, str(CODE_DIR))

import move_size as ms  # noqa: E402
from xen.avwap import generate_avwap_events  # noqa: E402
from xen.bar_aggregator import aggregate_ohlc  # noqa: E402

# --------------------------------------------------------------------------- #
# Constants (Phase 013 D0 / frozen Phase 011 conventions)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-047"
DOMAINS: dict[str, int] = {"1h": 60, "2h": 120, "4h": 240}
MIN_COVERAGE = 0.90
ANALYSIS_FRACTION = 0.7
TRAIN_FRACTION = 0.7
EXCLUDED_FILE_MARKERS = ("analysis70", "analysis_slice", "first70")
SEED = 47_013
N_PROBE_REGIMES_MIN = 3   # look-ahead truncation probes scale with sqrt(n_regimes)
LEG1_BORDERLINE_BAND = 0.25  # |ΔMFE − SE_diff| < band×SE_diff flags a brittle leg-1 call

# D0 P4 cost model (CONSERVATIVE RT bps, financing bps/day) — frozen Phase 011
# P2 table verbatim (incl. the EURUSD RT 3.0 correction).
COSTS: dict[str, tuple[float, float]] = {
    "EURUSD": (3.0, 0.6), "USTEC": (5.0, 1.2), "XAUUSD": (6.0, 1.2),
    "BTCUSD": (16.0, 10.0), "GBPUSD": (4.0, 0.8), "USDJPY": (3.6, 0.7),
    "USDCHF": (4.4, 0.7), "USDCAD": (4.4, 0.7), "AUDUSD": (4.0, 0.7),
    "NZDUSD": (5.2, 0.8), "EURJPY": (4.4, 0.8), "GBPJPY": (5.6, 1.0),
    "AUDJPY": (5.2, 0.9), "US500": (3.2, 1.2), "US2000": (6.0, 1.2),
    "DE30": (4.0, 1.2), "JP225": (4.8, 1.2),
}
DE30_DISCLOSURE = (
    "DE30 truncated history: broker history ends 2026-01-16; boundaries derive "
    "from its own realized timeline (VAL-003 disclosure)."
)

LOGGER = logging.getLogger(EXPERIMENT_ID)


# --------------------------------------------------------------------------- #
# I/O helpers (EXP-043/045/046 loader pattern, unchanged)
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
    """Load exactly the TRAIN 1-minute rows, bound to the EXP-043 boundaries."""
    path = find_source_file(instrument)
    if path.name != expected["source_file"]:
        raise RuntimeError(
            f"{instrument}: source file {path.name} != EXP-043 certified "
            f"{expected['source_file']}"
        )
    total = int(pl.scan_parquet(path).select(pl.len()).collect().item())
    if total != int(expected["total_rows_1m"]):
        raise RuntimeError(
            f"{instrument}: total rows {total} != EXP-043 {expected['total_rows_1m']}"
        )
    train_rows = int(math.floor(TRAIN_FRACTION * math.floor(ANALYSIS_FRACTION * total)))
    if train_rows != int(expected["train_rows_1m"]):
        raise RuntimeError(
            f"{instrument}: train rows {train_rows} != EXP-043 {expected['train_rows_1m']}"
        )
    frame = (
        pl.scan_parquet(path)
        .select("Symbol", "OpenTime", "CloseTime", "Open", "High", "Low", "Close", "TickVolume")
        .head(train_rows)
        .collect()
    )
    close_time = frame.get_column("CloseTime")
    if frame.height != train_rows or not close_time.is_sorted():
        raise RuntimeError(f"{instrument}: TRAIN slice not strictly chronological")
    if str(close_time.max()) != str(expected["train_end_ts"]):
        raise RuntimeError(
            f"{instrument}: TRAIN end {close_time.max()} != EXP-043 "
            f"{expected['train_end_ts']}"
        )
    return frame


def load_dependencies() -> tuple[dict[str, dict[str, Any]], dict, dict]:
    """EXP-043 boundaries + realized counts; EXP-046 baseline gross anchors."""
    meta43 = json.loads((EXP043_RESULTS / "run_metadata.json").read_text())
    boundaries: dict[str, dict[str, Any]] = meta43["boundaries"]
    power = pl.read_csv(EXP043_RESULTS / "power_statement.csv")
    counts = {
        (r["instrument"], r["domain"]): int(r["train_events"])
        for r in power.to_dicts()
    }
    clearance = pl.read_csv(EXP046_RESULTS / "clearance_table.csv")
    base46 = {
        (r["instrument"], r["domain"]): (int(r["n_evaluable"]), float(r["gross_h8_bps"]))
        for r in clearance.filter(pl.col("variant") == "baseline").to_dicts()
    }
    return boundaries, counts, base46


def run_p8_regression_gate() -> str:
    """P8 data-contact gate: the anchor regression suite must be green before
    the first TRAIN read. Hard-fails on any test failure."""
    cmd = [
        sys.executable, "-m", "pytest", "-q",
        str(TESTS_DIR / "test_avwap_band_param.py"),
        str(TESTS_DIR / "test_avwap_anchor_param.py"),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT / "python")
    summary = (proc.stdout.strip().splitlines() or ["<no output>"])[-1]
    if proc.returncode != 0:
        raise RuntimeError(f"P8 regression gate RED — aborting before TRAIN read:\n"
                           f"{proc.stdout}\n{proc.stderr}")
    return summary


# --------------------------------------------------------------------------- #
# Pure checks / per-cell computation
# --------------------------------------------------------------------------- #
def invariant_violations(result, bars: pl.DataFrame) -> list[str]:
    """EXP-020 invariant set, anchor-adapted, for one cell's `/ANCHOR` run."""
    out: list[str] = []
    ev, rg = result.events, result.regimes
    low = bars.get_column("Low").to_numpy()
    high = bars.get_column("High").to_numpy()
    if ev.height:
        t = ev.get_column("trigger_idx").to_numpy()
        if not np.all(np.diff(t) > 0):
            out.append("trigger_idx not strictly increasing")
        d = ev.get_column("direction").to_numpy()
        c = ev.get_column("trigger_close").to_numpy()
        a = ev.get_column("avwap_at_trigger").to_numpy()
        if not np.all(np.where(d == 1, c > a, c < a)):
            out.append("trigger close on wrong side of AVWAP")
        if not (ev.get_column("armed_time") < ev.get_column("trigger_time")).all():
            out.append("armed_time not before trigger_time")
    for r in rg.to_dicts():
        ai, ci, d = int(r["anchor_idx"]), int(r["confirm_idx"]), int(r["direction"])
        if ai > ci:
            out.append(f"regime {r['regime_id']}: anchor after confirmation bar")
            break
        realized = low[ai] if d == 1 else high[ai]
        if float(r["anchor_price"]) != float(realized):
            out.append(f"regime {r['regime_id']}: anchor price not a realized extreme")
            break
    return out


def lookahead_probe(bars: pl.DataFrame, full_regimes: pl.DataFrame) -> bool:
    """Bounded truncation probe (a spot-check, not exhaustive — the structural
    guarantee is pinned by the P8 suite): regenerating on a prefix ending at a
    sampled regime-confirmation bar must reproduce that regime's anchor
    selection. Probe count scales as ``max(3, isqrt(n_regimes))``, sampled
    evenly across the regime sequence."""
    rg = full_regimes.sort("confirm_idx")
    if rg.height == 0:
        return True
    n_probes = min(rg.height, max(N_PROBE_REGIMES_MIN, math.isqrt(rg.height)))
    picks = sorted({round(p * (rg.height - 1) / max(n_probes - 1, 1))
                    for p in range(n_probes)})
    cols = ["direction", "confirm_idx", "anchor_idx", "anchor_price", "anchor_fallback"]
    for p in picks:
        row = rg.row(p, named=True)
        prefix = int(row["confirm_idx"]) + 1
        part = generate_avwap_events(
            bars.head(prefix), instrument="probe", domain="probe",
            anchor_mode="atr_prominence",
        )
        # The probed regime is the last (still-open) regime of the prefix run.
        if part.regimes.height == 0:
            return False
        got = part.regimes.sort("confirm_idx").row(part.regimes.height - 1, named=True)
        if any(got[c] != row[c] for c in cols):
            return False
    return True


def arm_statistics(
    result, bars: pl.DataFrame, rng: np.random.Generator, with_controls: bool
) -> dict[str, Any]:
    """Lifetime MFE/MAE distribution summary for one cell × anchor arm."""
    ev = result.events
    rg = result.regimes.sort("confirm_idx")
    high = bars.get_column("High").to_numpy().astype(float)
    low = bars.get_column("Low").to_numpy().astype(float)
    close = bars.get_column("Close").to_numpy().astype(float)
    n = bars.height
    trigger_idx = ev.get_column("trigger_idx").to_numpy()
    direction = ev.get_column("direction").to_numpy()
    confirm = rg.get_column("confirm_idx").to_numpy()
    end_idx, censored = ms.lifetime_end(trigger_idx, confirm, n)
    mfe, mae = ms.excursions(
        high, low, close[trigger_idx], trigger_idx, end_idx, direction
    )
    lifetime_bars = (end_idx - trigger_idx).astype(float)
    out: dict[str, Any] = {
        "n_events": int(ev.height),
        "median_mfe_bps": float(np.median(mfe)) if mfe.size else float("nan"),
        "iqr_mfe_bps": float(np.subtract(*np.percentile(mfe, [75, 25]))) if mfe.size else float("nan"),
        "se_median_mfe_bps": ms.bootstrap_median_se(mfe, rng),
        "median_mae_bps": float(np.median(mae)) if mae.size else float("nan"),
        "se_median_mae_bps": ms.bootstrap_median_se(mae, rng),
        "median_lifetime_bars": float(np.median(lifetime_bars)) if lifetime_bars.size else float("nan"),
        "censored_fraction": float(censored.mean()) if censored.size else float("nan"),
        "fallback_rate": (
            float(ev.get_column("anchor_fallback").mean()) if ev.height else float("nan")
        ),
        "_mfe": mfe,
        "_mae": mae,
    }
    if with_controls and ev.height:
        cb, ce, cd = ms.matched_controls(
            rg, ev.get_column("regime_id").to_numpy(), trigger_idx, n
        )
        if cb.size:
            cmfe, _ = ms.excursions(high, low, close[cb], cb, ce, cd)
            out["control_median_mfe_bps"] = float(np.median(cmfe))
            out["n_controls"] = int(cb.size)
        else:
            out["control_median_mfe_bps"] = float("nan")
            out["n_controls"] = 0
    return out


def process_cell(
    instrument: str,
    domain: str,
    frame_1m: pl.DataFrame,
    counts43: dict,
    base46: dict,
) -> dict[str, Any]:
    """Run both anchor arms for one cell: reconciliation, readiness, stats,
    classification inputs. Returns a dict of row fragments."""
    bars = aggregate_ohlc(
        frame_1m, period_minutes=DOMAINS[domain], min_coverage=MIN_COVERAGE
    ).select("CloseTime", "Open", "High", "Low", "Close", "TickVolume")
    rng = np.random.default_rng(
        SEED + 1000 * sorted(COSTS).index(instrument) + list(DOMAINS).index(domain)
    )
    disclosure = DE30_DISCLOSURE if instrument == "DE30" else ""

    base_a = generate_avwap_events(bars, instrument=instrument, domain=domain)
    base_b = generate_avwap_events(bars, instrument=instrument, domain=domain)
    base_det = base_a.events.equals(base_b.events) and base_a.regimes.equals(base_b.regimes)

    anc_a = generate_avwap_events(
        bars, instrument=instrument, domain=domain, anchor_mode="atr_prominence"
    )
    anc_b = generate_avwap_events(
        bars, instrument=instrument, domain=domain, anchor_mode="atr_prominence"
    )
    anc_det = anc_a.events.equals(anc_b.events) and anc_a.regimes.equals(anc_b.regimes)

    # Reconciliation legs (baseline arm only; blocking).
    recon_rows: list[dict] = []
    key = (instrument, domain)
    if key in counts43:
        recon_rows.append({
            "instrument": instrument, "domain": domain,
            "check": "baseline_event_count_vs_EXP043",
            "ours": float(base_a.events.height), "theirs": float(counts43[key]),
            "pass": base_a.events.height == counts43[key],
        })
    if key in base46:
        n_eval, g_h8 = ms.recon_gross_h8(
            bars.get_column("Close").to_numpy().astype(float),
            base_a.events.get_column("trigger_idx").to_numpy(),
            base_a.events.get_column("direction").to_numpy(),
        )
        recon_rows.append({
            "instrument": instrument, "domain": domain,
            "check": "baseline_evaluable_count_vs_EXP046",
            "ours": float(n_eval), "theirs": float(base46[key][0]),
            "pass": n_eval == base46[key][0],
        })
        recon_rows.append({
            "instrument": instrument, "domain": domain,
            "check": "baseline_gross_h8_vs_EXP046",
            "ours": g_h8, "theirs": base46[key][1],
            "pass": bool(abs(g_h8 - base46[key][1]) <= ms.RECON_TOL_BPS),
        })

    # G1a readiness (/ANCHOR arm).
    violations = invariant_violations(anc_a, bars)
    probe_ok = lookahead_probe(bars, anc_a.regimes)
    n_anchor = anc_a.events.height
    fail_reasons = []
    if violations:
        fail_reasons.append("invariants:" + ";".join(violations[:2]))
    if not anc_det:
        fail_reasons.append("determinism")
    if not probe_ok:
        fail_reasons.append("look_ahead_probe")
    if n_anchor < ms.EVENT_FLOOR:
        fail_reasons.append(f"event_floor({n_anchor}<{ms.EVENT_FLOOR})")
    ready = not fail_reasons
    readiness_row = {
        "instrument": instrument, "domain": domain, "disclosure": disclosure,
        "n_anchor_events": n_anchor, "n_baseline_events": base_a.events.height,
        "invariant_violations": len(violations),
        "determinism_pass": anc_det and base_det,
        "lookahead_probe_pass": probe_ok,
        "verdict": "READY" if ready else "NOT_READY",
        "failing_checks": ";".join(fail_reasons),
        "anchor_events_digest": ms.events_digest(anc_a.events),
    }

    dist_rows: list[dict] = []
    shift_row: dict | None = None
    if ready:
        stats_anchor = arm_statistics(anc_a, bars, rng, with_controls=True)
        stats_base = arm_statistics(base_a, bars, rng, with_controls=True)
        rt, fin = COSTS[instrument]
        floor_anchor = ms.cost_floor_bps(rt, fin, domain, stats_anchor["median_lifetime_bars"])
        floor_base = ms.cost_floor_bps(rt, fin, domain, stats_base["median_lifetime_bars"])
        # Conservative binding floor: the max of the two arms' lifetime-derived
        # floors, so a lifetime shift cannot soften P5 leg 2 (both disclosed).
        floor_binding = max(floor_anchor, floor_base)
        se_diff = ms.bootstrap_median_diff_se(stats_anchor["_mfe"], stats_base["_mfe"], rng)
        for arm, st, fl in (("anchor", stats_anchor, floor_anchor),
                            ("baseline", stats_base, floor_base)):
            row = {k: v for k, v in st.items() if not k.startswith("_")}
            row.update({"instrument": instrument, "domain": domain, "arm": arm,
                        "disclosure": disclosure, "floor_bps": fl,
                        "floor_binding_bps": floor_binding})
            dist_rows.append(row)
        d_mfe = stats_anchor["median_mfe_bps"] - stats_base["median_mfe_bps"]
        d_mae = stats_anchor["median_mae_bps"] - stats_base["median_mae_bps"]
        verdict, legs = ms.shift_verdict(
            n_anchor=n_anchor,
            median_mfe_anchor=stats_anchor["median_mfe_bps"],
            median_mfe_base=stats_base["median_mfe_bps"],
            se_diff=se_diff,
            floor_bps=floor_binding,
            delta_median_mae=d_mae,
            delta_median_mfe=d_mfe,
            determinism_pass=anc_det,
        )
        leg1_margin = d_mfe - ms.SE_MULT * se_diff
        shift_row = {
            "instrument": instrument, "domain": domain, "disclosure": disclosure,
            "n_anchor": n_anchor, "n_baseline": base_a.events.height,
            "median_mfe_anchor_bps": stats_anchor["median_mfe_bps"],
            "median_mfe_baseline_bps": stats_base["median_mfe_bps"],
            "se_diff_bps": se_diff,
            "delta_median_mfe_bps": d_mfe, "delta_median_mae_bps": d_mae,
            "leg1_margin_bps": leg1_margin,
            "leg1_borderline": bool(
                np.isfinite(se_diff) and se_diff > 0
                and abs(leg1_margin) < LEG1_BORDERLINE_BAND * se_diff
            ),
            "floor_binding_bps": floor_binding,
            "floor_anchor_arm_bps": floor_anchor,
            "floor_baseline_arm_bps": floor_base,
            "floor_multiple_required": ms.FLOOR_MULTIPLE_M,
            "fallback_rate": stats_anchor["fallback_rate"],
            **legs, "verdict": verdict,
        }
    return {
        "readiness": readiness_row,
        "reconciliation": recon_rows,
        "distributions": dist_rows,
        "shift": shift_row,
    }


# --------------------------------------------------------------------------- #
# Plotting (consumes summary tables only)
# --------------------------------------------------------------------------- #
def plot_mfe_vs_floor(dist: pl.DataFrame, path: Path) -> None:
    """Per-domain MFE-median vs floor panels, baseline vs /ANCHOR."""
    fig, axes = plt.subplots(1, 3, figsize=(16, 5), sharey=False)
    for ax, dom in zip(axes, DOMAINS):
        sub = dist.filter(pl.col("domain") == dom).sort("instrument")
        insts = sorted(sub.get_column("instrument").unique().to_list())
        x = np.arange(len(insts))
        for arm, off, color in (("baseline", -0.15, "tab:gray"), ("anchor", 0.15, "tab:blue")):
            rows = {r["instrument"]: r for r in sub.filter(pl.col("arm") == arm).to_dicts()}
            y = [rows[i]["median_mfe_bps"] if i in rows else np.nan for i in insts]
            e = [rows[i]["se_median_mfe_bps"] if i in rows else np.nan for i in insts]
            f2 = [ms.FLOOR_MULTIPLE_M * rows[i]["floor_binding_bps"] if i in rows else np.nan for i in insts]
            ax.errorbar(x + off, y, yerr=e, fmt="o", ms=4, color=color, label=arm)
            if arm == "anchor":
                ax.scatter(x + off, f2, marker="_", s=200, color="tab:red",
                           label="2×floor (P5 leg 2)")
        ax.set_title(f"{dom}: median lifetime MFE vs floor")
        ax.set_xticks(x, insts, rotation=90, fontsize=7)
        ax.set_ylabel("bps")
        ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_shift_scatter(shift: pl.DataFrame, path: Path) -> None:
    """MFE shift vs MAE shift per READY cell (P5 legs 1 and 3 jointly)."""
    fig, ax = plt.subplots(figsize=(7, 6))
    colors = {"1h": "tab:blue", "2h": "tab:orange", "4h": "tab:green"}
    for dom, c in colors.items():
        sub = shift.filter(pl.col("domain") == dom)
        ax.scatter(sub.get_column("delta_median_mfe_bps"),
                   sub.get_column("delta_median_mae_bps"),
                   s=25, color=c, label=dom)
    lim = max(abs(v) for col in ("delta_median_mfe_bps", "delta_median_mae_bps")
              for v in shift.get_column(col).to_list() if v is not None and np.isfinite(v))
    lim = lim * 1.1 if np.isfinite(lim) and lim > 0 else 1.0
    ax.plot([-lim, lim], [-lim, lim], ls="--", color="gray", lw=1,
            label="ΔMAE = ΔMFE (leg-3 boundary)")
    ax.axvline(0, color="black", lw=0.5)
    ax.axhline(0, color="black", lw=0.5)
    ax.set_xlabel("Δ median MFE (anchor − baseline, bps)")
    ax.set_ylabel("Δ median MAE (anchor − baseline, bps)")
    ax.set_title("/ANCHOR shift: favorable vs adverse")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_readiness_map(readiness: pl.DataFrame, shift: pl.DataFrame, path: Path) -> None:
    """READY/fallback-rate grid map (17 × 3)."""
    insts = sorted(readiness.get_column("instrument").unique().to_list())
    doms = list(DOMAINS)
    grid = np.full((len(insts), len(doms)), np.nan)
    fb = {(r["instrument"], r["domain"]): r["fallback_rate"] for r in shift.to_dicts()}
    ready = {(r["instrument"], r["domain"]): r["verdict"] == "READY"
             for r in readiness.to_dicts()}
    for i, inst in enumerate(insts):
        for j, dom in enumerate(doms):
            if ready.get((inst, dom)):
                grid[i, j] = fb.get((inst, dom), np.nan)
    fig, ax = plt.subplots(figsize=(5, 9))
    im = ax.imshow(grid, vmin=0, vmax=1, cmap="viridis", aspect="auto")
    for i, inst in enumerate(insts):
        for j, dom in enumerate(doms):
            if not ready.get((inst, dom)):
                ax.text(j, i, "NR", ha="center", va="center", color="red", fontsize=7)
    ax.set_xticks(range(len(doms)), doms)
    ax.set_yticks(range(len(insts)), insts, fontsize=7)
    fig.colorbar(im, ax=ax, label="/ANCHOR fallback rate (NR = NOT_READY)")
    ax.set_title("G1a readiness and fallback rate")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_control_context(dist: pl.DataFrame, path: Path) -> None:
    """Event-MFE shift vs matched-control-MFE shift per READY cell."""
    fig, ax = plt.subplots(figsize=(7, 6))
    cells: dict[tuple[str, str], dict[str, dict]] = {}
    for r in dist.to_dicts():
        cells.setdefault((r["instrument"], r["domain"]), {})[r["arm"]] = r
    colors = {"1h": "tab:blue", "2h": "tab:orange", "4h": "tab:green"}
    for (inst, dom), arms in cells.items():
        if "anchor" not in arms or "baseline" not in arms:
            continue
        ev_shift = arms["anchor"]["median_mfe_bps"] - arms["baseline"]["median_mfe_bps"]
        ct_shift = (arms["anchor"].get("control_median_mfe_bps", np.nan)
                    - arms["baseline"].get("control_median_mfe_bps", np.nan))
        ax.scatter(ev_shift, ct_shift, s=25, color=colors[dom])
    handles = [plt.Line2D([], [], marker="o", ls="", color=c, label=d)
               for d, c in colors.items()]
    ax.axvline(0, color="black", lw=0.5)
    ax.axhline(0, color="black", lw=0.5)
    ax.set_xlabel("Δ event median MFE (anchor − baseline, bps)")
    ax.set_ylabel("Δ matched-control median MFE (bps)")
    ax.set_title("Volatility-sampling context (controls vs events)")
    ax.legend(handles=handles, fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    p8_summary = run_p8_regression_gate()
    LOGGER.info("P8 regression gate green: %s", p8_summary)

    boundaries, counts43, base46 = load_dependencies()
    instruments = sorted(COSTS)
    missing = set(instruments) - set(boundaries)
    if missing:
        raise RuntimeError(f"EXP-043 boundaries missing instruments: {sorted(missing)}")

    readiness_rows: list[dict] = []
    recon_rows: list[dict] = []
    dist_rows: list[dict] = []
    shift_rows: list[dict] = []
    for instrument in tqdm(instruments, desc="instruments"):
        frame_1m = load_train_frame(instrument, boundaries[instrument])
        for domain in DOMAINS:
            cell = process_cell(instrument, domain, frame_1m, counts43, base46)
            readiness_rows.append(cell["readiness"])
            recon_rows.extend(cell["reconciliation"])
            dist_rows.extend(cell["distributions"])
            if cell["shift"] is not None:
                shift_rows.append(cell["shift"])
        del frame_1m

    recon_fail = [r for r in recon_rows if not r["pass"]]
    readiness = pl.DataFrame(readiness_rows)
    dist = pl.DataFrame(dist_rows)
    shift = pl.DataFrame(shift_rows)
    readiness.write_csv(RESULTS_DIR / "readiness_map.csv")
    pl.DataFrame(recon_rows).write_csv(RESULTS_DIR / "reconciliation.csv")
    dist.write_csv(RESULTS_DIR / "move_size_distributions.csv")
    shift.write_csv(RESULTS_DIR / "shift_classification.csv")

    if shift.height:
        plot_mfe_vs_floor(dist, PLOTS_DIR / "mfe_vs_floor_by_domain.png")
        plot_shift_scatter(shift, PLOTS_DIR / "mfe_mae_shift_scatter.png")
        plot_readiness_map(readiness, shift, PLOTS_DIR / "readiness_fallback_map.png")
        plot_control_context(dist, PLOTS_DIR / "matched_control_context.png")

    composition = ms.composition_readout(shift_rows)
    integrity_clean = not recon_fail
    reconciled = {(r["instrument"], r["domain"]) for r in recon_rows}
    unreconciled_cells = sorted(
        f"{r['instrument']}-{r['domain']}" for r in readiness_rows
        if (r["instrument"], r["domain"]) not in reconciled
    )
    metadata = {
        "experiment": EXPERIMENT_ID,
        "registry": "CF-AVWAP-001/DIAG-007",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "p8_regression_gate": p8_summary,
        "anchor_rule": {
            "mode": "atr_prominence", "atr_period": ms.ANCHOR_ATR_PERIOD,
            "k": ms.ANCHOR_PROMINENCE_K, "tie_break": "most_extreme_then_most_recent",
            "fallback": "running_extreme",
        },
        "cost_model": "Phase 011 P2 CONSERVATIVE (frozen, reference line only)",
        "n_cells": len(readiness_rows),
        "n_ready": int((readiness.get_column("verdict") == "READY").sum()),
        "reconciliation_failures": len(recon_fail),
        "integrity_clean": integrity_clean,
        # Cells with no external reconciliation anchor (not in the EXP-043
        # power statement / EXP-046 baseline rows): their baseline integrity
        # rests on code-path identity + the P8 regression suite only.
        "unreconciled_cells": unreconciled_cells,
        "g1b_input": composition,
        "verdict": (
            "DIAGNOSTIC_DELIVERED" if integrity_clean else "INTEGRITY_FAIL"
        ),
        "test_reads": 0,
        "holdout_reads": 0,
    }
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(metadata, indent=2))

    LOGGER.info("cells: %d | READY: %d | reconciliation failures: %d",
                metadata["n_cells"], metadata["n_ready"], len(recon_fail))
    LOGGER.info("G1b input: %s", composition)
    LOGGER.info("verdict: %s", metadata["verdict"])
    if recon_fail:
        for r in recon_fail[:10]:
            LOGGER.info("RECON FAIL %s-%s %s: ours=%s theirs=%s",
                        r["instrument"], r["domain"], r["check"], r["ours"], r["theirs"])


if __name__ == "__main__":
    main()
