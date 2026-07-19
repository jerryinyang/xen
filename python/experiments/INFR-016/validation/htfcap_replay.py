#!/usr/bin/env python3
"""INFR-016 real known-answer replay — the trust anchor.

Synthetic tests can be gamed by their own design (the old CAL battery was). This test uses a
REAL case whose answer we now KNOW: the XENA-HTFCAP-001 redo established that the binder's
certified top-1 was ~1 bps noise (sign-p ≈ 0.44) while BTC mid-threshold adx25 H32/H64 carry a
real, sign-clean, gate-attributable edge (one-sided p ≈ 0.017–0.043), and SOL v1.5 DI_VOL_HI
H64 is suggestive-underpowered (p ≈ 0.22). We run the INFR-016 report layers (sign battery,
2000 seeds) over the ACTUAL emissions and confirm they reproduce that ranking — the exact
discrimination the binder failed, on real data with a known truth.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[3]           # python/
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

from xen.nautilus.adjudication_shim import emission_to_adjudication_frames  # noqa: E402
from xen.xena.controls import sign_battery  # noqa: E402

RUNS = REPO / "data" / "nautilus_runs" / "XENA-HTFCAP-001"
MIN_LEGS = 20


def load_legs(cell_dir: Path) -> pl.DataFrame | None:
    if not (cell_dir / "run_metadata.json").exists():
        return None
    try:
        _pos, cis, _meta = emission_to_adjudication_frames(cell_dir)
    except Exception:
        return None
    live = cis.filter(pl.col("Censored").cast(pl.Boolean).not_()
                      & pl.col("RealizedBps").is_finite()).sort("EntryTime")
    return live if live.height >= MIN_LEGS else None


def score_cell(live: pl.DataFrame, cid: str) -> dict:
    d = live.get_column("Direction").to_numpy().astype(float)
    ep = live.get_column("EntryFillPrice").to_numpy().astype(float)
    xp = live.get_column("ExitFillPrice").to_numpy().astype(float)
    sb = sign_battery(d, ep, xp, candidate_id=cid, n_seeds=2000)
    s = sb.supporting
    return {"cid": cid, "n_legs": s["n_legs"], "gross_med": s["raw_median_gross_bps"],
            "sign_p": s["one_sided_p"], "effect": s["effect_bps"],
            "pct": s["percentile_vs_battery"], "label": sb.interpretation_label}


def run() -> dict:
    rows = []
    for cell_dir in sorted(RUNS.iterdir()):
        if not cell_dir.is_dir():
            continue
        live = load_legs(cell_dir)
        if live is None:
            continue
        rows.append(score_cell(live, cell_dir.name))
    rows.sort(key=lambda r: r["sign_p"])          # cleanest first

    def find(sub: str) -> dict | None:
        return next((r for r in rows if sub in r["cid"]), None)

    def best_adx25(hold: int) -> dict | None:
        """Redo's claim is about the adx25 H32/H64 HOLDS (mid-threshold), not a fixed
        capture-scale variant — take the cleanest adx25 cell at that hold across v-variants."""
        cands = [r for r in rows if f"__adx25__H{hold}" in r["cid"] and r["cid"].startswith("BTC")]
        return min(cands, key=lambda r: r["sign_p"]) if cands else None

    btc_adx25 = {h: best_adx25(h) for h in (32, 64)}
    sol = find("SOLUSDT__DI_VOL_HI__v1.5__adxna__H64")

    clean = [r for r in rows if r["sign_p"] < 0.05 and r["gross_med"] > 0]
    checks = {
        "cells_scored": len(rows) >= 20,
        # known-good BTC adx25 holds are sign-clean (redo: p 0.017–0.043)
        "btc_adx25_H32_clean": btc_adx25[32] is not None and btc_adx25[32]["sign_p"] < 0.06,
        "btc_adx25_H64_clean": btc_adx25[64] is not None and btc_adx25[64]["sign_p"] < 0.06,
        "btc_adx25_positive": all(v is not None and v["gross_med"] > 0
                                  for v in btc_adx25.values()),
        # SOL suggestive-underpowered (redo: p ≈ 0.22) — NOT clean, NOT refuted
        "sol_suggestive_not_clean": sol is not None and 0.12 < sol["sign_p"] < 0.35,
        # the framework surfaces a real clean set (the good cells the binder hid)
        "clean_set_nonempty": len(clean) >= 1,
    }
    return {"rows": rows, "btc_adx25": btc_adx25, "sol": sol, "clean": clean, "checks": checks}


def _fmt(res: dict) -> str:
    lines = ["INFR-016 real HTFCAP known-answer replay (sign battery, 2000 seeds)",
             f"  cells scored: {len(res['rows'])}",
             "",
             f"  {'cell':<48} {'n':>4} {'gross_med':>10} {'sign_p':>7} {'pct':>5} {'label':>6}"]
    show = res["rows"][:8] + [None] + res["rows"][-3:]
    for r in show:
        if r is None:
            lines.append("  " + "…" * 20)
            continue
        lines.append(f"  {r['cid']:<48} {r['n_legs']:>4} {r['gross_med']:>10.1f} "
                     f"{r['sign_p']:>7.3f} {r['pct']:>5.2f} {str(r['label']):>6}")
    lines.append("")
    lines.append(f"  known-good BTC adx25 H32: {res['btc_adx25'][32]}")
    lines.append(f"  known-good BTC adx25 H64: {res['btc_adx25'][64]}")
    lines.append(f"  SOL v1.5 DI_VOL_HI H64  : {res['sol']}")
    lines.append(f"  clean set (sign_p<0.05, gross>0): {len(res['clean'])} cells")
    lines.append("")
    for k, v in res["checks"].items():
        lines.append(f"  [{'PASS' if v else 'FAIL'}] {k}")
    lines.append(f"\n  {sum(res['checks'].values())}/{len(res['checks'])} checks passed")
    return "\n".join(lines)


def main() -> int:
    if not RUNS.exists():
        print(f"SKIP: no HTFCAP emissions at {RUNS}")
        return 0
    res = run()
    print(_fmt(res))
    return 0 if all(res["checks"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
