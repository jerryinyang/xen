#!/usr/bin/env python3
"""INFR-010 Phase B orchestrator — pin, smokes, determinism, emission + shim verify.

Stop at the verify block. Writes artifacts under experiments/INFR-010/{artifacts,results}/.
"""
from __future__ import annotations

import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import nautilus_trader

ROOT = Path(__file__).resolve().parents[3]  # python/
EXP = Path(__file__).resolve().parents[1]  # INFR-010/
ARTIFACTS = EXP / "artifacts"
RESULTS = EXP / "results"
RUNS = ROOT.parent / "data" / "nautilus_runs"

sys.path.insert(0, str(ROOT / "src"))


def _pin_record() -> dict:
    return {
        "package": "nautilus_trader",
        "version": nautilus_trader.__version__,
        "specifier": "nautilus_trader==1.230.0",
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": sys.version.split()[0],
        "python_implementation": platform.python_implementation(),
        "one_platform_rule": (
            "INFR-007 caveat: bit-identical / 1-ULP-sensitive artefacts are valid only "
            "on the recorded platform. Do not upgrade the pin without an INFR amendment."
        ),
        "recorded_utc": datetime.now(UTC).isoformat(),
        "pyproject": "python/pyproject.toml",
        "uv_lock": "python/uv.lock",
    }


def publish_pin() -> dict:
    pin = _pin_record()
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    for path in (ARTIFACTS / "nautilus_pin.json", RESULTS / "nautilus_pin.json"):
        path.write_text(json.dumps(pin, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    # Early publish for INFR-011 catalog-ingest unblock
    infr011 = EXP.parent / "INFR-011" / "artifacts"
    if infr011.is_dir():
        (infr011 / "nautilus_pin.json").write_text(
            json.dumps(pin, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    print(f"PIN {pin['version']} @ {pin['platform']} / py{pin['python']}")
    return pin


def _run_subprocess(code: str, label: str) -> str:
    """Run Nautilus work in a fresh process (logging init is once-per-process)."""
    proc = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"{label} failed (rc={proc.returncode}):\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return proc.stdout


def smoke_bar(pin: dict) -> dict:
    """MA-cross smoke: BacktestNode (catalog) + BacktestEngine emission, separate processes."""
    src = str(ROOT / "src")
    runs = str(RUNS)

    # 1) BacktestNode path (design §6 Phase B) — subprocess
    node_code = f"""
import json, sys, tempfile
sys.path.insert(0, r"{src}")
from xen.nautilus.backtest_util import run_ma_cross_node
with tempfile.TemporaryDirectory(prefix="infr010_cat_") as tmp:
    out = run_ma_cross_node(tmp)
print("NODE_JSON:" + json.dumps(out["backtest_result"], default=str))
"""
    node_stdout = _run_subprocess(node_code, "smoke_bar/BacktestNode")
    node_line = [ln for ln in node_stdout.splitlines() if ln.startswith("NODE_JSON:")][-1]
    node_result = json.loads(node_line.split("NODE_JSON:", 1)[1])

    # 2) Engine path — emission contract + adjudication shim
    eng_code = f"""
import json, sys
sys.path.insert(0, r"{src}")
from pathlib import Path
import nautilus_trader, platform
from xen.nautilus.adjudication_shim import adjudicate_emission
from xen.nautilus.backtest_util import run_ma_cross_engine
from xen.nautilus.emission import write_emission_v1

eng = run_ma_cross_engine()
run_dir = Path(r"{runs}") / "INFR-010-smoke-bar-{pin['version']}"
paths = write_emission_v1(
    run_dir,
    fills=eng["fills"],
    orders=eng["orders"],
    positions_ledger=eng["positions_ledger"],
    bar_marks=eng["bar_marks"],
    instrument_id_map=eng["instrument_id_map"],
    run_config=eng["run_config"],
    catalog_version=None,
    catalog_path=None,
    nautilus_version=r"{pin['version']}",
    platform=r"{pin['platform']}",
    extra_metadata={{"smoke": "ma_cross_bars"}},
)
bundle = adjudicate_emission(run_dir, cost_bps=0.0)
ok = bool(bundle.reconcile_report and bundle.reconcile_report.ok)
meta = json.loads(paths.run_metadata.read_text())
payload = {{
    "instrument_id": eng["instrument_id"],
    "n_fills": eng["fills"].height,
    "n_orders": eng["orders"].height,
    "n_positions": eng["positions_ledger"].height,
    "n_bar_marks": eng["bar_marks"].height,
    "event_log_sha256": meta["event_log_sha256"],
    "emission_dir": str(run_dir),
    "n_legs": bundle.cis_trades.height,
    "reconcile_ok": ok,
    "reconcile": (
        {{
            "per_bar_gross_total": bundle.reconcile_report.per_bar_gross_total,
            "per_leg_realized_total": bundle.reconcile_report.per_leg_realized_total,
            "abs_diff_bps": bundle.reconcile_report.abs_diff_bps,
            "ok": bundle.reconcile_report.ok,
        }}
        if bundle.reconcile_report else None
    ),
}}
print("ENG_JSON:" + json.dumps(payload, default=str))
"""
    eng_stdout = _run_subprocess(eng_code, "smoke_bar/BacktestEngine")
    eng_line = [ln for ln in eng_stdout.splitlines() if ln.startswith("ENG_JSON:")][-1]
    eng = json.loads(eng_line.split("ENG_JSON:", 1)[1])

    report = {
        "smoke": "ma_cross_bars",
        "api": ["BacktestNode", "BacktestEngine"],
        "instrument_id": eng["instrument_id"],
        "n_fills": eng["n_fills"],
        "n_orders": eng["n_orders"],
        "n_positions": eng["n_positions"],
        "n_bar_marks": eng["n_bar_marks"],
        "event_log_sha256": eng["event_log_sha256"],
        "emission_dir": eng["emission_dir"],
        "backtest_node": {
            "iterations": node_result["iterations"],
            "total_events": node_result["total_events"],
            "stats_pnls": node_result["stats_pnls"],
        },
        "adjudication_shim": {
            "n_legs": eng["n_legs"],
            "reconcile_ok": eng["reconcile_ok"],
            "reconcile": eng["reconcile"],
        },
        "pass": (
            eng["n_fills"] > 0
            and eng["reconcile_ok"]
            and node_result["iterations"] == 500
        ),
    }
    (RESULTS / "smoke_bar.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    print(
        f"SMOKE_BAR fills={report['n_fills']} positions={report['n_positions']} "
        f"reconcile={eng['reconcile_ok']} node_iters={node_result['iterations']} "
        f"pass={report['pass']}"
    )
    return report


def smoke_l2(pin: dict) -> dict:
    """L2_MBP smoke in a fresh process (logging isolation)."""
    src = str(ROOT / "src")
    runs = str(RUNS)
    code = f"""
import json, sys
sys.path.insert(0, r"{src}")
from pathlib import Path
from xen.nautilus.backtest_util import run_l2_mbp_engine
from xen.nautilus.emission import write_emission_v1

out = run_l2_mbp_engine()
run_dir = Path(r"{runs}") / "INFR-010-smoke-l2-{pin['version']}"
write_emission_v1(
    run_dir,
    fills=out["fills"],
    orders=out["orders"],
    positions_ledger=out["positions_ledger"],
    bar_marks=out["bar_marks"],
    instrument_id_map=out["instrument_id_map"],
    run_config=out["run_config"],
    nautilus_version=r"{pin['version']}",
    platform=r"{pin['platform']}",
    extra_metadata={{"smoke": "l2_mbp", "book_summary": out["book_summary"]}},
)
payload = {{
    "instrument_id": out["run_config"]["instrument_id"],
    "n_fills": out["fills"].height,
    "n_orders": out["orders"].height,
    "book_summary": out["book_summary"],
    "emission_dir": str(run_dir),
}}
print("L2_JSON:" + json.dumps(payload, default=str))
"""
    stdout = _run_subprocess(code, "smoke_l2")
    line = [ln for ln in stdout.splitlines() if ln.startswith("L2_JSON:")][-1]
    out = json.loads(line.split("L2_JSON:", 1)[1])
    report = {
        "smoke": "l2_mbp",
        "instrument_id": out["instrument_id"],
        "book_type": "L2_MBP",
        "n_fills": out["n_fills"],
        "n_orders": out["n_orders"],
        "book_summary": out["book_summary"],
        "emission_dir": out["emission_dir"],
        "pass": (
            out["n_fills"] > 0
            and out["book_summary"].get("best_bid") is not None
            and out["book_summary"].get("best_ask") is not None
        ),
    }
    (RESULTS / "smoke_l2.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    print(
        f"SMOKE_L2 fills={report['n_fills']} bid={report['book_summary'].get('best_bid')} "
        f"ask={report['book_summary'].get('best_ask')} pass={report['pass']}"
    )
    return report


def determinism_check(n_repeats: int = 3) -> dict:
    """Identical config → byte-identical event logs across fresh processes."""
    src = str(ROOT / "src")
    code = f"""
import hashlib, platform, sys, tempfile
from pathlib import Path
sys.path.insert(0, r"{src}")
import nautilus_trader
from xen.nautilus.backtest_util import run_ma_cross_engine
from xen.nautilus.emission import write_emission_v1
eng = run_ma_cross_engine()
with tempfile.TemporaryDirectory(prefix="infr010_det_") as tmp:
    paths = write_emission_v1(
        Path(tmp) / "run",
        fills=eng["fills"],
        orders=eng["orders"],
        positions_ledger=eng["positions_ledger"],
        bar_marks=eng["bar_marks"],
        instrument_id_map=eng["instrument_id_map"],
        run_config=eng["run_config"],
        nautilus_version=nautilus_trader.__version__,
        platform=platform.platform(),
    )
    body = paths.event_log.read_bytes()
    print("DET:" + hashlib.sha256(body).hexdigest() + " " + str(len(body)))
"""
    hashes: list[str] = []
    sizes: list[int] = []
    for i in range(n_repeats):
        stdout = _run_subprocess(code, f"determinism/{i+1}")
        line = [ln for ln in stdout.splitlines() if ln.startswith("DET:")][-1]
        h, sz = line.split("DET:", 1)[1].split()
        hashes.append(h)
        sizes.append(int(sz))
        print(f"DET run{i+1}/{n_repeats} sha256={h} bytes={sz}")

    identical = len(set(hashes)) == 1
    report = {
        "n_repeats": n_repeats,
        "event_log_sha256": hashes,
        "event_log_bytes": sizes,
        "byte_identical": identical,
        "canonical_sha256": hashes[0] if identical else None,
        "method": "fresh_process_x3_identical_config",
        "note": (
            "Event log is UUID-stripped (emission contract v1). "
            "Nautilus init_id UUIDs are process-ephemeral and excluded. "
            "Economic content (side/qty/px/ts/commissions) is hashed."
        ),
        "pass": identical,
    }
    (RESULTS / "determinism.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"DETERMINISM byte_identical={identical} pass={report['pass']}")
    return report


def verify(pin: dict, bar: dict, l2: dict, det: dict) -> dict:
    """Phase B verify block."""
    from xen.nautilus.instrument_ids import (
        archive_symbol_to_instrument_id_str,
        instrument_id_to_archive_symbol,
    )

    mapping_ok = (
        archive_symbol_to_instrument_id_str("BTCUSDT") == "BTCUSDT-LINEAR.BYBIT"
        and instrument_id_to_archive_symbol("ETHUSDT-LINEAR.BYBIT") == "ETHUSDT"
    )
    checks = {
        "pin_hard": pin["version"] == "1.230.0" and pin["specifier"].endswith("==1.230.0"),
        "instrument_id_convention": mapping_ok,
        "smoke_bar": bool(bar.get("pass")),
        "smoke_l2_mbp": bool(l2.get("pass")),
        "determinism_3x": bool(det.get("pass")),
        "emission_parses_to_adjudication": bool(
            bar.get("adjudication_shim", {}).get("reconcile_ok")
        ),
    }
    report = {
        "phase": "INFR-010 Phase B",
        "verified_utc": datetime.now(UTC).isoformat(),
        "checks": checks,
        "all_pass": all(checks.values()),
        "pin": pin,
        "determinism_canonical_sha256": det.get("canonical_sha256"),
        "emission_contract": "nautilus-emission-v1",
        "stop": "verify block — Phase B complete when all_pass",
    }
    (RESULTS / "phase_b_verify.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    print("VERIFY", json.dumps(checks, indent=2))
    print("ALL_PASS" if report["all_pass"] else "VERIFY_FAILED")
    return report


def main() -> int:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    RUNS.mkdir(parents=True, exist_ok=True)

    pin = publish_pin()
    bar = smoke_bar(pin)
    l2 = smoke_l2(pin)
    det = determinism_check(3)
    ver = verify(pin, bar, l2, det)
    return 0 if ver["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
