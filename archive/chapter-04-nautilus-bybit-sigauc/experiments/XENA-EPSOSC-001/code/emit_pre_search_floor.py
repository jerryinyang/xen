#!/usr/bin/env python3
"""XENA-EPSOSC-001 pre-search gross-floor + cadence/F*=16 coverage attestation.

Design §4.3 + §6 / XENA-003:
  - Per-cell TRAIN median gross bps/episode vs bybit_round_trip_cost_bps_v1
    breakeven (fees + GAP spread + funding × episode duration).
  - Entire binding mass sub-breakeven → park recommendation before search.
  - Cadence attestation: per-candidate episode counts + median duration; HIGH-
    shaped streams (median ~1h / dense) outside CLS-EPISODE LOW certification.
  - F*=16 reachability: expected stage-2/gate-band legs ≥16 for certified
    subsets (disclosed; single-cell may fall under floor — design §10).

Sources (priority):
  1. Nautilus emission legs via xen.nautilus.adjudication_shim → RealizedBps
     (no local accounting).
  2. Else feature-replay on fenced TRAIN using frozen SPDR-005 defs (no retune)
     — labelled source=feature_replay_pre_emission.

Usage (from python/):
  uv run python experiments/XENA-EPSOSC-001/code/build_universe.py --reuse-spdr-membership
  uv run python experiments/XENA-EPSOSC-001/code/emit_pre_search_floor.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from tqdm import tqdm

CODE = Path(__file__).resolve().parent
EXP = CODE.parent
ROOT = EXP.parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(CODE))

from features import (  # noqa: E402
    ATR_PERIOD,
    ATR_SLOW,
    VOLARM_RATIO,
    batch_event_mask,
    causal_rolling_median,
    wilder_atr_pair,
)
from xen.bar_aggregator import aggregate_ohlc  # noqa: E402
from xen.evaluation import (  # noqa: E402
    BYBIT_FUNDING_CONSERVATIVE_BPS_PER_8H,
    bybit_round_trip_cost_bps,
)
from xen.nautilus.adjudication_shim import emission_to_adjudication_frames  # noqa: E402
from xen.nautilus.catalog_fence import fenced_bar_query, load_fence_manifest  # noqa: E402

UNIVERSE_ID = "XENA-EPSOSC-001"
RUNS_ROOT = REPO / "data" / "nautilus_runs" / UNIVERSE_ID
MANIFEST_PATH = RUNS_ROOT / "universe_manifest.json"
MEMBERSHIP_PATH = RUNS_ROOT / "membership.parquet"
RESULTS = EXP / "results"
CATALOG_PATH = REPO / "data" / "catalog"
GAP_SPREAD_BPS = 5.0
NS_PER_MIN = 60_000_000_000
N_LEGS_FLOOR = 16  # F* pin
# LOW cadence prior: med duration ~19–20h; HIGH ~1h
HIGH_CADENCE_MED_HOURS = 2.0  # below this med → HIGH-shaped (outside pin)


def load_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"run build_universe.py first — missing {MANIFEST_PATH}")
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def median_gross_from_emission(emission_dir: Path) -> tuple[float, int, float, float, str]:
    """Return (median_gross_bps, n_legs, med_dur_h, cens_frac, source) via shim."""
    if not (emission_dir / "run_metadata.json").exists():
        return float("nan"), 0, float("nan"), float("nan"), "missing"
    try:
        _pos, cis, _meta = emission_to_adjudication_frames(emission_dir)
    except Exception as e:  # noqa: BLE001
        return float("nan"), 0, float("nan"), float("nan"), f"error:{e}"
    if cis.height == 0:
        return float("nan"), 0, float("nan"), 0.0, "emission_empty"
    cens_frac = float(cis.filter(pl.col("Censored").cast(pl.Boolean)).height / cis.height)
    live = cis.filter(
        pl.col("Censored").cast(pl.Boolean).not_() & pl.col("RealizedBps").is_finite()
    )
    if live.height == 0:
        return float("nan"), 0, float("nan"), cens_frac, "emission_all_censored"
    r = live.get_column("RealizedBps").to_numpy().astype(float)
    # duration hours from Entry/Exit if present
    med_h = float("nan")
    if "EntryTime" in live.columns and "ExitTime" in live.columns:
        et = live.get_column("EntryTime")
        xt = live.get_column("ExitTime")
        try:
            ens = et.dt.epoch("ns").to_numpy().astype(np.int64)
            xns = xt.dt.epoch("ns").to_numpy().astype(np.int64)
            hrs = (xns - ens) / 3.6e12
            hrs = hrs[np.isfinite(hrs) & (hrs > 0)]
            if hrs.size:
                med_h = float(np.median(hrs))
        except Exception:  # noqa: BLE001
            med_h = float("nan")
    return float(np.median(r)), int(r.size), med_h, cens_frac, "nautilus_emission"


def load_train_1m(symbol: str, fence) -> pl.DataFrame:
    catalog = ParquetDataCatalog(str(CATALOG_PATH))
    bars = fenced_bar_query(
        catalog,
        [f"{symbol}-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL"],
        start=fence.analysis_start_utc,
        end=fence.train_end_utc,
        band="TRAIN",
        manifest=fence,
    )
    if not bars:
        return pl.DataFrame()
    close_ns = np.array([b.ts_event for b in bars], dtype=np.int64)
    open_ns = close_ns - NS_PER_MIN
    return pl.DataFrame(
        {
            "Symbol": [symbol] * len(bars),
            "OpenTime": open_ns,
            "CloseTime": close_ns,
            "Open": [float(b.open) for b in bars],
            "High": [float(b.high) for b in bars],
            "Low": [float(b.low) for b in bars],
            "Close": [float(b.close) for b in bars],
            "TickVolume": [float(b.volume) for b in bars],
        }
    ).with_columns(
        pl.from_epoch("OpenTime", time_unit="ns").dt.replace_time_zone("UTC").alias("OpenTime"),
        pl.from_epoch("CloseTime", time_unit="ns").dt.replace_time_zone("UTC").alias("CloseTime"),
    ).sort("CloseTime")


def load_member_mask(
    symbol: str, open_ns: np.ndarray, membership: pl.DataFrame
) -> np.ndarray:
    """Boolean membership aligned to LTF opens (UTC day rebalance set)."""
    n = len(open_ns)
    member = np.zeros(n, dtype=bool)
    if membership is None or membership.height == 0:
        return member
    sym_m = membership.filter(pl.col("symbol") == symbol)
    if sym_m.height == 0:
        return member
    reb = sym_m.get_column("rebalance_ts")
    if reb.dtype != pl.Int64:
        reb_ns = reb.dt.epoch("ns").to_numpy().astype(np.int64)
    else:
        reb_ns = reb.to_numpy().astype(np.int64)
    day_set = set(int(x) for x in reb_ns)
    NS_DAY = 86_400_000_000_000
    for i, ons in enumerate(open_ns):
        day_ns = (int(ons) // NS_DAY) * NS_DAY
        member[i] = day_ns in day_set
    return member


def feature_replay_episodes(
    train_1m: pl.DataFrame,
    membership: pl.DataFrame,
    *,
    symbol: str,
    object_type: str,
    ltf_min: int,
    w: int,
    k: float,
    clear: str,
    side: str,
    train_end_ns: int | None,
) -> dict[str, Any]:
    """Gross open-to-open bps/episode via frozen SPDR-005 episode engine (floor only)."""
    empty = {
        "returns": np.array([], dtype=np.float64),
        "durations_h": np.array([], dtype=np.float64),
        "n_episodes": 0,
        "n_started": 0,
        "n_censored": 0,
        "censored_frac": 0.0,
    }
    if train_1m.is_empty() or train_1m.height < ltf_min * (w + ATR_SLOW + 5):
        return empty
    ltf = aggregate_ohlc(train_1m, period_minutes=ltf_min, min_coverage=0.90).sort("CloseTime")
    if ltf.height < w + ATR_SLOW + 5:
        return empty

    o = ltf["Open"].to_numpy().astype(np.float64)
    h = ltf["High"].to_numpy().astype(np.float64)
    l = ltf["Low"].to_numpy().astype(np.float64)
    c = ltf["Close"].to_numpy().astype(np.float64)
    open_ns = ltf.select(pl.col("OpenTime").dt.epoch("ns")).to_series().to_numpy().astype(np.int64)
    atr, atr_s = wilder_atr_pair(h, l, c)
    atr_prev = np.concatenate([[np.nan], atr[:-1]])
    atr_slow_prev = np.concatenate([[np.nan], atr_s[:-1]])
    anchor = causal_rolling_median(c, w)
    a_prev = np.concatenate([[np.nan], anchor[:-1]])
    c_prev = np.concatenate([[np.nan], c[:-1]])
    member = load_member_mask(symbol, open_ns, membership)
    # event mask at entry bar t uses features [t-1]
    _ev, direction = batch_event_mask(
        c_prev,
        atr_prev,
        atr_slow_prev,
        a_prev,
        member,
        k,
        volarm=(object_type == "VOLARM"),
    )
    want = 1 if side == "LONG_ONLY" else -1
    cand = np.nonzero((direction == want) & np.isfinite(o) & (o > 0) & member)[0]
    if cand.size == 0:
        return empty

    h_time = int(w)
    thr = 0.25 * k
    r_list: list[float] = []
    dur_h: list[float] = []
    n_censored = 0
    n_started = 0
    i = 0
    m = len(cand)
    n = len(o)
    while i < m:
        t_entry = int(cand[i])
        d = int(direction[t_entry])
        if d == 0 or t_entry >= n - 1:
            i += 1
            continue
        n_started += 1
        t_exit = -1
        scan_end = min(n - 1, t_entry + h_time) if clear == "HYBRID" else (n - 1)
        cleared = False
        for t in range(t_entry + 1, scan_end + 1):
            ap, cp, atrv = a_prev[t], c_prev[t], atr_prev[t]
            if not (np.isfinite(ap) and np.isfinite(cp) and np.isfinite(atrv) and atrv > 0):
                continue
            dist = abs(cp - ap) / atrv
            crossed = (d == 1 and cp >= ap) or (d == -1 and cp <= ap)
            if dist < thr or crossed:
                t_exit = t
                cleared = True
                break
        if not cleared:
            if clear == "HYBRID":
                t_exit = t_entry + h_time
                if t_exit >= n:
                    n_censored += 1
                    break
            else:
                n_censored += 1
                break
        if t_exit <= t_entry or t_exit >= n:
            n_censored += 1
            i += 1
            continue
        if train_end_ns is not None and int(open_ns[t_exit]) >= train_end_ns:
            n_censored += 1
            i = int(np.searchsorted(cand, t_exit + 1, side="left"))
            continue
        o0, o1 = o[t_entry], o[t_exit]
        r_bps = d * (o1 - o0) / o0 * 1e4
        if np.isfinite(r_bps):
            r_list.append(float(r_bps))
            hours = (open_ns[t_exit] - open_ns[t_entry]) / 3.6e12
            dur_h.append(float(hours) if hours > 0 else float("nan"))
        i = int(np.searchsorted(cand, t_exit + 1, side="left"))

    r = np.asarray(r_list, dtype=np.float64)
    dh = np.asarray(dur_h, dtype=np.float64)
    return {
        "returns": r,
        "durations_h": dh,
        "n_episodes": int(r.size),
        "n_started": n_started,
        "n_censored": n_censored,
        "censored_frac": float(n_censored / max(1, n_started)) if n_started else 0.0,
    }


def breakeven_bps(hold_hours: float) -> dict[str, float]:
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
        "breakeven_bps": float(d["total_bps"]),
        "fee_rt_bps": float(d["fee_rt_bps"]),
        "spread_rt_bps": float(d["spread_rt_bps"]),
        "funding_rt_bps": float(d["funding_rt_bps"]),
        "hold_hours": hold_hours,
    }


def band_leg_expectation(n_full: int, stage_bands: dict[str, Any]) -> dict[str, float]:
    """Rough per-band episode expectation from full-TRAIN count × pin fracs."""
    # search 0.5 / ranking 0.25 / gate ~ remaining after embargo 0.2 of usable
    # Usable ≈ 1 - embargo on the post-embargo split; pin uses fracs on usable span.
    # Approximate gate share ≈ 0.25 of full when embargo=0.2, search=0.5, ranking=0.25
    # of usable (0.8): gate = 0.25*0.8 = 0.20 of full span.
    search_f = float(stage_bands.get("search_frac", 0.5))
    rank_f = float(stage_bands.get("ranking_frac", 0.25))
    emb = float(stage_bands.get("embargo_frac", 0.2))
    usable = 1.0 - emb
    gate_f = max(0.0, usable - search_f * usable - rank_f * usable)
    # Actually SegmentLayout: search_frac/ranking_frac of (span - purge); purge=embargo*span
    # search share of full ≈ search_frac * (1-embargo)
    s_share = search_f * usable
    r_share = rank_f * usable
    g_share = usable - s_share - r_share
    return {
        "search_expected_legs": n_full * s_share,
        "ranking_expected_legs": n_full * r_share,
        "gate_expected_legs": n_full * g_share,
        "search_share": s_share,
        "ranking_share": r_share,
        "gate_share": g_share,
    }


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    fence = load_fence_manifest()
    manifest = load_manifest()
    candidates = manifest["candidates"]
    stage_bands = manifest.get("stage_bands") or {}
    train_end_ns = int(fence.train_end_utc.timestamp() * 1e9)

    membership = (
        pl.read_parquet(MEMBERSHIP_PATH) if MEMBERSHIP_PATH.exists() else pl.DataFrame()
    )

    train_cache: dict[str, pl.DataFrame] = {}
    rows: list[dict[str, Any]] = []

    for cell in tqdm(candidates, desc="floor+cadence"):
        cid = cell["candidate_id"]
        symbol = cell["symbol"]
        hold_h_prior = float(
            (cell.get("cost_breakdown") or {}).get("hold_hours") or 20.0
        )
        emission_dir = RUNS_ROOT / cid
        med, n_legs, med_h, cens_frac, source = median_gross_from_emission(emission_dir)

        if source in ("missing", "emission_empty", "emission_all_censored") or (
            isinstance(source, str) and source.startswith("error")
        ):
            if symbol not in train_cache:
                train_cache[symbol] = load_train_1m(symbol, fence)
            ep = feature_replay_episodes(
                train_cache[symbol],
                membership,
                symbol=symbol,
                object_type=cell["object_type"],
                ltf_min=int(cell["ltf_minutes"]),
                w=int(cell["w"]),
                k=float(cell["k"]),
                clear=cell["clear_policy"],
                side=cell["side_mode"],
                train_end_ns=train_end_ns,
            )
            n_legs = int(ep["n_episodes"])
            med = float(np.median(ep["returns"])) if n_legs else float("nan")
            dh = ep["durations_h"]
            med_h = float(np.median(dh[np.isfinite(dh)])) if len(dh) else float("nan")
            cens_frac = float(ep["censored_frac"])
            source = "feature_replay_pre_emission"
            hold_h = med_h if med_h == med_h and med_h > 0 else hold_h_prior
        else:
            hold_h = med_h if med_h == med_h and med_h > 0 else hold_h_prior

        be = breakeven_bps(hold_h)
        above = bool(np.isfinite(med) and med >= be["breakeven_bps"])
        band_exp = band_leg_expectation(n_legs, stage_bands)
        gate_n = band_exp["gate_expected_legs"]
        cadence = "LOW"
        if med_h == med_h and med_h < HIGH_CADENCE_MED_HOURS and n_legs > 0:
            # dense short episodes → outside CLS-EPISODE LOW certification
            cadence = "HIGH_SHAPED"
        f_star_ok_cell = bool(gate_n >= N_LEGS_FLOOR)
        rows.append(
            {
                "candidate_id": cid,
                "symbol": symbol,
                "role": cell["role"],
                "object_type": cell["object_type"],
                "ltf_minutes": cell["ltf_minutes"],
                "w": cell["w"],
                "k": cell["k"],
                "clear_policy": cell["clear_policy"],
                "side_mode": cell["side_mode"],
                "n_episodes": n_legs,
                "median_gross_bps": med,
                "median_duration_h": med_h,
                "censored_frac": cens_frac,
                "breakeven_bps": be["breakeven_bps"],
                "fee_rt_bps": be["fee_rt_bps"],
                "spread_rt_bps": be["spread_rt_bps"],
                "funding_rt_bps": be["funding_rt_bps"],
                "hold_hours_costed": hold_h,
                "median_minus_breakeven": (
                    med - be["breakeven_bps"] if np.isfinite(med) else float("nan")
                ),
                "above_breakeven": above,
                "cadence_class": cadence,
                "gate_expected_legs": gate_n,
                "search_expected_legs": band_exp["search_expected_legs"],
                "ranking_expected_legs": band_exp["ranking_expected_legs"],
                "f_star_16_cell_reachable": f_star_ok_cell,
                "source": source,
                "cost_stack": "bybit_round_trip_cost_bps_v1",
                "spread_label": "GAP",
            }
        )

    df = pl.DataFrame(rows)
    out_pq = RESULTS / "pre_search_gross_floor.parquet"
    out_csv = RESULTS / "pre_search_gross_floor.csv"
    df.write_parquet(out_pq)
    df.write_csv(out_csv)

    bind = df.filter(pl.col("role") == "binding")
    n_bind = bind.height
    n_above = bind.filter(pl.col("above_breakeven")).height if n_bind else 0
    n_sub = n_bind - n_above
    all_sub = n_bind > 0 and n_above == 0

    # Cadence attestation
    n_high = int(bind.filter(pl.col("cadence_class") == "HIGH_SHAPED").height) if n_bind else 0
    n_low = n_bind - n_high
    # F* portfolio pooling note: K≥3 cells pool legs
    bind_gate = (
        bind.get_column("gate_expected_legs").to_numpy().astype(float) if n_bind else np.array([])
    )
    n_cell_fstar = int(np.sum(bind_gate >= N_LEGS_FLOOR)) if bind_gate.size else 0
    # expected top subset: sum of top-3 gate expectations (optimistic pool)
    top3_pool = float(np.sum(np.sort(bind_gate)[::-1][:3])) if bind_gate.size else 0.0

    cadence_attest = {
        "universe_id": UNIVERSE_ID,
        "pin_class": "CLS-EPISODE",
        "pin_cadence": "LOW_ONLY_CERTIFY",
        "true_alpha_priced_le": 0.06,
        "true_alpha_note": (
            "INFR-015 CLS-EPISODE pin caveat 1: true α priced plausibly ≤ ~0.06; "
            "state alongside every gate result (design §9 / §1)"
        ),
        "n_binding_cells": n_bind,
        "n_binding_LOW": n_low,
        "n_binding_HIGH_SHAPED": n_high,
        "HIGH_shaped_outside_certification": n_high > 0,
        "HIGH_note": (
            "median duration < 2h → HIGH-shaped; no gate spend on HIGH-shaped streams "
            "(design §4.3)"
            if n_high
            else "no HIGH-shaped binding cells under med-duration prior"
        ),
        "F_star": N_LEGS_FLOOR,
        "n_binding_cells_gate_expected_ge_Fstar": n_cell_fstar,
        "top3_pool_gate_expected_legs": top3_pool,
        "portfolio_Fstar_reachable": bool(top3_pool >= N_LEGS_FLOOR),
        "Fstar_note": (
            "single-cell stage-2 may fall under F*=16 (design §10 / pin ood 0.75); "
            "certified SUBSETS pool legs — top-3 gate expectation disclosed"
        ),
        "median_duration_h_binding_p50": (
            float(bind["median_duration_h"].median()) if n_bind else None
        ),
        "median_n_episodes_binding_p50": (
            float(bind["n_episodes"].median()) if n_bind else None
        ),
    }
    (RESULTS / "cadence_fstar_attestation.json").write_text(
        json.dumps(cadence_attest, indent=2) + "\n", encoding="utf-8"
    )

    summary = {
        "universe_id": UNIVERSE_ID,
        "generated_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "n_cells": df.height,
        "n_binding": n_bind,
        "n_disclosure": df.height - n_bind,
        "n_binding_above_breakeven": n_above,
        "n_binding_sub_breakeven": n_sub,
        "entire_binding_mass_sub_breakeven": all_sub,
        "park_recommendation": (
            "PARK before search — entire binding mass sub-breakeven (design §6 / family kill row)"
            if all_sub
            else "PROCEED — at least one binding cell ≥ breakeven (individual sub-floor cells still enter)"
        ),
        "cost_stack": "bybit_round_trip_cost_bps_v1",
        "funding": "included (GAP conservative 1.0 bps/8h × episode hold_hours)",
        "spread_label": "GAP 5.0 bps (per-symbol pin deferred; re-measure before search)",
        "sources": df.group_by("source").len().to_dicts(),
        "binding_median_gross_bps_p50": (
            float(bind["median_gross_bps"].median()) if n_bind else None
        ),
        "cadence_fstar_attestation": cadence_attest,
        "paths": {
            "parquet": str(out_pq.relative_to(REPO)),
            "csv": str(out_csv.relative_to(REPO)),
            "cadence_fstar": str(
                (RESULTS / "cadence_fstar_attestation.json").relative_to(REPO)
            ),
        },
    }
    out_sum = RESULTS / "pre_search_gross_floor_summary.json"
    out_sum.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"WROTE {out_pq}")
    print(f"WROTE {out_csv}")
    print(f"WROTE {out_sum}")
    print(f"WROTE {RESULTS / 'cadence_fstar_attestation.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
