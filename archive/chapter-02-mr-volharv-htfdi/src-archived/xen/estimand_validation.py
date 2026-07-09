"""Estimand validation gate (INFR-001 WS-2) — run BEFORE any analysis, verdict, or TEST read.

Validates that an emitted run's P&L measurement is faithful before anything downstream may
consume it. This is the missing layer behind critical-017: every control validated the
hypothesis on top of an unvalidated estimand.

Blocking checks (any failure => the emission must not be adjudicated):
* schema — required columns present; ``SourceCloseTime`` strictly increasing;
* fence — last bar within the run's ``analysis_end_utc``;
* reconciliation — |sum(per-bar gross) - sum(leg RealizedBps)| <= tolerance, per cell,
  using the canonical ``xen.adjudication`` series (never experiment-local code);
* manifest — every expected instrument has an emitted run (when an expectation is given).

Reported checks (informative — never blocking; operator judges):
* physicality — annualised return, per-bar Sharpe, max drawdown, occupancy, versus a
  buy-and-hold baseline derived from the same emission's ``RealOpen`` path;
* loose sanity flags (e.g. Sharpe above any credible single-instrument level).

CLI::

    python -m xen.estimand_validation <family_root_or_run_dir> \
        [--expect US2000,AUDUSD,...] [--cost-bps N] [--out results/estimand_validation.json]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from xen.adjudication import (
    REQUIRED_LEG_COLS,
    REQUIRED_POSITION_COLS,
    assemble_multileg_bps,
    reconcile,
)

SHARPE_SANITY = 3.0          # informative flag only — no real single-instrument strategy
ANN_RETURN_SANITY = 1.0      # sustains Sharpe>3 or >100%/yr; the operator judges

# accounting primitives that must never be (re)defined in experiment-local code
BANNED_LOCAL_DEFS = ("assemble_realized_bps", "assemble_multileg_bps", "per_leg_net",
                     "build_episodes")


def _load_metadata(run_dir: Path) -> dict:
    meta_path = run_dir / "run_metadata.json"
    return json.loads(meta_path.read_text()) if meta_path.exists() else {}


def _schema_check(pos: pl.DataFrame, cis: pl.DataFrame) -> dict:
    missing_pos = [c for c in REQUIRED_POSITION_COLS if c not in pos.columns]
    missing_leg = [c for c in REQUIRED_LEG_COLS if c not in cis.columns] if cis.height else []
    t = pos.sort("SourceCloseTime").get_column("SourceCloseTime").to_numpy()
    monotonic = bool((np.diff(t.astype("int64")) > 0).all()) if len(t) > 1 else True
    ok = not missing_pos and not missing_leg and monotonic
    return {"ok": ok, "missing_positions_cols": missing_pos,
            "missing_leg_cols": missing_leg, "timestamps_strictly_increasing": monotonic}


def _fence_check(pos: pl.DataFrame, metadata: dict) -> dict:
    fence = metadata.get("analysis_end_utc")
    if not fence:
        return {"ok": False, "reason": "no analysis_end_utc in run metadata"}
    last = pos.get_column("SourceCloseTime").max()
    fence_ts = np.datetime64(str(fence).rstrip("Z"))
    ok = bool(np.datetime64(last) <= fence_ts)
    return {"ok": ok, "last_bar": str(last), "fence": str(fence)}


def _physicality(pos: pl.DataFrame, cis: pl.DataFrame, cost_bps: float) -> dict:
    series = assemble_multileg_bps(pos, cis, cost_bps=cost_bps)
    t = series.times.astype("datetime64[s]").astype("int64")
    years = max(float(t[-1] - t[0]) / (365.25 * 24 * 3600), 1e-9)
    bars_per_year = len(t) / years
    net = series.net_bps
    total_net = float(net.sum())
    ann_return = total_net / 1e4 / years
    sd = float(net.std())
    sharpe = float(net.mean() / sd * np.sqrt(bars_per_year)) if sd > 0 else float("nan")
    cum = np.cumsum(net)
    max_dd_bps = float((cum - np.maximum.accumulate(cum)).min())
    occupancy = float((series.open_legs > 0).mean())

    opens = pos.sort("SourceCloseTime").get_column("RealOpen").to_numpy().astype(float)
    bh_ret = np.diff(np.log(opens))
    bh_ann_return = float(bh_ret.sum() / years)
    bh_ann_vol = float(bh_ret.std() * np.sqrt(bars_per_year))

    flags = []
    if np.isfinite(sharpe) and abs(sharpe) > SHARPE_SANITY:
        flags.append(f"|Sharpe| {sharpe:.2f} > {SHARPE_SANITY} — non-physical for a "
                     "single-instrument strategy; interrogate before trusting")
    if abs(ann_return) > ANN_RETURN_SANITY:
        flags.append(f"|annualised return| {ann_return:.1%} > {ANN_RETURN_SANITY:.0%}/yr")
    if bh_ann_vol > 0 and abs(ann_return) > 3.0 * bh_ann_vol:
        flags.append(f"annualised return {ann_return:.1%} exceeds 3x buy-and-hold vol "
                     f"({bh_ann_vol:.1%}) on the same instrument")
    return {
        "years": years, "n_bars": len(t), "n_legs": series.n_legs,
        "n_censored_legs": series.n_censored,
        "total_net_bps": total_net, "annualised_return": ann_return,
        "per_bar_sharpe_annualised": sharpe, "max_drawdown_bps": max_dd_bps,
        "occupancy": occupancy,
        "buy_and_hold_annualised_return": bh_ann_return,
        "buy_and_hold_annualised_vol": bh_ann_vol,
        "sanity_flags": flags,
    }


def validate_run(run_dir: str | Path, *, cost_bps: float = 0.0) -> dict:
    """Validate one emitted run directory. ``blocking_pass`` gates all downstream use."""
    run_dir = Path(run_dir)
    pos = pl.read_parquet(run_dir / "positions.parquet")
    cis_path = run_dir / "cis_trades.parquet"
    cis = pl.read_parquet(cis_path) if cis_path.exists() else pl.DataFrame()
    metadata = _load_metadata(run_dir)

    schema = _schema_check(pos, cis)
    fence = _fence_check(pos, metadata)
    result: dict[str, Any] = {
        "run_dir": str(run_dir),
        "instrument": metadata.get("symbol"), "domain": metadata.get("domain"),
        "schema": schema, "fence": fence,
    }
    if schema["ok"] and cis.height:
        series = assemble_multileg_bps(pos, cis, cost_bps=cost_bps)
        rep = reconcile(series, cis)
        result["reconciliation"] = {
            "ok": rep.ok, "per_bar_gross_total": rep.per_bar_gross_total,
            "per_leg_realized_total": rep.per_leg_realized_total,
            "abs_diff_bps": rep.abs_diff_bps, "tol_bps": rep.tol_bps,
        }
        result["physicality"] = _physicality(pos, cis, cost_bps)
        reconcile_ok = rep.ok
    else:
        result["reconciliation"] = {"ok": cis.height == 0,
                                    "note": "no leg ledger" if cis.height == 0
                                    else "schema failure — not attempted"}
        reconcile_ok = cis.height == 0 and schema["ok"]
    result["blocking_pass"] = bool(schema["ok"] and fence["ok"] and reconcile_ok)
    return result


def validate_family(root: str | Path, *, expected_instruments: list[str] | None = None,
                    cost_bps: float = 0.0) -> dict:
    """Validate every emitted run under a family root; check the completeness manifest."""
    root = Path(root)
    run_dirs = sorted(d for d in root.iterdir()
                      if d.is_dir() and (d / "positions.parquet").exists())
    cells = [validate_run(d, cost_bps=cost_bps) for d in run_dirs]
    emitted = {str(c["instrument"]).upper() for c in cells if c.get("instrument")}
    missing = ([i.upper() for i in expected_instruments if i.upper() not in emitted]
               if expected_instruments else [])
    return {
        "root": str(root), "n_cells": len(cells),
        "manifest": {"ok": not missing, "expected": expected_instruments or [],
                     "emitted": sorted(emitted), "missing": missing},
        "blocking_pass": bool(all(c["blocking_pass"] for c in cells)
                              and not missing and cells),
        "cells": cells,
    }


def check_no_local_accounting(experiment_code_dir: str | Path) -> dict:
    """Blocking repo check: accounting primitives must not be redefined in experiment code."""
    hits = []
    for py in sorted(Path(experiment_code_dir).rglob("*.py")):
        text = py.read_text(errors="replace")
        for name in BANNED_LOCAL_DEFS:
            if f"def {name}" in text:
                hits.append(f"{py}: def {name}")
    return {"ok": not hits, "banned_defs_found": hits}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("target", help="family root (dir of run dirs) or a single run dir")
    ap.add_argument("--expect", default=None,
                    help="comma-separated expected instruments (manifest check)")
    ap.add_argument("--cost-bps", type=float, default=0.0)
    ap.add_argument("--out", default=None, help="write JSON report here")
    args = ap.parse_args()

    target = Path(args.target)
    expected = [s.strip() for s in args.expect.split(",")] if args.expect else None
    if (target / "positions.parquet").exists():
        report = validate_run(target, cost_bps=args.cost_bps)
    else:
        report = validate_family(target, expected_instruments=expected,
                                 cost_bps=args.cost_bps)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(report, indent=2, default=str))
    print(json.dumps({k: v for k, v in report.items() if k != "cells"},
                     indent=2, default=str))
    print(f"BLOCKING_PASS: {report['blocking_pass']}")
    return 0 if report["blocking_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
