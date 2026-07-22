#!/usr/bin/env python3
"""XENA-HTFCAP-001 re-analysis under the INFR-016 report-layer framework.

Reuses the VALID emitted parquet (engine runs ONLY at emission — no re-emission). Every
value / quality / significance read is re-expressed as a **report layer**
(`observed / ideal / interpretation` per candidate, no pass/fail) via
`xen.xena.report_layer` + `xen.xena.controls`. Nothing is machine-dropped; ALL authorised
candidates are reported (BTC+SOL binding verdict-bearing; ETH disclosure-only). Retired:
`one_subset` top-1 hiding (stage-2 per-cell + per-subset), `n_legs_floor` veto (power layer),
`at_or_above_p95` boolean (≥2000-seed sign battery with effect+p+CI), derangement
`hard_fail_leak` (reported collapse fraction). HARD data-VALIDITY attestations stay separate
(estimand recon, fence, cadence, pin, boundary trim) and are emitted as an attestation block.

Usage (from python/):
  uv run python experiments/XENA-HTFCAP-001/analysis_code/reframe_layers.py
"""
from __future__ import annotations

import json
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

CODE = Path(__file__).resolve().parents[1] / "code"
EXP = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]  # python/
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

from xen.nautilus.adjudication_shim import emission_to_adjudication_frames  # noqa: E402
from xen.xena.calibration_p3d import eval_lcb_legs  # noqa: E402
from xen.xena.controls import (  # noqa: E402
    DEFAULT_DERANGE_SEEDS,
    DEFAULT_SIGN_BATTERY_SEEDS,
    attribution_derangement,
    sign_battery,
)
from xen.xena.ingest import load_universe  # noqa: E402
from xen.xena.oracle import OracleConfig  # noqa: E402
from xen.xena.report_layer import LayerReport, power_layer, render_all_layers  # noqa: E402

UNIVERSE_ID = "XENA-HTFCAP-001"
RUNS_ROOT = REPO / "data" / "nautilus_runs" / UNIVERSE_ID
RESULTS = EXP / "results"
ARCHIVE = EXP / "archive" / "pre-infr016"
SEARCH_MANIFEST = RUNS_ROOT / "search_manifest_binding.json"
STAGE_BANDS = RESULTS / "stage_bands.json"
FLOOR_CSV = ARCHIVE / "pre_search_gross_floor.csv"       # reused emission fact (validity kept)
SEARCH_PKG = ARCHIVE / "search_certify_package.json"     # reused search terminals (deterministic)
MANIFEST = RUNS_ROOT / "universe_manifest.json"

LTF_NS = 15 * 60 * 1_000_000_000
NS_PER_MIN = 60 * 1_000_000_000
MIN_BLOCK_LTF = 64          # design §8: ≥ max hold H (64×15m = 16h)
BREAKEVEN_LABEL = "measured taker+GAP ≈ 13–15 bps (SPDR-006 money floor)"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# --------------------------------------------------------------------------- #
# leg / grid extraction (index math only — no accounting; L-18 clean)
# --------------------------------------------------------------------------- #
def load_live_legs(cid: str) -> pl.DataFrame:
    pos, cis, _meta = emission_to_adjudication_frames(RUNS_ROOT / cid)
    live = cis.filter(
        pl.col("Censored").cast(pl.Boolean).not_() & pl.col("RealizedBps").is_finite()
    ).sort("EntryTime")
    return live


def load_marks(cid: str) -> pl.DataFrame:
    pos, _cis, _meta = emission_to_adjudication_frames(RUNS_ROOT / cid)
    return pos


def build_15m_open_grid(marks: pl.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    m = marks.sort("SourceCloseTime")
    close_ns = m.get_column("SourceCloseTime").cast(pl.Datetime("ns")).cast(pl.Int64).to_numpy()
    real_open = m.get_column("RealOpen").to_numpy().astype(float)
    open_by_close = {int(c): float(o) for c, o in zip(close_ns, real_open)}
    one_min_open = close_ns - NS_PER_MIN
    boundaries = np.unique((one_min_open // LTF_NS) * LTF_NS)
    grid_ns, grid_open = [], []
    for b in boundaries:
        o = open_by_close.get(int(b) + NS_PER_MIN)
        if o is not None and np.isfinite(o) and o > 0:
            grid_ns.append(int(b))
            grid_open.append(float(o))
    return np.asarray(grid_ns, dtype=np.int64), np.asarray(grid_open, dtype=float)


def derangement_inputs(legs: pl.DataFrame, grid_ns: np.ndarray, grid_open: np.ndarray):
    """Build (entry_idx, block_id, block_edges, n_blocks, direction, hold_bars) on the 15m grid."""
    et = legs.get_column("EntryTime").cast(pl.Datetime("ns"))
    d = legs.get_column("Direction").to_numpy().astype(float)
    hold_ns = (legs.get_column("ExitTime").cast(pl.Datetime("ns")).cast(pl.Int64)
               - et.cast(pl.Int64)).to_numpy()
    hold_bars = np.maximum(1, np.rint(hold_ns / LTF_NS).astype(int))
    n_grid = len(grid_ns)
    entry_ns = et.cast(pl.Int64).to_numpy()
    entry_idx = np.clip(np.searchsorted(grid_ns, entry_ns, side="left"), 0, n_grid - 1)
    for i, e in enumerate(entry_ns):
        j = int(entry_idx[i])
        if j > 0 and abs(grid_ns[j - 1] - e) < abs(grid_ns[j] - e):
            entry_idx[i] = j - 1
    n_blocks = max(2, n_grid // MIN_BLOCK_LTF)
    block_edges = np.linspace(0, n_grid, n_blocks + 1, dtype=int)
    block_id = np.clip(np.searchsorted(block_edges[1:], entry_idx, side="right"), 0, n_blocks - 1)
    return entry_idx, block_id, block_edges, n_blocks, d, hold_bars


# --------------------------------------------------------------------------- #
# stage-2 (report layer, gross+net, per-cell AND per-subset — retires one_subset)
# --------------------------------------------------------------------------- #
def _bounds(res: dict) -> dict[str, Any]:
    lcb = res.get("lcb")
    point = res.get("point")
    se = res.get("se")
    t_crit = res.get("t_crit")
    ucb = (point + t_crit * se) if None not in (point, t_crit, se) else None
    return {"lcb": lcb, "point": point, "se": se, "ucb": ucb,
            "n_legs": int(res.get("n_legs") or 0), "t_crit": t_crit}


def stage2_layer(cid: str, gross: dict, net: dict) -> list[LayerReport]:
    out = []
    for scale, b in (("gross", gross), ("net", net)):
        lcb, point, se, ucb, n = b["lcb"], b["point"], b["se"], b["ucb"], b["n_legs"]
        directional = lcb is not None and lcb > 0
        lo = f"{lcb:.1f}" if lcb is not None else "n/a"
        hi = f"{ucb:.1f}" if ucb is not None else "n/a"
        pt = f"{point:.1f}" if point is not None else "n/a"
        sestr = f"{se:.1f}" if se is not None else "n/a"
        interp = (f"{scale} point {pt} bps, 95% LCB {lo} (UCB {hi}), se {sestr}, {n} legs — "
                  + ("lower band above zero" if directional else
                     "lower band spans/below zero — edge not resolved above zero on the "
                     "embargoed band"))
        out.append(LayerReport(
            layer=f"stage2_{scale}", candidate_id=cid,
            observed=f"point {pt}, LCB {lo}, se {sestr}, n={n}",
            ideal_range="LCB above zero at the traded scale on the embargoed band",
            interpretation=interp, interpretation_label=None,
            supporting={"scale": scale, "lcb": lcb, "point": point, "se": se, "ucb": ucb,
                        "n_legs": n, "band": "embargoed stage-2 gate (2024-07-10→2025-01-08)",
                        "note": "reported for ALL cells + subsets (retires one_subset top-1)"}))
    return out


# --------------------------------------------------------------------------- #
def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cands = manifest["candidates"]
    binding = [c for c in cands if c.get("role") == "binding"]
    disclosure = [c for c in cands if c.get("role") == "disclosure"]
    bands = json.loads(STAGE_BANDS.read_text(encoding="utf-8"))
    gate_seg = (int(bands["stage2_gate"]["start_ns"]), int(bands["stage2_gate"]["end_ns"]))
    floor = pl.read_csv(FLOOR_CSV)
    floor_by_cid = {r["candidate_id"]: r for r in floor.to_dicts()}
    pkg = json.loads(SEARCH_PKG.read_text(encoding="utf-8"))

    reports: list[LayerReport] = []
    rich: dict[str, Any] = {"stage2": {}, "sign_battery": {}, "derangement": {}, "power": {}}

    # ---- Layer: cost floor & breakeven (per cell, all 108) ----
    print("[layer] cost_floor …", flush=True)
    for c in cands:
        cid = c["candidate_id"]
        fr = floor_by_cid.get(cid)
        if fr is None:
            continue
        mg, be = fr["median_gross_bps"], fr["breakeven_bps"]
        role = c["role"]
        interp = (f"median gross {mg:.1f} bps/trade vs breakeven ~{be:.0f} bps — "
                  + ("clears cost floor" if mg >= be else "below cost floor")
                  + ("" if role == "binding" else "  [ETH disclosure-only]"))
        reports.append(LayerReport(
            layer="cost_floor", candidate_id=cid,
            observed=f"gross {mg:.1f} bps, breakeven {be:.0f} bps",
            ideal_range=f"median gross ≥ breakeven ({BREAKEVEN_LABEL})",
            interpretation=interp, interpretation_label=None,
            supporting={"role": role, "median_gross_bps": mg, "breakeven_bps": be,
                        "hold_hours": fr["hold_hours"], "n_legs_full": fr["n_legs"]}))

    # ---- Layer: leg power (per cell, all 108) — retires n_legs_floor veto ----
    print("[layer] leg_power …", flush=True)
    for c in cands:
        cid = c["candidate_id"]
        legs = load_live_legs(cid)
        if legs.height == 0:
            continue
        d = legs.get_column("Direction").to_numpy().astype(float)
        ep = legs.get_column("EntryFillPrice").to_numpy().astype(float)
        xp = legs.get_column("ExitFillPrice").to_numpy().astype(float)
        raw = d * (xp - ep) / ep * 1e4
        n = int(len(raw))
        vol = float(np.std(raw, ddof=1)) if n > 1 else float("nan")
        med = float(np.median(raw))
        mde = float(1.96 * vol / np.sqrt(n)) if n > 0 and np.isfinite(vol) else float("nan")
        rep = power_layer(cid, n_legs=n, per_leg_vol_bps=vol, mde_bps=mde,
                          observed_edge_bps=med)
        reports.append(rep)
        rich["power"][cid] = {"n_legs_full": n, "per_leg_vol_bps": vol,
                              "median_gross_bps": med, "mde_bps": mde, "role": c["role"]}

    # ---- Layer: search / ranking-fold stability (all 10 ranked subsets) ----
    print("[layer] search_fold …", flush=True)
    disp = pkg["certify"].get("dispersion", {})
    for r in pkg["certify"]["ranked"]:
        sub = r["subset"]
        sid = " + ".join(s.split("__")[0] + ":" + "/".join(s.split("__")[2:]) for s in sub) \
            if len(sub) <= 3 else f"{len(sub)}-cell subset"
        stable = r["worst_F"] > 0
        interp = (f"search F {r['search_F_hat']:.1f} → ranking median F {r['median_F']:.1f}, "
                  f"worst-fold F {r['worst_F']:.1f} — "
                  + ("holds across folds" if stable else
                     "collapses out-of-search-band (worst-fold F negative)"))
        reports.append(LayerReport(
            layer="search_fold", candidate_id=sid,
            observed=f"searchF {r['search_F_hat']:.1f}, medF {r['median_F']:.1f}, "
                     f"worstF {r['worst_F']:.1f}",
            ideal_range="worst-fold F > 0 and shared structure across folds (stable selection)",
            interpretation=interp, interpretation_label=None,
            supporting={"subset": sub, "search_F_hat": r["search_F_hat"],
                        "median_F": r["median_F"], "worst_F": r["worst_F"],
                        "fold_F": r["fold_F"]}))

    # ---- Layer: stage-2 bounds (per binding cell + per ranked subset) — retires one_subset ----
    print("[layer] stage2 (load_universe) …", flush=True)
    uni = load_universe(SEARCH_MANIFEST)
    streams = uni.streams
    config = OracleConfig(charge_costs=True)
    n_boot = 200

    def eval_subset(subset: frozenset) -> dict:
        g = eval_lcb_legs(subset, streams, config, gate_seg, n_boot=n_boot, seed=42, block_legs=1,
                          net=False)
        nn = eval_lcb_legs(subset, streams, config, gate_seg, n_boot=n_boot, seed=59, block_legs=1,
                           net=True)
        return {"gross": _bounds(g), "net": _bounds(nn)}

    for c in binding:
        cid = c["candidate_id"]
        b = eval_subset(frozenset({cid}))
        rich["stage2"][cid] = b
        reports.extend(stage2_layer(cid, b["gross"], b["net"]))
        print(f"    cell {cid}: gross LCB {b['gross']['lcb']} n {b['gross']['n_legs']}", flush=True)

    for i, r in enumerate(pkg["certify"]["ranked"]):
        sub = frozenset(r["subset"])
        sid = f"SUBSET#{i+1}({len(sub)}cell)"
        b = eval_subset(sub)
        rich["stage2"][sid] = {"members": sorted(sub), **b}
        reports.extend(stage2_layer(sid, b["gross"], b["net"]))
        print(f"    {sid}: gross LCB {b['gross']['lcb']} n {b['gross']['n_legs']}", flush=True)

    # ---- Layer: sign battery (≥2000 seeds) per binding cell — retires at_or_above_p95 ----
    print(f"[layer] sign_battery ({DEFAULT_SIGN_BATTERY_SEEDS} seeds) …", flush=True)
    for c in binding:
        cid = c["candidate_id"]
        legs = load_live_legs(cid)
        if legs.height == 0:
            continue
        d = legs.get_column("Direction").to_numpy().astype(float)
        ep = legs.get_column("EntryFillPrice").to_numpy().astype(float)
        xp = legs.get_column("ExitFillPrice").to_numpy().astype(float)
        rep = sign_battery(d, ep, xp, candidate_id=cid)
        reports.append(rep)
        rich["sign_battery"][cid] = rep.supporting
        print(f"    {cid}: raw {rep.supporting['raw_median_gross_bps']:.1f} "
              f"p={rep.supporting['one_sided_p']:.3f} {rep.interpretation_label}", flush=True)

    # ---- Layer: attribution derangement per binding cell — retires hard_fail_leak ----
    print(f"[layer] attribution_derangement ({DEFAULT_DERANGE_SEEDS} seeds) …", flush=True)
    grid_cache: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for c in binding:
        cid = c["candidate_id"]
        sym = c["symbol"]
        legs = load_live_legs(cid)
        if legs.height == 0:
            continue
        if sym not in grid_cache:
            grid_cache[sym] = build_15m_open_grid(load_marks(cid))
        grid_ns, grid_open = grid_cache[sym]
        if len(grid_ns) < MIN_BLOCK_LTF * 2:
            continue
        entry_idx, block_id, block_edges, n_blocks, d, hold_bars = derangement_inputs(
            legs, grid_ns, grid_open)
        rep = attribution_derangement(
            entry_idx, block_id, block_edges, n_blocks, grid_open, d, hold_bars,
            candidate_id=cid, control_class="within_sample_attribution")
        reports.append(rep)
        s = rep.supporting
        rich["derangement"][cid] = {k: s[k] for k in
                                    ("collapse_median", "collapse_p05", "collapse_p95",
                                     "raw_median_gross_bps", "n_legs", "n_blocks",
                                     "derangement_zero_fixed_points")}
        print(f"    {cid}: collapse {s['collapse_median']:.2f} "
              f"[{s['collapse_p05']:.2f},{s['collapse_p95']:.2f}]", flush=True)

    # ---- write artifacts ----
    layer_rows = [r.to_dict() for r in reports]
    (RESULTS / "layer_reports.json").write_text(
        json.dumps({"universe_id": UNIVERSE_ID, "generated_utc": _utc_now(),
                    "framework": "INFR-016 report layers (observed/ideal/interpretation)",
                    "n_binding": len(binding), "n_disclosure": len(disclosure),
                    "gate_band": bands["stage2_gate"], "layers": layer_rows,
                    "rich": rich}, indent=2, default=str) + "\n", encoding="utf-8")
    (RESULTS / "layer_tables.md").write_text(render_all_layers(reports) + "\n", encoding="utf-8")
    print(f"\nWROTE {RESULTS/'layer_reports.json'}")
    print(f"WROTE {RESULTS/'layer_tables.md'}")
    print(f"layers: {sorted(set(r.layer for r in reports))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
