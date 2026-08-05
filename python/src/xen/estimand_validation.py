"""Estimand validation gate — run BEFORE any analysis, verdict, or TEST read.

v2 (INFR-012): Nautilus emission contract v1 — reconciliation via adjudication shim,
fence attestation (rejects Phase-B STUB), manifest + catalog hash checks.

v1 (legacy): cTrader ``data/strategy_runs/`` emissions — retained for archived VAL carve-out.

Blocking checks (any failure => emission must not be adjudicated):
* schema — required columns; ``SourceCloseTime`` strictly increasing;
* fence — last bar within ``analysis_end_utc``; v2 rejects ``STUB`` attestations;
* reconciliation — |sum(per-bar gross) - sum(leg RealizedBps)| <= tolerance;
* manifest — expected instruments present when an expectation is given.

CLI::

    python -m xen.estimand_validation <family_root_or_run_dir> \\
        [--expect BTCUSDT,ETHUSDT,...] [--cost-bps N] [--out results/estimand_validation.json]
"""
from __future__ import annotations

import argparse
import hashlib
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

GATE_VERSION = "v2"
EMISSION_CONTRACT_V1 = "nautilus-emission-v1"
PHASE_B_STUB_STATUS = "STUB"
FENCE_MANIFEST_CANONICAL = Path(
    "archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-011/artifacts/fence-manifest.json"
)

SHARPE_SANITY = 3.0
ANN_RETURN_SANITY = 1.0

BANNED_LOCAL_DEFS = ("assemble_realized_bps", "assemble_multileg_bps", "per_leg_net",
                     "build_episodes")

NAUTILUS_REQUIRED_FILES = (
    "run_metadata.json",
    "bar_marks.parquet",
    "positions_ledger.parquet",
    "fills.parquet",
    "orders.parquet",
    "event_log.jsonl",
    "instrument_id_map.json",
    "fence_attestation.json",
)


def _repo_root() -> Path:
    """Best-effort repo root from this file location."""
    return Path(__file__).resolve().parents[3]


def is_nautilus_emission(run_dir: Path) -> bool:
    """True when ``run_dir`` looks like emission contract v1."""
    meta_path = run_dir / "run_metadata.json"
    if not meta_path.exists():
        return False
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("emission_contract_version") == EMISSION_CONTRACT_V1:
        return True
    return (run_dir / "bar_marks.parquet").exists() and not (run_dir / "positions.parquet").exists()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def _nautilus_schema_check(run_dir: Path, pos: pl.DataFrame, cis: pl.DataFrame) -> dict:
    missing_files = [f for f in NAUTILUS_REQUIRED_FILES if not (run_dir / f).exists()]
    base = _schema_check(pos, cis)
    meta = _load_metadata(run_dir)
    contract_ok = meta.get("emission_contract_version") == EMISSION_CONTRACT_V1
    ok = base["ok"] and not missing_files and contract_ok
    return {
        **base,
        "ok": ok,
        "emission_contract_version": meta.get("emission_contract_version"),
        "missing_emission_files": missing_files,
        "contract_version_ok": contract_ok,
    }


def _fence_check_ctrader(pos: pl.DataFrame, metadata: dict) -> dict:
    fence = metadata.get("analysis_end_utc")
    if not fence:
        return {"ok": False, "reason": "no analysis_end_utc in run metadata"}
    last = pos.get_column("SourceCloseTime").max()
    fence_ts = np.datetime64(str(fence).rstrip("Z"))
    ok = bool(np.datetime64(last) <= fence_ts)
    return {"ok": ok, "last_bar": str(last), "fence": str(fence), "mode": "ctrader"}


def _fence_check_v2(
    pos: pl.DataFrame,
    metadata: dict,
    fence_attestation: dict,
    *,
    repo_root: Path | None = None,
) -> dict:
    """v2 fence: reject STUB; require pinned manifest hash when canonical manifest exists."""
    status = fence_attestation.get("status")
    if status == PHASE_B_STUB_STATUS:
        return {
            "ok": False,
            "mode": "nautilus_v2",
            "reason": "Phase-B STUB fence_attestation — real experiments require INFR-011 A6 manifest",
            "status": status,
            "note": fence_attestation.get("note"),
        }

    analysis_end = fence_attestation.get("analysis_end_utc") or metadata.get("analysis_end_utc")
    if not analysis_end:
        return {"ok": False, "mode": "nautilus_v2",
                "reason": "no analysis_end_utc in fence attestation or metadata"}

    last = pos.get_column("SourceCloseTime").max()
    fence_ts = np.datetime64(str(analysis_end).rstrip("Z"))
    within_fence = bool(np.datetime64(last) <= fence_ts)

    root = repo_root or _repo_root()
    manifest_path = fence_attestation.get("manifest_path")
    if manifest_path:
        canon = root / manifest_path
    else:
        canon = root / FENCE_MANIFEST_CANONICAL

    manifest_sha256_attested = fence_attestation.get("manifest_sha256")
    manifest_check: dict[str, Any] = {"canonical_path": str(canon), "exists": canon.exists()}

    if manifest_sha256_attested:
        if not canon.exists():
            manifest_check["ok"] = False
            manifest_check["reason"] = "manifest_sha256 attested but canonical manifest missing"
        else:
            actual = _sha256_file(canon)
            manifest_check["ok"] = actual == manifest_sha256_attested
            manifest_check["expected_sha256"] = manifest_sha256_attested
            manifest_check["actual_sha256"] = actual
    elif status in (None, "", "PENDING"):
        manifest_check["ok"] = False
        manifest_check["reason"] = "no manifest_sha256 — INFR-011 A6 pin required"
    else:
        # Non-STUB status without hash — still blocking until A6 lands
        manifest_check["ok"] = False
        manifest_check["reason"] = f"status={status!r} without manifest_sha256 pin"

    ok = within_fence and manifest_check.get("ok", False)
    return {
        "ok": ok,
        "mode": "nautilus_v2",
        "status": status,
        "last_bar": str(last),
        "analysis_end_utc": str(analysis_end),
        "within_fence": within_fence,
        "manifest": manifest_check,
    }


def _manifest_check(
    metadata: dict,
    instrument_map: dict[str, str] | None,
    expected_instruments: list[str] | None,
) -> dict:
    emitted_symbol = metadata.get("symbol")
    if emitted_symbol:
        emitted = {str(emitted_symbol).upper()}
    elif instrument_map:
        emitted = {k.upper() for k in instrument_map}
    else:
        emitted = set()

    missing = ([i.upper() for i in expected_instruments if i.upper() not in emitted]
               if expected_instruments else [])
    return {
        "ok": not missing,
        "expected": expected_instruments or [],
        "emitted": sorted(emitted),
        "missing": missing,
    }


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


def validate_nautilus_run_v2(
    run_dir: str | Path,
    *,
    cost_bps: float = 0.0,
    expected_instruments: list[str] | None = None,
    repo_root: Path | None = None,
) -> dict:
    """Validate one Nautilus emission-contract-v1 directory."""
    from xen.nautilus.adjudication_shim import emission_to_adjudication_frames

    run_dir = Path(run_dir)
    pos, cis, metadata = emission_to_adjudication_frames(run_dir)
    fence_attestation = json.loads((run_dir / "fence_attestation.json").read_text(encoding="utf-8"))
    instrument_map = json.loads((run_dir / "instrument_id_map.json").read_text(encoding="utf-8"))

    schema = _nautilus_schema_check(run_dir, pos, cis)
    fence = _fence_check_v2(pos, metadata, fence_attestation, repo_root=repo_root)
    manifest = _manifest_check(metadata, instrument_map, expected_instruments)

    catalog_ok = True
    catalog_note = None
    if metadata.get("catalog_version") is None and metadata.get("catalog_path") is None:
        catalog_note = "catalog_version/path null — acceptable for Phase B smokes only"
        if fence_attestation.get("status") != PHASE_B_STUB_STATUS:
            catalog_ok = False
            catalog_note = "production emission requires catalog_version + catalog_path"

    result: dict[str, Any] = {
        "gate_version": GATE_VERSION,
        "emission_type": "nautilus_v1",
        "run_dir": str(run_dir),
        "instrument": metadata.get("symbol"),
        "domain": metadata.get("domain"),
        "schema": schema,
        "fence": fence,
        "manifest": manifest,
        "catalog_attestation": {"ok": catalog_ok, "note": catalog_note,
                                "catalog_version": metadata.get("catalog_version"),
                                "config_hash": metadata.get("config_hash")},
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

    result["blocking_pass"] = bool(
        schema["ok"] and fence["ok"] and reconcile_ok and manifest["ok"] and catalog_ok
    )
    return result


def validate_run(run_dir: str | Path, *, cost_bps: float = 0.0,
                 expected_instruments: list[str] | None = None) -> dict:
    """Validate one run — auto-detects Nautilus v1 vs legacy cTrader."""
    run_dir = Path(run_dir)
    if is_nautilus_emission(run_dir):
        return validate_nautilus_run_v2(
            run_dir, cost_bps=cost_bps, expected_instruments=expected_instruments,
        )

    pos = pl.read_parquet(run_dir / "positions.parquet")
    cis_path = run_dir / "cis_trades.parquet"
    cis = pl.read_parquet(cis_path) if cis_path.exists() else pl.DataFrame()
    metadata = _load_metadata(run_dir)

    schema = _schema_check(pos, cis)
    fence = _fence_check_ctrader(pos, metadata)
    manifest = _manifest_check(metadata, None, expected_instruments)
    result: dict[str, Any] = {
        "gate_version": "v1",
        "emission_type": "ctrader",
        "run_dir": str(run_dir),
        "instrument": metadata.get("symbol"), "domain": metadata.get("domain"),
        "schema": schema, "fence": fence, "manifest": manifest,
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
    result["blocking_pass"] = bool(schema["ok"] and fence["ok"] and reconcile_ok and manifest["ok"])
    return result


def validate_family(root: str | Path, *, expected_instruments: list[str] | None = None,
                    cost_bps: float = 0.0) -> dict:
    """Validate every emitted run under a family root."""
    root = Path(root)
    run_dirs = []
    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        if (d / "bar_marks.parquet").exists() or (d / "positions.parquet").exists():
            run_dirs.append(d)
    cells = [validate_run(d, cost_bps=cost_bps, expected_instruments=None)
             for d in run_dirs]
    emitted: set[str] = set()
    for c in cells:
        for sym in c.get("manifest", {}).get("emitted", []):
            emitted.add(sym)
        if c.get("instrument"):
            emitted.add(str(c["instrument"]).upper())
    missing = ([i.upper() for i in (expected_instruments or []) if i.upper() not in emitted])
    return {
        "gate_version": GATE_VERSION,
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
    if (target / "bar_marks.parquet").exists() or (target / "positions.parquet").exists():
        report = validate_run(target, cost_bps=args.cost_bps, expected_instruments=expected)
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
