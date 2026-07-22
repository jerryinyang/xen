#!/usr/bin/env python3
"""XENA-HTFCAP-001 universe manifest builder — 108 cells, immutable stage bands.

Writes:
  data/nautilus_runs/XENA-HTFCAP-001/universe_manifest.json
  python/experiments/XENA-HTFCAP-001/results/universe_manifest.json  (copy)
  python/experiments/XENA-HTFCAP-001/results/stage_bands.json

Band boundaries: frozen INFR-015 / calibration_pc fracs on TRAIN calendar
  search_frac=0.5, ranking_frac=0.25, embargo_frac=0.2
  via ``xen.xena.calibration.SegmentLayout.from_span`` + pin fracs.

Grid (design §4.2): 2 filter models × vol_thr{1.10,1.25,1.50} × holds{16,32,64}
  × (DI: no ADX; DI_ADX: ADX_min{20,25,30}) × 3 symbols = 108.

Instruments: BTC+SOL binding; ETH disclosure-only.
Feature pin: W=100, ATR(14), defs verbatim from spdr006_screen.py (no retune).
Cost stack: bybit_round_trip_cost_bps_v1 + funding (GAP pin until per-symbol series).

Usage (from python/):
  uv run python experiments/XENA-HTFCAP-001/code/build_universe.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CODE = Path(__file__).resolve().parent
EXP = CODE.parent
ROOT = EXP.parents[1]  # python/
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

from xen.evaluation import (  # noqa: E402
    BYBIT_FUNDING_CONSERVATIVE_BPS_PER_8H,
    bybit_round_trip_cost_bps,
)
from xen.nautilus.catalog_fence import load_fence_manifest  # noqa: E402
from xen.xena.calibration import SegmentLayout  # noqa: E402
from xen.xena.calibration_pc import (  # noqa: E402
    EMBARGO_FRAC,
    STAGE_RANKING_FRAC,
    STAGE_SEARCH_FRAC,
)

UNIVERSE_ID = "XENA-HTFCAP-001"
FAMILY = "CF-HTFCAP-001"
RUNS_ROOT = REPO / "data" / "nautilus_runs" / UNIVERSE_ID
RESULTS = EXP / "results"
REGISTRY_PATH = REPO / "python/experiments/INFR-015/results/bybit_pc_frozen_registry.json"
DESIGN_PIN_BODY_SHA = "abbb184229236a75f624537ca605668a73f6f85138c150e14a3609c4191bf786"

# design §4.1
BINDING_SYMBOLS = ("BTCUSDT", "SOLUSDT")
DISCLOSURE_SYMBOLS = ("ETHUSDT",)
ALL_SYMBOLS = BINDING_SYMBOLS + DISCLOSURE_SYMBOLS

FILTER_DI = "DI×VOL_HI"
FILTER_DI_ADX = "DI_ADX×VOL_HI"
VOL_THRS = (1.10, 1.25, 1.50)
ADX_MINS = (20.0, 25.0, 30.0)
HOLD_BARS = (16, 32, 64)  # 1×, 2×, 4× of 4h span in 15m bars
HOLD_MULT = {16: 1.0, 32: 2.0, 64: 4.0}

# GAP spread pin (INFR-014 cost_pins) until per-symbol pseudo-quote series wired
GAP_SPREAD_BPS = 5.0
COST_STACK = "bybit_round_trip_cost_bps_v1"
CATALOG_VERSION = "INFR-011-A4-2026-07-16"


def _utc_iso(ns: int) -> str:
    return datetime.fromtimestamp(ns / 1e9, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin_body_sha256(path: Path) -> str:
    """Official pin digest = sha256 of registry body (sort_keys), not file bytes."""
    artifact = json.loads(path.read_text(encoding="utf-8"))
    blob = json.dumps(artifact["registry"], sort_keys=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


MAJORS_START_UTC = "2022-07-14T00:00:00Z"  # AMENDMENT-4: majors' local catalog start


def stage_bands_from_fence(fence, *, extend_test: bool = False) -> dict[str, Any]:
    """Stage bands on the analysis calendar (frozen pin fracs).

    AMENDMENT-4 (operator 2026-07-18): with ``extend_test`` the calendar is the covered
    majors window 2022-07-14 → holdout_start (TRAIN+TEST, exploratory, no reserved OOS);
    HOLDOUT (≥ holdout_start) is never included. Default is TRAIN-only (original design).
    """
    if extend_test:
        start_dt = datetime.fromisoformat(MAJORS_START_UTC.replace("Z", "+00:00"))
        start_ns = int(start_dt.timestamp() * 1e9)
        end_ns = int(fence.holdout_start_utc.timestamp() * 1e9)
    else:
        start_ns = int(fence.analysis_start_utc.timestamp() * 1e9)
        end_ns = int(fence.train_end_utc.timestamp() * 1e9)
    span = end_ns - start_ns
    purge_ns = int(EMBARGO_FRAC * span)
    layout = SegmentLayout.from_span(
        start_ns,
        end_ns,
        search_frac=STAGE_SEARCH_FRAC,
        ranking_frac=STAGE_RANKING_FRAC,
        purge_ns=purge_ns,
    )
    return {
        "source": (
            "AMENDMENT-4 exploratory TRAIN+TEST fracs (majors 2022-07-14 → holdout_start); "
            "NO reserved OOS" if extend_test
            else "xen.xena.calibration_pc frozen fracs on INFR-011 TRAIN fence"
        ),
        "extend_test": extend_test,
        "window_start_utc": _utc_iso(start_ns),
        "window_end_utc": _utc_iso(end_ns),
        "search_frac": STAGE_SEARCH_FRAC,
        "ranking_frac": STAGE_RANKING_FRAC,
        "embargo_frac": EMBARGO_FRAC,
        "purge_ns": layout.purge_ns,
        "train_start_utc": fence.analysis_start_utc.isoformat().replace("+00:00", "Z"),
        "train_end_utc": fence.train_end_utc.isoformat().replace("+00:00", "Z"),
        "holdout_start_utc": fence.holdout_start_utc.isoformat().replace("+00:00", "Z"),
        "search": {"start_ns": layout.search[0], "end_ns": layout.search[1],
                   "start_utc": _utc_iso(layout.search[0]), "end_utc": _utc_iso(layout.search[1])},
        "ranking": {"start_ns": layout.ranking[0], "end_ns": layout.ranking[1],
                    "start_utc": _utc_iso(layout.ranking[0]), "end_utc": _utc_iso(layout.ranking[1])},
        "stage2_gate": {"start_ns": layout.gate[0], "end_ns": layout.gate[1],
                        "start_utc": _utc_iso(layout.gate[0]), "end_utc": _utc_iso(layout.gate[1])},
        "note": (
            "AMENDMENT-4: exploratory TRAIN+TEST window; search/ranking in TRAIN, stage-2 "
            "gate lands in TEST; HOLDOUT sealed; NO reserved OOS — read as informative"
            if extend_test
            else "immutable once written; search may only read TRAIN search band"
        ),
    }


def candidate_id(
    symbol: str,
    filter_model: str,
    vol_thr: float,
    adx_min: float | None,
    hold_bars: int,
) -> str:
    fm = "DI_VOL_HI" if filter_model == FILTER_DI else "DI_ADX_VOL_HI"
    adx_part = "na" if adx_min is None else f"{adx_min:g}"
    return f"{symbol}__{fm}__v{vol_thr:g}__adx{adx_part}__H{hold_bars}"


def cost_bps_for_hold(hold_bars: int) -> dict[str, Any]:
    """bybit_round_trip_cost_bps_v1 with funding; hold_hours = hold_bars × 0.25h."""
    hold_hours = hold_bars * 0.25  # 15m LTF bars
    d = bybit_round_trip_cost_bps(
        "BTCUSDT",
        1.0,
        liquidity="taker",
        spread_bps=GAP_SPREAD_BPS,
        funding_bps_per_8h=BYBIT_FUNDING_CONSERVATIVE_BPS_PER_8H,
        hold_hours=hold_hours,
        funding_coverage="GAP",
    )
    return {
        "cost_bps": float(d["total_bps"]),
        "hold_hours": hold_hours,
        "fee_rt_bps": d["fee_rt_bps"],
        "spread_rt_bps": d["spread_rt_bps"],
        "funding_rt_bps": d["funding_rt_bps"],
        "funding_coverage": d["funding_coverage"],
        "spread_label": "GAP",
        "spread_bps": GAP_SPREAD_BPS,
    }


def build_candidates() -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    for symbol in ALL_SYMBOLS:
        role = "binding" if symbol in BINDING_SYMBOLS else "disclosure"
        for hold in HOLD_BARS:
            cost = cost_bps_for_hold(hold)
            # DI×VOL_HI — 3 vol × 3 hold × 3 sym
            for vol in VOL_THRS:
                cid = candidate_id(symbol, FILTER_DI, vol, None, hold)
                cells.append(
                    {
                        "candidate_id": cid,
                        "run_dir": cid,
                        "symbol": symbol,
                        "instrument_id": f"{symbol}-LINEAR.BYBIT",
                        "role": role,
                        "filter_model": FILTER_DI,
                        "vol_thr": vol,
                        "adx_min": None,
                        "hold_bars": hold,
                        "hold_mult": HOLD_MULT[hold],
                        "domain": "4h/15m",
                        "ltf_base": "UNF",
                        "polarity": "with-HTF",
                        "cost_bps": cost["cost_bps"],
                        "cost_breakdown": cost,
                        "money_per_unit": 1.0,
                        "cost_stack": COST_STACK,
                    }
                )
            # DI_ADX×VOL_HI — 3 vol × 3 adx × 3 hold × 3 sym
            for vol in VOL_THRS:
                for adx in ADX_MINS:
                    cid = candidate_id(symbol, FILTER_DI_ADX, vol, adx, hold)
                    cells.append(
                        {
                            "candidate_id": cid,
                            "run_dir": cid,
                            "symbol": symbol,
                            "instrument_id": f"{symbol}-LINEAR.BYBIT",
                            "role": role,
                            "filter_model": FILTER_DI_ADX,
                            "vol_thr": vol,
                            "adx_min": adx,
                            "hold_bars": hold,
                            "hold_mult": HOLD_MULT[hold],
                            "domain": "4h/15m",
                            "ltf_base": "UNF",
                            "polarity": "with-HTF",
                            "cost_bps": cost["cost_bps"],
                            "cost_breakdown": cost,
                            "money_per_unit": 1.0,
                            "cost_stack": COST_STACK,
                        }
                    )
    return cells


def build_manifest(*, extend_test: bool = False) -> dict[str, Any]:
    fence = load_fence_manifest()
    bands = stage_bands_from_fence(fence, extend_test=extend_test)
    candidates = build_candidates()
    reg_body = pin_body_sha256(REGISTRY_PATH) if REGISTRY_PATH.exists() else None
    reg_file = _sha256_file(REGISTRY_PATH) if REGISTRY_PATH.exists() else None
    # verify_frozen_registry equivalent (raises on mismatch)
    if reg_body is not None and reg_body != DESIGN_PIN_BODY_SHA:
        raise RuntimeError(
            f"INFR-015 pin body sha {reg_body} != design claim {DESIGN_PIN_BODY_SHA}"
        )
    pin_artifact = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if pin_artifact.get("sha256") != reg_body:
        raise RuntimeError("registry artifact sha256 field != recomputed body digest")
    n_di = sum(1 for c in candidates if c["filter_model"] == FILTER_DI)
    n_di_adx = sum(1 for c in candidates if c["filter_model"] == FILTER_DI_ADX)
    n_bind = sum(1 for c in candidates if c["role"] == "binding")
    n_disc = sum(1 for c in candidates if c["role"] == "disclosure")
    if len(candidates) != 108:
        raise RuntimeError(f"expected 108 cells, got {len(candidates)}")
    if n_di != 27 or n_di_adx != 81:
        raise RuntimeError(f"grid split wrong: DI={n_di} DI_ADX={n_di_adx}")

    return {
        "universe_id": UNIVERSE_ID,
        "family": FAMILY,
        "lane": "XENA",
        "schema": "xena.universe_manifest.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "n_candidates": len(candidates),
        "n_binding": n_bind,
        "n_disclosure": n_disc,
        "grid": {
            "domain": "4h/15m",
            "ltf_base": "UNF",
            "filter_models": [FILTER_DI, FILTER_DI_ADX],
            "vol_thr": list(VOL_THRS),
            "adx_min": list(ADX_MINS),
            "hold_bars": list(HOLD_BARS),
            "polarity": "with-HTF",
            "n_di_vol": n_di,
            "n_di_adx_vol": n_di_adx,
        },
        "instruments": {
            "binding": list(BINDING_SYMBOLS),
            "disclosure": list(DISCLOSURE_SYMBOLS),
            "note": "SPDR-006 §10 caveat 2 supersedes ckpt-013 §5 online-10 (operator 2026-07-18)",
        },
        "feature_pin": {
            "source": "python/experiments/SPDR-006/screen_code/spdr006_screen.py",
            "atr_period": 14,
            "adx_period": 14,
            "vol_median_w": 100,
            "retune": False,
        },
        "stage_bands": bands,
        "registry": {
            "path": str(REGISTRY_PATH.relative_to(REPO)),
            "sha256": reg_body,
            "sha256_file_bytes_disclosure": reg_file,
            "sha256_design_claimed": DESIGN_PIN_BODY_SHA,
            "verify_frozen_registry": "PASS",
            "sha256_match_design": reg_body == DESIGN_PIN_BODY_SHA,
            "class_id": "CLS-FILTER",
            "cadence": "LOW_ONLY_CERTIFY",
            "binder": "two_stage_sample_split",
            "cost_stack": COST_STACK,
            "stage1_score_kind": "g_net",
            "stage1_charge_costs": True,
            "e2e_pass_event": "stage2_gross_lcb_positive",
            "note": "pin digest is registry body sha (abbb1842…); file-bytes sha differs and is not the pin",
        },
        "topology": {
            "batch": "multi_instrument_single_node",
            "dispose_on_completion": False,
            "one_node_per_process": True,
            "lessons": ["L-30", "L-31"],
            "s1_smoke": "INFR-014 S1 PASS",
        },
        "emission": {
            "contract": "nautilus-emission-v1",
            "sl_price": "synthetic finite EntryFill - side * 1.0 * HTF_ATR14",
            "live_stop_order": False,
            "catalog_version": CATALOG_VERSION,
            "runs_root": str(RUNS_ROOT.relative_to(REPO)),
        },
        "candidates": candidates,
    }


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="XENA-HTFCAP-001 universe/bands builder")
    ap.add_argument("--extend-test", action="store_true",
                    help="AMENDMENT-4 (operator 2026-07-18): stage bands over TRAIN+TEST "
                    "(2022-07-14 → holdout_start), exploratory; holdout sealed")
    args = ap.parse_args()
    RESULTS.mkdir(parents=True, exist_ok=True)
    RUNS_ROOT.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(extend_test=args.extend_test)
    if args.extend_test:
        print("EXTEND-TEST (AMENDMENT-4): stage bands over TRAIN+TEST — exploratory, no OOS")
    text = json.dumps(manifest, indent=2, sort_keys=False) + "\n"
    out_runs = RUNS_ROOT / "universe_manifest.json"
    out_res = RESULTS / "universe_manifest.json"
    out_bands = RESULTS / "stage_bands.json"
    out_runs.write_text(text, encoding="utf-8")
    out_res.write_text(text, encoding="utf-8")
    out_bands.write_text(
        json.dumps(manifest["stage_bands"], indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"WROTE {out_runs}  n={manifest['n_candidates']} "
        f"binding={manifest['n_binding']} disclosure={manifest['n_disclosure']}"
    )
    print(
        f"  registry_sha={manifest['registry']['sha256']} "
        f"verify={manifest['registry']['verify_frozen_registry']} "
        f"match_design={manifest['registry']['sha256_match_design']}"
    )
    sb = manifest["stage_bands"]
    print(f"  search  {sb['search']['start_utc']} → {sb['search']['end_utc']}")
    print(f"  ranking {sb['ranking']['start_utc']} → {sb['ranking']['end_utc']}")
    print(f"  stage2  {sb['stage2_gate']['start_utc']} → {sb['stage2_gate']['end_utc']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
