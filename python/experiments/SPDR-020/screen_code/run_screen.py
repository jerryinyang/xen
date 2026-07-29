#!/usr/bin/env python3
"""SPDR-020 orchestrator — phase (a) only, TRAIN-only, SPDR-014 object + L4 capture.

    python run_screen.py --jobs 8
    python run_screen.py --jobs 8 --resume
    python run_screen.py --smoke   # 2 symbols, reduced bootstrap / primary grid

Work unit = one symbol. Grid axes applied inside. Polars requires spawn (not fork).
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import multiprocessing as mp
import subprocess
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from config import (  # noqa: E402
    BOOT_BLOCKS_DAYS_H1,
    BOOT_BLOCKS_DAYS_H4,
    BOOT_RESAMPLES,
    BANDS,
    CLOCKS_RUN,
    COST_FLOOR_BPS,
    DAY_NS,
    DERIVED_VARIANTS,
    EVENT_TYPES,
    EXPECTED_RESOLUTION_SHA256,
    H_PRIMARY,
    H_VALUES,
    H_POST,
    RESULTS_DIR,
    RESOLUTION_BASIS_SHA256,
    SIZING_VARIANTS,
    SOURCE_PRIMARY,
    SOURCES,
    SPREAD_COST_DISCLOSURE,
    TIMING_SEEDS,
    UNIVERSE_PIN_FAMILY,
    VARIANT_IDS,
    Z_VALUES,
    ZVOL_COVERED_N,
    ZVOL_NAN_SYMBOLS,
)
import controls as controls_mod  # noqa: E402
import event_engine  # noqa: E402
import fills_bridge  # noqa: E402
import golden  # noqa: E402
import layers  # noqa: E402
import metrics  # noqa: E402
import parent_parity  # noqa: E402
import prepare  # noqa: E402
import selection  # noqa: E402
import selfcheck  # noqa: E402
import provenance  # noqa: E402


def _shift_to_t_plus_one(values: np.ndarray) -> np.ndarray:
    shifted = np.full_like(values, np.nan, dtype=float)
    if values.size > 1:
        shifted[:-1] = values[1:]
    return shifted


def _tripwire_one_for_pack(pack) -> dict:
    """Rebuild primary event/layer pipeline from illegal t+1 inputs."""
    leaky = copy.deepcopy(pack)
    conditioning_names = (
        "sigma_zvol",
        "sigma_zmag",
        "s_hmm_rv",
        "p_rmarkov_k4",
        "p_rmarkov_k12",
        "tgtcur_fires",
        "p_stay",
        "n_prior_trans",
    )
    legal_columns = []
    leaky_columns = []
    for name in conditioning_names:
        values = np.asarray(getattr(pack, name), dtype=float)
        shifted = _shift_to_t_plus_one(values)
        setattr(leaky, name, shifted)
        legal_columns.append(values)
        leaky_columns.append(shifted)
    variants = tuple(v for v in VARIANT_IDS if v not in DERIVED_VARIANTS)
    kwargs = {
        "sources": tuple(SOURCES),
        "z_values": (1.5,),
        "H_values": (12,),
        "h_values": tuple(H_POST),
        "event_types": ("E-TOUCH",),
        "variants": variants,
    }
    _, _, legal_rows, _, _ = layers.run_grid_for_pack(pack, **kwargs)
    _, _, leaky_rows, _, _ = layers.run_grid_for_pack(leaky, **kwargs)

    def first_g1(rows: list[dict]) -> dict | None:
        frame = pd.DataFrame(rows)
        if frame.empty:
            return None
        selected = frame[
            (frame["variant_id"] == "L0_BASELINE")
            & (frame["source"] == "Z-VOL")
            & (frame["z"] == 1.5)
            & (frame["H"] == 12)
            & (frame["h"] == 12)
            & (frame["event_type"] == "E-TOUCH")
            & (frame["policy"] == "P-MR")
            & (frame["band"] == "DESIGN")
        ]
        return (
            selected.sort_values("entry_ts").iloc[0].to_dict()
            if not selected.empty else None
        )

    def material(rows: list[dict]) -> tuple[set[tuple], np.ndarray, np.ndarray]:
        frame = pd.DataFrame(rows)
        if frame.empty:
            return set(), np.empty(0), np.empty(0, dtype=np.int64)
        keys = {
            (
                row.symbol,
                row.source,
                row.variant_id,
                int(row.event_idx),
                row.policy,
                row.band,
            )
            for row in frame.itertuples()
        }
        l0 = frame[(frame["variant_id"] == "L0_BASELINE")]
        return (
            keys,
            l0["r_bps"].to_numpy(dtype=float),
            l0["entry_ts"].to_numpy(dtype=np.int64),
        )

    legal_keys, legal_r, legal_ts = material(legal_rows)
    leaky_keys, leaky_r, leaky_ts = material(leaky_rows)
    legal_conditioning = np.concatenate(legal_columns)
    leaky_conditioning = np.concatenate(leaky_columns)
    result = controls_mod.evaluate_tripwire_1(
        controls_mod.TripwireRun(
            legal_conditioning,
            legal_keys,
            legal_r,
            legal_ts,
        ),
        controls_mod.TripwireRun(
            leaky_conditioning,
            leaky_keys,
            leaky_r,
            leaky_ts,
        ),
        n_boot=BOOT_RESAMPLES,
    )
    result["covered_variants"] = list(variants)
    result["covered_sources"] = list(SOURCES)
    result["symbol"] = pack.symbol
    result["complete_layer_source_coverage"] = bool(
        set(variants).issubset({key[2] for key in legal_keys | leaky_keys})
        and set(SOURCES).issubset({key[1] for key in legal_keys | leaky_keys})
    )
    result["hard_pass"] = bool(
        result["hard_pass"] and result["complete_layer_source_coverage"]
    )
    legal_g1 = first_g1(legal_rows)
    leaky_g1 = first_g1(leaky_rows)
    result["g1_twin"] = {
        "legal": legal_g1,
        "leaky": leaky_g1,
        "changed": bool(
            legal_g1 is not None
            and leaky_g1 is not None
            and any(
                legal_g1.get(column) != leaky_g1.get(column)
                for column in (
                    "event_idx", "entry_idx", "entry_price", "exit_price", "r_bps"
                )
            )
        ),
    }
    return result


def _tripwire_two_for_pack(pack) -> dict:
    """Run legal and deliberately leaky detectors through the same zone walker."""
    common = {
        "source": "Z-VOL",
        "z": 1.5,
        "H": 12,
        "event_type": "E-TOUCH",
        "h": 12,
        "band": "TRAIN",
        "occupation_h": 24,
    }
    _, legal_events, legal_posts, legal_counts = event_engine.walk_zones(
        pack, **common
    )
    _, leaky_events, leaky_posts, leaky_counts = event_engine.walk_zones(
        pack, **common, illegal_future_touch_at_anchor=True
    )
    legal_by_origin = {int(row["t_idx"]): row for row in legal_events}
    leaky_by_origin = {int(row["t_idx"]): row for row in leaky_events}
    pairs = []
    for origin in sorted(set(legal_by_origin) & set(leaky_by_origin)):
        legal = legal_by_origin[origin]
        leaky = leaky_by_origin[origin]
        actual = int(leaky.get("actual_future_event_idx", -1))
        if legal["event"] and leaky["event"] and actual > int(leaky["anchor_idx"]):
            pairs.append({
                "origin_idx": origin,
                "anchor_idx": int(leaky["anchor_idx"]),
                "legal_event_idx": int(legal["event_idx"]),
                "leaky_event_idx": int(leaky["event_idx"]),
                "actual_future_event_idx": actual,
            })
    legal_frame = pd.DataFrame(legal_posts)
    leaky_frame = pd.DataFrame(leaky_posts)
    if legal_frame.empty or leaky_frame.empty:
        return {
            "hard_pass": False,
            "future_touch_zones": len(pairs),
            "early_entry_count": 0,
            "event_index_pairs": pairs,
            "evidence_source": "independent_legal_and_illegal_walk_zones_runs",
            "reason": "no_common_decided_posts",
        }
    common_origins = sorted(
        set(legal_frame.get("t_idx", pd.Series(dtype=int)))
        & set(leaky_frame.get("t_idx", pd.Series(dtype=int)))
    )
    legal_frame = legal_frame[legal_frame["t_idx"].isin(common_origins)]
    leaky_frame = leaky_frame[leaky_frame["t_idx"].isin(common_origins)]
    if not common_origins:
        return {
            "hard_pass": False,
            "future_touch_zones": len(pairs),
            "early_entry_count": 0,
            "event_index_pairs": pairs,
            "evidence_source": "independent_legal_and_illegal_walk_zones_runs",
            "reason": "no_common_origins",
        }
    legal_frame = legal_frame.sort_values("t_idx")
    leaky_frame = leaky_frame.sort_values("t_idx")
    result = controls_mod.evaluate_tripwire_2(
        pairs,
        live_returns=legal_frame["r_h"].to_numpy(dtype=float),
        leaky_returns=leaky_frame["r_h"].to_numpy(dtype=float),
        timestamps=legal_frame["entry_ts"].to_numpy(dtype=np.int64),
        n_boot=BOOT_RESAMPLES,
        live_p_event=legal_counts["p_event"],
        leaky_p_event=leaky_counts["p_event"],
        future_touch_zones=len(pairs),
    )
    result["evidence_source"] = "independent_legal_and_illegal_walk_zones_runs"
    return result


def _rerun_control_rows(
    frame: pd.DataFrame,
    exit_rule: str,
    *,
    s_pin: dict[str, float],
    bundle_cache: dict[str, dict],
) -> np.ndarray:
    """Rerun entry, fill, exit, and signed return for a control arm."""
    returns = []
    for row in frame.itertuples():
        if row.symbol not in bundle_cache:
            bundle = prepare.load_symbol_bundle(row.symbol, s_pin=s_pin)
            if bundle is None:
                raise ValueError(f"missing TRAIN bundle for {row.symbol}")
            bundle_cache[row.symbol] = bundle
        pack = bundle_cache[row.symbol]["packs"][row.clock]
        entry_idx = int(row.entry_idx)
        if entry_idx < 0 or entry_idx >= pack.open.size:
            returns.append(float("nan"))
            continue
        entry_ts = int(pack.slot_start[entry_idx])
        entry_price = float(pack.open[entry_idx])
        side = int(row.side)
        h_use = float(getattr(row, "h_use", row.h))
        meta = (
            layers._parse_l4(exit_rule)
            if str(exit_rule).startswith("L4_")
            else {"device": "time"}
        )
        target = trail_width = None
        weight = 1.0
        if str(exit_rule).startswith("L4_"):
            origin = int(getattr(row, "forecast_origin_t0", row.event_idx))
            try:
                target, trail_width, weight, _ = layers._exit_params(
                    pack,
                    entry_price=entry_price,
                    event_idx=origin,
                    source=row.source,
                    trade_side=side,
                    variant_id=exit_rule,
                    meta=meta,
                    h_bars=h_use,
                    clock=row.clock,
                )
            except ValueError:
                returns.append(float("nan"))
                continue
        exit_idx = entry_idx + int(round(h_use))
        if exit_idx >= pack.open.size:
            returns.append(float("nan"))
            continue
        if meta.get("device") in ("target", "trail"):
            fill_m1 = fills_bridge.first_m1_at_or_after(pack.m1["ts"], entry_ts)
            active_ns = int(pack.slot_start[exit_idx]) - entry_ts
            exit_fill = fills_bridge.resolve_target_trail_time(
                pack.m1,
                pack.open,
                pack.slot_start,
                side=side,
                entry_price=entry_price,
                fill_ts=entry_ts,
                fill_m1_idx=fill_m1,
                active_hold_ns=active_ns,
                target_price=target,
                trail_width_price=trail_width,
            )
            if exit_fill is None:
                returns.append(float("nan"))
                continue
            exit_price = float(exit_fill.exit_price)
        else:
            exit_price = float(pack.open[exit_idx])
        value = fills_bridge.signed_r_bps(side, entry_price, exit_price)
        returns.append(value * weight if meta.get("device") == "size" else value)
    return np.asarray(returns, dtype=float)


def _episode_event_key(frame: pd.DataFrame) -> pd.Series:
    columns = [
        c for c in (
            "symbol", "clock", "source", "z", "H", "event_type", "h",
            "policy", "band", "event_idx",
        ) if c in frame.columns
    ]
    return frame[columns].astype(str).agg("|".join, axis=1)


def _magnitude_control_candidates(episodes: pd.DataFrame) -> pd.DataFrame:
    base = episodes[
        (episodes["variant_id"] == "L0_BASELINE")
        & (episodes["clock"] == "H1")
        & (episodes["source"] == "Z-VOL")
        & np.isclose(episodes["z"].astype(float), 1.5)
        & (episodes["H"] == 12)
        & (episodes["h"] == 12)
        & (episodes["event_type"] == "E-TOUCH")
        & (episodes["policy"] == "P-MOMO")
        & ~episodes["suppressed"].fillna(False).astype(bool)
    ].copy()
    selected = episodes[
        (episodes["variant_id"] == "L2_SHOCK_HMM")
        & (episodes["clock"] == "H1")
        & (episodes["source"] == "Z-VOL")
        & np.isclose(episodes["z"].astype(float), 1.5)
        & (episodes["H"] == 12)
        & (episodes["h"] == 12)
        & (episodes["event_type"] == "E-TOUCH")
        & (episodes["policy"] == "P-MOMO")
    ].copy()
    if base.empty:
        return pd.DataFrame()
    base["event_key"] = _episode_event_key(base)
    selected_keys = set(_episode_event_key(selected)) if not selected.empty else set()
    base["selected"] = base["event_key"].isin(selected_keys)
    ranks = base["decision_move_bps"].rank(method="first")
    base["move_decile"] = pd.qcut(
        ranks,
        q=min(10, len(base)),
        labels=False,
        duplicates="drop",
    ).fillna(0).astype(int)
    return base[["event_key", "selected", "move_decile", "r_bps"]]


def _ambient_control_candidates(
    episodes: pd.DataFrame,
    events: pd.DataFrame,
    *,
    s_pin: dict[str, float],
    bundle_cache: dict[str, dict],
) -> pd.DataFrame:
    live = episodes[
        (episodes["variant_id"] == "L0_BASELINE")
        & (episodes["clock"] == "H1")
        & (episodes["source"] == "Z-VOL")
        & np.isclose(episodes["z"].astype(float), 1.5)
        & (episodes["H"] == 12)
        & (episodes["h"] == 12)
        & (episodes["event_type"] == "E-TOUCH")
        & (episodes["policy"] == "P-MOMO")
    ].copy()
    rows = [
        {
            "event_key": key,
            "is_breach": True,
            "r_bps": float(r),
        }
        for key, r in zip(_episode_event_key(live), live["r_bps"])
    ]
    no_breach = events[
        (events["clock"] == "H1")
        & (events["source"] == "Z-VOL")
        & np.isclose(events["z"].astype(float), 1.5)
        & (events["H"] == 12)
        & (events["event_type"] == "E-TOUCH")
        & (events["event"] == 0)
    ]
    live_sides = live["side"].to_numpy(dtype=int)
    for number, event in enumerate(no_breach.itertuples()):
        if event.symbol not in bundle_cache:
            bundle = prepare.load_symbol_bundle(event.symbol, s_pin=s_pin)
            if bundle is None:
                continue
            bundle_cache[event.symbol] = bundle
        pack = bundle_cache[event.symbol]["packs"]["H1"]
        entry_idx = int(event.anchor_idx) + 1
        exit_idx = entry_idx + 12
        if exit_idx >= pack.open.size:
            continue
        side = int(live_sides[number % len(live_sides)]) if live_sides.size else 1
        value = fills_bridge.signed_r_bps(
            side,
            float(pack.open[entry_idx]),
            float(pack.open[exit_idx]),
        )
        rows.append({
            "event_key": (
                f"{event.symbol}|H1|Z-VOL|1.5|12|E-TOUCH|12|"
                f"AMBIENT|{event.band}|{event.t_idx}"
            ),
            "is_breach": False,
            "r_bps": value,
        })
    return pd.DataFrame(rows)


def _json(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, Path):
        return str(o)
    return str(o)


def write_json(name: str, payload) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    p = RESULTS_DIR / name
    p.write_text(json.dumps(payload, indent=2, sort_keys=True, default=_json))
    return p


def write_parquet(name: str, df: pd.DataFrame) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    p = RESULTS_DIR / name
    out = df.copy()
    for c in out.columns:
        if out[c].dtype == object:
            out[c] = out[c].map(
                lambda v: json.dumps(v, default=_json) if isinstance(v, (list, dict)) else v
            )
    out.to_parquet(p, index=False)
    return p


def _frame_to_parquet(path: Path, rows: list | None) -> None:
    """Write a list-of-dicts table; empty list removes any prior file."""
    if path.exists():
        path.unlink()
    if not rows:
        return
    frame = pd.DataFrame(rows)
    for column in frame.columns:
        if frame[column].dtype == object:
            frame[column] = frame[column].map(
                lambda value: (
                    json.dumps(value, default=_json)
                    if isinstance(value, (list, dict))
                    else value
                )
            )
    frame.to_parquet(path, index=False)


def shard_meta_path(shard_dir: Path, symbol: str) -> Path:
    return shard_dir / f"meta_{symbol}.json"


def shard_is_complete(shard_dir: Path, symbol: str) -> bool:
    return shard_meta_path(shard_dir, symbol).is_file()


def list_complete_shard_symbols(shard_dir: Path) -> set[str]:
    if not shard_dir.exists():
        return set()
    return {
        path.name[len("meta_"):-len(".json")]
        for path in shard_dir.glob("meta_*.json")
    }


def write_symbol_shard(shard_dir: Path, result: dict) -> None:
    """Persist one symbol as soon as it finishes (resume-safe).

    Completion marker is ``meta_<symbol>.json``, written last so a kill mid-write
    leaves the symbol incomplete and re-runnable.
    """
    symbol = str(result.get("symbol") or "")
    if not symbol:
        raise ValueError("symbol shard requires a symbol")
    shard_dir.mkdir(parents=True, exist_ok=True)
    _frame_to_parquet(shard_dir / f"ep_{symbol}.parquet", result.get("episodes") or [])
    _frame_to_parquet(shard_dir / f"zn_{symbol}.parquet", result.get("zones") or [])
    _frame_to_parquet(shard_dir / f"ev_{symbol}.parquet", result.get("events") or [])
    _frame_to_parquet(shard_dir / f"cv_{symbol}.parquet", result.get("cell_cov") or [])
    meta = {
        "symbol": symbol,
        "empty": bool(result.get("empty")),
        "error": result.get("error"),
        "traceback": result.get("traceback"),
        "unit": result.get("unit"),
        "tripwire": result.get("tripwire") or {},
        "g8_evidence": result.get("g8_evidence"),
        "parity_posts": result.get("parity_posts") or [],
        "gate_info": result.get("gate_info") or {},
        "n_episodes": len(result.get("episodes") or []),
        "n_zones": len(result.get("zones") or []),
        "n_events": len(result.get("events") or []),
        "n_cell_cov": len(result.get("cell_cov") or []),
    }
    tmp = shard_dir / f"meta_{symbol}.json.tmp"
    final = shard_meta_path(shard_dir, symbol)
    tmp.write_text(json.dumps(meta, indent=2, sort_keys=True, default=_json))
    tmp.replace(final)


def load_symbol_shard(shard_dir: Path, symbol: str) -> dict:
    """Reconstruct a process-symbol result from an on-disk shard.

    Prefer :func:`assemble_tables_from_shards` for full-universe wrap-up — this
    path materialises list-of-dicts and is only safe for small probes/tests.
    """
    meta_path = shard_meta_path(shard_dir, symbol)
    if not meta_path.is_file():
        raise FileNotFoundError(f"missing shard meta for {symbol}")
    meta = json.loads(meta_path.read_text())

    def _rows(name: str) -> list[dict]:
        path = shard_dir / f"{name}_{symbol}.parquet"
        if not path.is_file():
            return []
        return pd.read_parquet(path).to_dict(orient="records")

    return {
        "symbol": symbol,
        "empty": bool(meta.get("empty")),
        "error": meta.get("error"),
        "traceback": meta.get("traceback"),
        "episodes": _rows("ep"),
        "zones": _rows("zn"),
        "events": _rows("ev"),
        "cell_cov": _rows("cv"),
        "parity_posts": meta.get("parity_posts") or [],
        "unit": meta.get("unit"),
        "tripwire": meta.get("tripwire") or {},
        "g8_evidence": meta.get("g8_evidence"),
        "gate_info": meta.get("gate_info") or {},
    }


def assemble_tables_from_shards(
    shard_dir: Path,
    symbols: list[str],
) -> dict:
    """Concat shard parquets as DataFrames — never expand 10M+ rows to dicts.

    Loading every episode as a Python dict OOMs on the full universe (~30M rows).
    Parquet concat keeps peak memory near the on-disk table footprint.
    """
    print(f"  assembling tables from {len(symbols)} shards…", flush=True)

    def concat_kind(prefix: str) -> pd.DataFrame:
        frames: list[pd.DataFrame] = []
        for index, symbol in enumerate(symbols, 1):
            path = shard_dir / f"{prefix}_{symbol}.parquet"
            if path.is_file():
                frames.append(pd.read_parquet(path))
            if index % 5 == 0 or index == len(symbols):
                rows = sum(len(frame) for frame in frames)
                print(
                    f"    {prefix}: {index}/{len(symbols)} files, {rows} rows",
                    flush=True,
                )
        if not frames:
            return pd.DataFrame()
        out = pd.concat(frames, ignore_index=True)
        del frames
        return out

    episodes = concat_kind("ep")
    zones = concat_kind("zn")
    events = concat_kind("ev")
    cell_cov = concat_kind("cv")

    units: list[dict] = []
    tw_mats: list[dict] = []
    g8_evidence_rows: list = []
    parity_map: dict[str, list] = {}
    for symbol in symbols:
        meta_path = shard_meta_path(shard_dir, symbol)
        if not meta_path.is_file():
            continue
        meta = json.loads(meta_path.read_text())
        if meta.get("error"):
            print(
                f"  ERROR {symbol}: {meta.get('error')}\n"
                f"{str(meta.get('traceback') or '')[:500]}",
                flush=True,
            )
        if meta.get("unit"):
            units.append(meta["unit"])
        if meta.get("tripwire"):
            tw_mats.append(meta["tripwire"])
        if meta.get("g8_evidence"):
            g8_evidence_rows.append(meta["g8_evidence"])
        parity_map[symbol] = meta.get("parity_posts") or []

    print(
        f"  episodes={len(episodes)}  zones={len(zones)}  events={len(events)}  "
        f"cell_cov={len(cell_cov)}",
        flush=True,
    )
    return {
        "episodes": episodes,
        "zones": zones,
        "events": events,
        "cell_cov": cell_cov,
        "units": units,
        "tw_mats": tw_mats,
        "g8_evidence_rows": g8_evidence_rows,
        "parity_map": parity_map,
    }


def universe() -> list[str]:
    pin = json.loads(Path(UNIVERSE_PIN_FAMILY).read_text())
    return list(pin["symbols"])


def verify_predeclaration() -> None:
    def sha(p: Path) -> str:
        h = hashlib.sha256()
        h.update(p.read_bytes())
        return h.hexdigest()

    b = RESULTS_DIR / "resolution_basis.json"
    e = RESULTS_DIR / "expected_resolution.json"
    assert b.exists() and e.exists(), "predeclaration artifacts missing"
    bs, es = sha(b), sha(e)
    assert bs == RESOLUTION_BASIS_SHA256, f"resolution_basis.json hash mismatch: {bs}"
    assert es == EXPECTED_RESOLUTION_SHA256, f"expected_resolution.json hash mismatch: {es}"
    print(f"  predeclaration OK  basis={bs[:16]}…  expected={es[:16]}…", flush=True)


def _process_symbol(task: dict) -> dict:
    symbol = task["symbol"]
    try:
        s_pin = task.get("s_pin") or prepare.load_s_symbol_pin()
        bundle = prepare.load_symbol_bundle(symbol, s_pin=s_pin)
        if bundle is None:
            return {
                "symbol": symbol, "empty": True,
                "episodes": [], "zones": [], "events": [],
                "parity_posts": [], "cell_cov": [],
            }

        clocks = task.get("clocks", list(CLOCKS_RUN))
        sources = task.get("sources", list(SOURCES))
        z_values = task.get("z_values", list(Z_VALUES))
        H_values = task.get("H_values", list(H_VALUES))
        h_values = task.get("h_values", list(H_POST))
        event_types = task.get("event_types", list(EVENT_TYPES))
        variants = task.get("variants", list(VARIANT_IDS))

        episodes, zones, events, parity_posts, cell_cov = [], [], [], [], []
        for clock in clocks:
            if clock not in bundle["packs"]:
                continue
            pack = bundle["packs"][clock]
            z, e, ep, pp, cov = layers.run_grid_for_pack(
                pack,
                sources=tuple(sources),
                z_values=tuple(z_values),
                H_values=tuple(H_values),
                h_values=tuple(h_values),
                event_types=tuple(event_types),
                variants=tuple(variants),
            )
            zones.extend(z)
            events.extend(e)
            episodes.extend(ep)
            if clock == "H1":
                parity_posts.extend(pp)
            cell_cov.extend(cov)

        # tripwire material from H1
        tw = {}
        g8_evidence = None
        if "H1" in bundle["packs"]:
            pan = bundle["packs"]["H1"]
            g8_evidence = golden.find_g8_evidence(pan)
            if symbol == "ETHUSDT":
                tw["tripwire_1"] = _tripwire_one_for_pack(pan)
                tw["tripwire_2"] = _tripwire_two_for_pack(pan)

        return {
            "symbol": symbol,
            "empty": False,
            "episodes": episodes,
            "zones": zones,
            "events": events,
            "parity_posts": parity_posts,
            "cell_cov": cell_cov,
            "unit": {
                "symbol": symbol,
                "s_symbol": bundle["s_symbol"],
                "s_hat_uncond": bundle["s_hat_uncond"],
                "n_h1": int(bundle["packs"]["H1"].close.size) if "H1" in bundle["packs"] else 0,
            },
            "tripwire": tw,
            "g8_evidence": g8_evidence,
            "gate_info": bundle.get("gate_info", {}),
        }
    except Exception as e:
        return {
            "symbol": symbol, "empty": True, "error": repr(e),
            "traceback": traceback.format_exc(),
            "episodes": [], "zones": [], "events": [],
            "parity_posts": [], "cell_cov": [],
        }


def run_tasks(
    tasks: list[dict],
    jobs: int,
    *,
    label: str,
    shard_dir: Path | None = None,
    already_done: int = 0,
    total_symbols: int | None = None,
) -> list[dict]:
    """Run symbol tasks; optionally write a complete shard as each finishes."""
    t0 = time.time()
    planned = total_symbols if total_symbols is not None else (already_done + len(tasks))

    def _record(res: dict, finished_in_batch: int) -> None:
        if shard_dir is not None:
            write_symbol_shard(shard_dir, res)
        print(
            f"  [{label}] {already_done + finished_in_batch}/{planned} "
            f"{res.get('symbol', '?')} ({time.time() - t0:.0f}s)",
            flush=True,
        )

    if not tasks:
        return []
    if jobs <= 1:
        out = []
        for i, task in enumerate(tasks, 1):
            res = _process_symbol(task)
            out.append(res)
            _record(res, i)
        return out
    ctx = mp.get_context("spawn")
    with ctx.Pool(jobs) as pool:
        out = []
        for i, res in enumerate(pool.imap_unordered(_process_symbol, tasks), 1):
            out.append(res)
            _record(res, i)
    return sorted(out, key=lambda r: r.get("symbol", ""))


def _score_one_cell(args: tuple) -> dict | None:
    (keys, r, ts, exit_ts, hold_h, symbols, n_boot, clock) = args
    if r.size == 0:
        return None
    band_name = keys["band"]
    band_start, band_end = BANDS[band_name]
    m = metrics.cell_metrics(
        r,
        ts,
        n_boot=n_boot,
        cost_bps=COST_FLOOR_BPS,
        clock=clock,
        calendar_start_ns=int(band_start.timestamp() * 1_000_000_000),
        calendar_end_ns=int(band_end.timestamp() * 1_000_000_000),
    )
    sp = metrics.span_stats(ts, exit_ts, float(hold_h) if np.isfinite(hold_h) else 1.0)
    m.update(sp)
    cov = metrics.effective_coverage(ts, symbols)
    m["effective_frac_of_nominal"] = cov.get("effective_frac_of_nominal")
    m["n_symbols_in_cell"] = cov.get("n_symbols")
    m.update(keys)
    m["n_episodes"] = int(r.size)
    m["spread_cost_status"] = SPREAD_COST_DISCLOSURE["spread_cost_status"]
    m["sizing_no_logR_claim"] = keys.get("variant_id") in SIZING_VARIANTS
    m["evidence_class"] = (
        "[S]" if keys.get("scope") == "POOLED" and keys.get("band") == "TRAIN" else "[D]"
    )
    return m


def _score_cells(
    episodes: pd.DataFrame,
    n_boot: int,
    *,
    jobs: int = 1,
    n_boot_disclosure: int | None = None,
) -> list[dict]:
    """Score cells. Full bootstrap on POOLED TRAIN; lighter on disclosure scopes/bands.

    Same block rule everywhere — only the resample count drops for disclosure (still
    the min/max envelope construction; descriptive, not a different estimand).
    """
    if episodes.empty:
        return []
    if "suppressed" in episodes.columns:
        episodes = episodes[~episodes["suppressed"].fillna(False).astype(bool)]
    n_boot_disc = n_boot_disclosure if n_boot_disclosure is not None else max(50, n_boot // 10)
    symbols = sorted(episodes["symbol"].unique().tolist())
    group_cols = [
        c for c in (
            "variant_id", "clock", "source", "z", "H", "event_type", "h", "policy",
        ) if c in episodes.columns
    ]
    tasks = []
    for keys, g in episodes.groupby(group_cols, sort=True, observed=True):
        if not isinstance(keys, tuple):
            keys = (keys,)
        key_d = dict(zip(group_cols, keys))
        if key_d.get("variant_id") in DERIVED_VARIANTS:
            continue
        for band, sub in (
            ("TRAIN", g),
            ("DESIGN", g[g["band"] == "DESIGN"] if "band" in g.columns else g.iloc[0:0]),
            ("CONFIRM", g[g["band"] == "CONFIRM"] if "band" in g.columns else g.iloc[0:0]),
        ):
            if sub.empty:
                continue
            # POOLED always; per-symbol only for L0 on primary axes (heterogeneity disclosure)
            scopes = ["POOLED"]
            is_primary_l0 = (
                key_d.get("variant_id") == "L0_BASELINE"
                and key_d.get("clock") == "H1"
                and key_d.get("source") == "Z-VOL"
                and key_d.get("H") == 12
            )
            if is_primary_l0 and band == "TRAIN":
                scopes = ["POOLED"] + symbols
            for scope in scopes:
                cell = sub if scope == "POOLED" else sub[sub["symbol"] == scope]
                if cell.empty:
                    continue
                population_cols = [
                    c for c in (
                        "symbol", "band", "n_origins", "n_events", "n_undecided"
                    ) if c in cell.columns
                ]
                if {
                    "symbol", "band", "n_origins", "n_events", "n_undecided"
                }.issubset(population_cols):
                    sufficient = cell[population_cols].drop_duplicates(
                        ["symbol", "band"]
                    )
                    n_origins = int(sufficient["n_origins"].sum())
                    n_events = int(sufficient["n_events"].sum())
                    n_und = int(sufficient["n_undecided"].sum())
                    pev = n_events / n_origins if n_origins else float("nan")
                else:
                    n_origins = n_events = 0
                    n_und = 0
                    pev = float("nan")
                h_hours = 1.0
                if "h" in key_d and "clock" in key_d:
                    mins = 60 if key_d["clock"] == "H1" else 240
                    h_hours = float(key_d["h"]) * mins / 60.0
                nb = n_boot if (scope == "POOLED" and band == "TRAIN") else n_boot_disc
                kd = {
                    **key_d, "scope": scope, "band": band,
                    "p_event": pev, "n_undecided": n_und,
                    "n_origins": n_origins, "n_events": n_events,
                }
                tasks.append((
                    kd,
                    cell["r_bps"].to_numpy(dtype=float),
                    cell["entry_ts"].to_numpy(dtype=np.int64),
                    cell["exit_ts"].to_numpy(dtype=np.int64),
                    h_hours,
                    cell["symbol"].to_numpy(),
                    nb,
                    key_d.get("clock", "H1"),
                ))
    print(f"  scoring {len(tasks)} cells (jobs={jobs}, n_boot_primary={n_boot})…", flush=True)
    if jobs <= 1:
        rows = []
        for i, t in enumerate(tasks, 1):
            m = _score_one_cell(t)
            if m is not None:
                rows.append(m)
            if i % 500 == 0:
                print(f"    {i}/{len(tasks)}", flush=True)
        return rows
    ctx = mp.get_context("spawn")
    with ctx.Pool(jobs) as pool:
        rows = [m for m in pool.imap_unordered(_score_one_cell, tasks, chunksize=16) if m]
    return rows


def _episode_arm(episodes: pd.DataFrame, row: dict, variant_id: str) -> pd.DataFrame:
    arm = episodes[episodes["variant_id"] == variant_id]
    for column in ("clock", "source", "z", "H", "event_type", "h", "policy"):
        if column in arm.columns and row.get(column) is not None:
            value = row[column]
            if isinstance(value, float):
                arm = arm[np.isclose(arm[column].astype(float), value)]
            else:
                arm = arm[arm[column] == value]
    if row.get("band") in ("DESIGN", "CONFIRM"):
        arm = arm[arm["band"] == row["band"]]
    if row.get("scope") not in (None, "POOLED"):
        arm = arm[arm["symbol"] == row["scope"]]
    return arm


def _add_interaction_rows(
    metrics_rows: list[dict],
    episodes: pd.DataFrame,
    *,
    n_boot: int,
) -> list[dict]:
    extra = []
    by = {}
    for r in metrics_rows:
        key = (
            r.get("clock"), r.get("source"), r.get("z"), r.get("H"),
            r.get("event_type"), r.get("h"), r.get("policy"),
            r.get("scope"), r.get("band"), r.get("variant_id"),
        )
        by[key] = r
    base_keys = set()
    for r in metrics_rows:
        base_keys.add((
            r.get("clock"), r.get("source"), r.get("z"), r.get("H"),
            r.get("event_type"), r.get("h"), r.get("policy"),
            r.get("scope"), r.get("band"),
        ))
    for bk in base_keys:
        def get(vid):
            return by.get((*bk, vid))
        l0 = get("L0_BASELINE")
        shock = get("L2_SHOCK_HMM")
        k12 = get("L2_LEVEL_RMARKOV_K12")
        joint = get("L2_JOINT_HMM_HIGH_AND_K12_HIGH")
        if not all(x is not None for x in (l0, shock, k12, joint)):
            continue
        template = joint
        arms = [
            _episode_arm(episodes, template, vid)
            for vid in (
                "L2_JOINT_HMM_HIGH_AND_K12_HIGH",
                "L2_SHOCK_HMM",
                "L2_LEVEL_RMARKOV_K12",
                "L0_BASELINE",
            )
        ]
        if any(arm.empty for arm in arms):
            continue
        inter = metrics.paired_interaction_metrics(
            *(arm["r_bps"].to_numpy(dtype=float) for arm in arms),
            tuple(arm["entry_ts"].to_numpy(dtype=np.int64) for arm in arms),
            n_boot=n_boot,
            clock=str(bk[0]),
            calendar_start_ns=int(BANDS[str(bk[8])][0].timestamp() * 1_000_000_000),
            calendar_end_ns=int(BANDS[str(bk[8])][1].timestamp() * 1_000_000_000),
        )
        interaction_row = {
            "variant_id": "L2_INTERACTION_HMM_X_K12",
            "clock": bk[0], "source": bk[1], "z": bk[2], "H": bk[3],
            "event_type": bk[4], "h": bk[5], "policy": bk[6],
            "scope": bk[7], "band": bk[8],
            "log_R": inter["delta_log_R"],
            "ci_low": inter["ci_low"],
            "ci_high": inter["ci_high"],
            "ci_width": inter["ci_width"],
            "block_mde": inter["block_mde"],
            "n": joint.get("n"),
            "p": float("nan"), "W": float("nan"), "L": float("nan"),
            "mde50": inter["block_mde"],
            "mde80": float("nan"), "mde95": float("nan"),
            "evidence_class": "[S]" if bk[7] == "POOLED" and bk[8] == "TRAIN" else "[D]",
            "note": "interaction Δjoint−Δshock−Δk12",
            "spread_cost_status": SPREAD_COST_DISCLOSURE["spread_cost_status"],
            "p_event": joint.get("p_event"),
            "paired": True,
            "n_boot_replicates": inter["n_boot_replicates"],
            "requested_replicates_per_seed": inter[
                "requested_replicates_per_seed"
            ],
            "ladder": inter["ladder"],
        }
        for rung, rate in inter["ladder"]["via_WL"].items():
            interaction_row[f"detect_wl_{rung}"] = rate
        for rung, rate in inter["ladder"]["via_p"].items():
            interaction_row[f"detect_p_{rung}"] = rate
        extra.append(interaction_row)
    return metrics_rows + extra


def _layer_deltas(
    metrics_rows: list[dict],
    episodes: pd.DataFrame,
    *,
    n_boot: int,
) -> list[dict]:
    out = []
    by = {}
    for r in metrics_rows:
        if r.get("band") != "TRAIN":
            continue
        key = (
            r.get("clock"), r.get("source"), r.get("z"), r.get("H"),
            r.get("event_type"), r.get("h"), r.get("policy"),
            r.get("scope"), r.get("variant_id"),
        )
        by[key] = r
    for r in metrics_rows:
        if r.get("band") != "TRAIN" or r.get("variant_id") == "L0_BASELINE":
            continue
        l0 = by.get((
            r.get("clock"), r.get("source"), r.get("z"), r.get("H"),
            r.get("event_type"), r.get("h"), r.get("policy"),
            r.get("scope"), "L0_BASELINE",
        ))
        if l0 is None:
            continue
        layer_arm = _episode_arm(episodes, r, str(r.get("variant_id")))
        l0_arm = _episode_arm(episodes, l0, "L0_BASELINE")
        if layer_arm.empty or l0_arm.empty:
            continue
        d = metrics.paired_delta_metrics(
            layer_arm["r_bps"].to_numpy(dtype=float),
            layer_arm["entry_ts"].to_numpy(dtype=np.int64),
            l0_arm["r_bps"].to_numpy(dtype=float),
            l0_arm["entry_ts"].to_numpy(dtype=np.int64),
            n_boot=n_boot,
            clock=str(r.get("clock")),
            calendar_start_ns=int(BANDS["TRAIN"][0].timestamp() * 1_000_000_000),
            calendar_end_ns=int(BANDS["TRAIN"][1].timestamp() * 1_000_000_000),
        )
        delta_row = {
            "variant_id": r.get("variant_id"),
            "clock": r.get("clock"), "source": r.get("source"),
            "z": r.get("z"), "H": r.get("H"),
            "event_type": r.get("event_type"), "h": r.get("h"),
            "policy": r.get("policy"), "scope": r.get("scope"),
            "band": "TRAIN",
            "log_R_layer": r.get("log_R"),
            "log_R_L0": l0.get("log_R"),
            "delta_log_R": d["delta_log_R"],
            "ci_low": d["ci_low"], "ci_high": d["ci_high"],
            "ci_width": d["ci_width"], "block_mde": d["block_mde"],
            "p_event": r.get("p_event"),
            "paired": True,
            "n_boot_replicates": d["n_boot_replicates"],
            "requested_replicates_per_seed": d[
                "requested_replicates_per_seed"
            ],
            "ladder": d["ladder"],
        }
        for rung, rate in d["ladder"]["via_WL"].items():
            delta_row[f"detect_wl_{rung}"] = rate
        for rung, rate in d["ladder"]["via_p"].items():
            delta_row[f"detect_p_{rung}"] = rate
        out.append(delta_row)
    return out


def _join_predeclaration(metrics_df: pd.DataFrame) -> pd.DataFrame:
    exp = json.loads((RESULTS_DIR / "expected_resolution.json").read_text())
    strata = exp.get("strata", [])
    lookup = {}
    for s in strata:
        key = (
            s.get("source"), s.get("clock"), s.get("H"), s.get("h"),
            s.get("z"), s.get("event_type"), s.get("policy"),
        )
        lookup[key] = s
    exp_n, exp_mde, prior, d_n, d_mde = [], [], [], [], []
    for _, row in metrics_df.iterrows():
        key = (
            row.get("source"), row.get("clock"), row.get("H"), row.get("h"),
            row.get("z"), row.get("event_type"), row.get("policy"),
        )
        s = lookup.get(key, {})
        en = s.get("expected_n")
        em = s.get("expected_mde50")
        exp_n.append(en)
        exp_mde.append(em)
        prior.append(s.get("prior_status"))
        rn = row.get("n")
        rm = row.get("mde50")
        d_n.append((rn - en) if en is not None and rn is not None and np.isfinite(rn) else None)
        d_mde.append(
            (rm - em) if em is not None and rm is not None and np.isfinite(rm) else None
        )
    metrics_df = metrics_df.copy()
    metrics_df["expected_n"] = exp_n
    metrics_df["expected_mde50"] = exp_mde
    metrics_df["prior_status"] = prior
    metrics_df["delta_n_realised_minus_expected"] = d_n
    metrics_df["delta_mde50_realised_minus_expected"] = d_mde
    return metrics_df


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="SPDR-020 phase-(a) screen")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--n-boot", type=int, default=None)
    ap.add_argument("--symbols", type=str, default=None)
    ap.add_argument(
        "--primary-only",
        action="store_true",
        help="Z-VOL × H1 × H=12 only (1,584-cell no-L5 phase-(a) shape)",
    )
    args = ap.parse_args(argv)

    t_start = time.time()
    print("SPDR-020 phase (a) — SPDR-014 object + L4 capture, TRAIN only", flush=True)
    print(f"  fills module: {fills_bridge.FILLS_SOURCE_PATH}", flush=True)
    verify_predeclaration()

    # bit-identity assertion on bootstrap path
    rng = np.random.default_rng(0)
    demo_r = rng.normal(0, 50, size=500)
    demo_ts = np.arange(500) * DAY_NS // 24 + int(1.6e18)
    day_idx, _ = metrics.day_index(demo_ts)
    suff = metrics.day_sufficient(demo_r, day_idx, int(day_idx.max()) + 1)
    equiv = metrics.assert_canonical_equivalence(suff, n_boot=200)
    assert equiv["equivalent"], f"bootstrap bit-identity failed: {equiv}"
    print("  bootstrap vectorised ≡ canonical  |Δ|≤1e-9  OK", flush=True)

    syms = universe()
    if args.symbols:
        syms = [s.strip() for s in args.symbols.split(",")]
    if args.smoke:
        syms = [s for s in ("BTCUSDT", "ETHUSDT") if s in syms] or syms[:2]
    n_boot = args.n_boot or (50 if args.smoke else BOOT_RESAMPLES)

    # grid plan
    if args.smoke or args.primary_only:
        sources = (SOURCE_PRIMARY,)
        clocks = ("H1",)
        H_values = (H_PRIMARY,)
        z_values = Z_VALUES if not args.smoke else (1.5, 3.0)
        h_values = H_POST if not args.smoke else (12,)
        event_types = EVENT_TYPES if not args.smoke else ("E-TOUCH",)
    else:
        sources = SOURCES
        clocks = CLOCKS_RUN
        H_values = H_VALUES
        z_values = Z_VALUES
        h_values = H_POST
        event_types = EVENT_TYPES

    n_base = (
        len(sources) * len(clocks) * len(H_values) * len(z_values)
        * len(h_values) * len(event_types) * 2  # sides
    )
    print(
        f"  symbols={len(syms)}  jobs={args.jobs}  n_boot={n_boot}  "
        f"base_points≈{n_base}  variants={len(VARIANT_IDS)}",
        flush=True,
    )
    run_plan = {
        "symbols": list(syms), "jobs": args.jobs, "n_boot": n_boot,
        "sources": list(sources), "clocks": list(clocks),
        "H": list(H_values), "z": list(z_values), "h": list(h_values),
        "event_types": list(event_types),
        "variants": list(VARIANT_IDS),
        "smoke": args.smoke,
        "subset": bool(args.symbols),
        "primary_only": args.primary_only,
        "expected_primary_cells": 1584,
        "expected_full_cells": 28512,
        "fills_source": fills_bridge.FILLS_SOURCE_PATH,
        "note": (
            "phase-(a) exact no-L5 counts: primary 1584; full 28512; "
            "design maxima with four authorised L5 rows: 1872/33696"
        ),
    }
    execution_eligibility = selfcheck.execution_candidate_eligibility(run_plan)
    run_plan["execution_eligibility"] = execution_eligibility
    write_json("run_plan.json", run_plan)
    declared_manifest = (
        layers.expected_primary_cell_manifest()
        if args.primary_only or args.smoke
        else layers.expected_full_cell_manifest()
    )
    write_parquet("cell_manifest.parquet", pd.DataFrame(declared_manifest))

    s_pin = prepare.load_s_symbol_pin()
    tasks = [{
        "symbol": s, "s_pin": s_pin,
        "sources": list(sources), "clocks": list(clocks),
        "H_values": list(H_values), "z_values": list(z_values),
        "h_values": list(h_values), "event_types": list(event_types),
        "variants": list(VARIANT_IDS),
    } for s in syms]

    # resume: skip symbols with a complete per-symbol shard (meta_*.json)
    shard_dir = RESULTS_DIR / "shards"
    shard_dir.mkdir(parents=True, exist_ok=True)
    done_symbols = list_complete_shard_symbols(shard_dir) if args.resume else set()
    if args.resume:
        tasks = [t for t in tasks if t["symbol"] not in done_symbols]
        print(
            f"  resume: {len(done_symbols)} complete shards, "
            f"{len(tasks)} remaining",
            flush=True,
        )

    new_results = run_tasks(
        tasks,
        args.jobs,
        label="symbols",
        shard_dir=shard_dir,
        already_done=len(done_symbols),
        total_symbols=len(syms),
    )

    # Assemble ONLY from shard parquets (DataFrame concat). Never reload full
    # symbol results as list-of-dicts — that OOMs at ~30M episode rows.
    complete_now = list_complete_shard_symbols(shard_dir)
    assemble_symbols = [s for s in syms if s in complete_now]
    missing_symbols = [s for s in syms if s not in complete_now]
    if missing_symbols:
        print(
            f"  WARNING missing symbol shards: {missing_symbols}",
            flush=True,
        )

    # determinism when jobs>1 (only if this batch produced at least one symbol)
    determinism_ok = True
    if args.jobs > 1 and new_results and not args.smoke:
        print("  determinism: re-running 1 symbol sequential…", flush=True)
        probe_symbol = new_results[0]["symbol"]
        seq = _process_symbol({
            "symbol": probe_symbol,
            "s_pin": s_pin,
            "sources": list(sources),
            "clocks": list(clocks),
            "H_values": list(H_values),
            "z_values": list(z_values),
            "h_values": list(h_values),
            "event_types": list(event_types),
            "variants": list(VARIANT_IDS),
        })
        # Compare against the just-written shard parquet row count / sample hash.
        shard_eps = pd.read_parquet(shard_dir / f"ep_{probe_symbol}.parquet")
        par_n = int(len(shard_eps))
        seq_n = len(seq.get("episodes") or [])
        h1 = hashlib.sha256(
            json.dumps(seq.get("episodes", [])[:100], sort_keys=True, default=_json).encode()
        ).hexdigest()
        h2 = hashlib.sha256(
            shard_eps.head(100).to_json(orient="records").encode()
        ).hexdigest()
        determinism_ok = seq_n == par_n
        print(
            f"  determinism {'OK' if determinism_ok else 'FAIL'} "
            f"n={seq_n} vs {par_n} "
            f"hash {h1[:12]} vs {h2[:12]}",
            flush=True,
        )
        # Free probe payload before universe assemble.
        del seq, shard_eps
        new_results = []

    assembled = assemble_tables_from_shards(shard_dir, assemble_symbols)
    episodes = assembled["episodes"]
    zones_df = assembled["zones"]
    events_df = assembled["events"]
    cell_cov_df = assembled["cell_cov"]
    units = assembled["units"]
    tw_mats = assembled["tw_mats"]
    g8_evidence_rows = assembled["g8_evidence_rows"]
    parity_map = assembled["parity_map"]

    if not episodes.empty:
        print("  writing episodes.parquet…", flush=True)
        write_parquet("episodes.parquet", episodes)
    if not zones_df.empty:
        print("  writing zones.parquet…", flush=True)
        write_parquet("zones.parquet", zones_df)
    if not events_df.empty:
        print("  writing events.parquet…", flush=True)
        write_parquet("events.parquet", events_df)
    if not cell_cov_df.empty:
        print("  writing cell_coverage.parquet…", flush=True)
        write_parquet("cell_coverage.parquet", cell_cov_df)
    # zones only needed for write
    del zones_df

    # metrics
    print("  scoring cells…", flush=True)
    mrows = _score_cells(episodes, n_boot=n_boot, jobs=args.jobs)
    mrows = _add_interaction_rows(mrows, episodes, n_boot=n_boot)
    metrics_df = pd.DataFrame(mrows) if mrows else pd.DataFrame()
    if not metrics_df.empty:
        pooled = (
            metrics_df[metrics_df["scope"] == "POOLED"]
            if "scope" in metrics_df.columns
            else metrics_df
        )
        disclosures = (
            metrics_df[metrics_df["scope"] != "POOLED"]
            if "scope" in metrics_df.columns
            else pd.DataFrame()
        )
        pooled = layers.reconcile_metrics_to_manifest(pooled, declared_manifest)
        pooled["scope"] = "POOLED"
        metrics_df = pd.concat([pooled, disclosures], ignore_index=True, sort=False)
        metrics_df = _join_predeclaration(metrics_df)
        for col in ("per_block_ci", "per_seed_ci", "ladder", "blocks_days"):
            if col in metrics_df.columns:
                metrics_df[col] = metrics_df[col].map(
                    lambda v: json.dumps(v, default=_json) if not isinstance(v, str) else v
                )
        write_parquet("metrics_by_cell.parquet", metrics_df)
        pooled_count = int(
            (metrics_df["scope"] == "POOLED").sum()
            if "scope" in metrics_df.columns
            else len(metrics_df)
        )
        expected_pooled_count = len(declared_manifest) * 3
        if pooled_count != expected_pooled_count:
            execution_eligibility["eligible"] = False
            execution_eligibility["grade"] = "DEVELOPER_ONLY"
            execution_eligibility["reasons"].append("manifest_row_coverage")
        execution_eligibility["pooled_manifest_rows"] = pooled_count
        execution_eligibility["expected_pooled_manifest_rows"] = expected_pooled_count
        run_plan["execution_eligibility"] = execution_eligibility
        write_json("run_plan.json", run_plan)

    ld = _layer_deltas(mrows, episodes, n_boot=n_boot)
    if ld:
        write_parquet("layer_deltas.parquet", pd.DataFrame(ld))

    if not metrics_df.empty:
        ladder_cols = [
            c for c in metrics_df.columns
            if c in (
                "variant_id", "clock", "source", "z", "H", "event_type", "h", "policy",
                "scope", "band", "n", "n_dates", "log_R", "ci_low", "ci_high", "ci_width",
                "block_mde", "mde50", "mde80", "mde95", "realised_c", "effective_n",
                "expected_n", "expected_mde50", "prior_status",
                "delta_n_realised_minus_expected", "delta_mde50_realised_minus_expected",
                "p_event",
            ) or c.startswith("detect_")
        ]
        write_parquet("resolution_ladder.parquet", metrics_df[ladder_cols])

    # unit pin
    covered = [
        u
        for u in units
        if u.get("symbol") not in ZVOL_NAN_SYMBOLS
        and np.isfinite(u.get("s_symbol", np.nan))
    ]
    observed_missing = [
        u["symbol"]
        for u in units
        if not np.isfinite(u.get("s_symbol", np.nan))
    ]
    unit_pin = {
        "divisor_object": "s_symbol * EWMA_park (SPDR-014 Z-VOL identical)",
        "s_symbol_source": str(prepare.ZVOL_SCALE_PATH),
        "per_symbol": units,
        "pooled_s_hat_median": float(np.nanmedian([u["s_hat_uncond"] for u in covered])) if covered else None,
        "zvol_covered_n": len(covered),
        "zvol_covered_n_expected": ZVOL_COVERED_N,
        "zvol_covered_symbols": sorted(u["symbol"] for u in covered),
        "zvol_nan_symbols": sorted(observed_missing),
        "zvol_nan_symbols_expected": sorted(ZVOL_NAN_SYMBOLS),
        "cost_floor_bps_DISCLOSURE_ONLY": COST_FLOOR_BPS,
        "spread_cost_disclosure": SPREAD_COST_DISCLOSURE,
        "n_h1_bars_pooled": int(sum(u.get("n_h1", 0) for u in units)),
    }
    write_json("unit_pin.json", unit_pin)

    # parent parity
    print("  parent parity…", flush=True)
    parity = parent_parity.build_parity_report(parity_map)
    write_json("parent_parity.json", parity)
    print(
        f"  parity hard_pass={parity['hard_pass']} "
        f"n={parity['n_reproduced']}/{parity['n_compared']} "
        f"max|Δ|={parity['max_abs_diff']}",
        flush=True,
    )

    # controls
    print("  controls…", flush=True)
    control_bundle_cache: dict[str, dict] = {}
    ambient_candidates = _ambient_control_candidates(
        episodes,
        events_df,
        s_pin=s_pin,
        bundle_cache=control_bundle_cache,
    )
    magnitude_candidates = _magnitude_control_candidates(episodes)
    control_seeds = TIMING_SEEDS[:10] if args.smoke else TIMING_SEEDS
    l4_variants = tuple(
        vid for vid in run_plan.get("variants", VARIANT_IDS)
        if str(vid).startswith("L4_")
    )
    required_control_cells = controls_mod.expand_required_control_cells(
        episodes,
        l4_variants=l4_variants,
    )
    ctrl = controls_mod.run_primary_controls(
        episodes,
        n_boot=n_boot,
        rerun=lambda frame, exit_rule: _rerun_control_rows(
            frame,
            exit_rule,
            s_pin=s_pin,
            bundle_cache=control_bundle_cache,
        ),
        ambient_candidates=ambient_candidates,
        magnitude_candidates=magnitude_candidates,
        seeds=control_seeds,
        required_cells=required_control_cells,
        l4_variants=l4_variants,
    )
    write_json("controls.json", ctrl)

    # selection L-51
    sel = selection.run_selection_checks(episodes, metrics_df)
    write_json("selection_check.json", sel)

    # integrity extras / tripwires
    tw1 = {"hard_pass": False}
    tw2 = {"hard_pass": False}
    if tw_mats:
        tw1 = next(
            (
                item["tripwire_1"]
                for item in tw_mats
                if item.get("tripwire_1", {}).get("symbol") == "ETHUSDT"
            ),
            tw1,
        )
        tw2 = next(
            (
                item["tripwire_2"]
                for item in tw_mats
                if item.get("tripwire_2", {}).get("hard_pass")
            ),
            tw_mats[0].get("tripwire_2", tw2),
        )

    # fill causality sample
    fill_ok = False
    fill_detail = {"n_checked": 0, "n_fail": 0}
    if not episodes.empty and "fill_m1_idx" in episodes.columns:
        l4_all = episodes[
            episodes["variant_id"].astype(str).str.startswith("L4_")
        ]
        ineligible = l4_all.get(
            "ineligible_missing_source",
            pd.Series(False, index=l4_all.index),
        ).fillna(False).astype(bool)
        active_l4 = l4_all[
            ~ineligible & ~l4_all["suppressed"].fillna(False).astype(bool)
        ]
        required_provenance = {
            "cell_source",
            "forecast_origin_t0",
            "forecast_value_bps",
            "forecast_median_bps",
            "boundary_source",
        }
        provenance_ok = bool(
            not active_l4.empty
            and required_provenance.issubset(active_l4.columns)
            and active_l4[list(required_provenance)].notna().all(axis=1).all()
        )
        boundary_expected = (
            active_l4.apply(
                lambda row: layers.l4_boundary_source(
                    layers._parse_l4(row["variant_id"])["device"],
                    row["source"],
                ),
                axis=1,
            )
            if not active_l4.empty
            else pd.Series(dtype=str)
        )
        boundary_ok = bool(
            not active_l4.empty
            and (
                active_l4["boundary_source"].astype(str)
                == boundary_expected.astype(str)
            ).all()
        )
        l4 = active_l4[
            active_l4["variant_id"].astype(str).str.startswith("L4_TARGET")
            | active_l4["variant_id"].astype(str).str.startswith("L4_TRAIL")
        ]
        if len(l4):
            # exit_ts > entry_ts
            bad = l4["exit_ts"].to_numpy() <= l4["entry_ts"].to_numpy()
            fill_detail = {
                "n_checked": int(len(l4)),
                "n_fail": int(bad.sum()),
                "source_provenance_ok": provenance_ok,
                "boundary_source_ok": boundary_ok,
                "n_ineligible_missing_source": int(ineligible.sum()),
            }
            fill_ok = int(bad.sum()) == 0 and provenance_ok and boundary_ok

    # G8 both-reachable
    both_sample = g8_evidence_rows[0] if g8_evidence_rows else None

    integrity_extra = {
        "tripwire_1": tw1,
        "tripwire_2": tw2,
        "causality_ok": bool(tw1.get("hard_pass")),
        "causality_detail": {"rule": "width<=t; anchor open[t+1]; entry open[j+1]; L0 exit open[entry+h]"},
        "breach_ok": bool(tw2.get("hard_pass")),
        "fill_causality_ok": fill_ok,
        "fill_causality_detail": fill_detail,
        "p_event_never_filters": (
            "p_event" not in layers._select_at_breach.__code__.co_names
        ),
        "predeclared_joined": bool(
            not metrics_df.empty
            and {"expected_n", "expected_mde50"}.issubset(metrics_df.columns)
        ),
        "fills_source": fills_bridge.FILLS_SOURCE_PATH,
        "block_rule": {
            "ok": bool(
                tuple(metrics.block_days_for_clock("H1")) == tuple(BOOT_BLOCKS_DAYS_H1)
                and tuple(metrics.block_days_for_clock("H4")) == tuple(BOOT_BLOCKS_DAYS_H4)
            ),
            "H1_blocks_days": list(BOOT_BLOCKS_DAYS_H1),
            "H4_blocks_days": list(BOOT_BLOCKS_DAYS_H4),
            "H1_rule": "SPDR-018 §6.2 verbatim",
            "H4_rule": "{4,12,28}-day co-report; no H1 c prior",
            "forbidden_form_absent": "max(h hours, 20 hours)",
        },
        "undecided_counts": {
            "present": "n_undecided" in (episodes.columns if not episodes.empty else []),
        },
        "both_reachable_sample": both_sample,
        "g8_detail": {},
        "bootstrap_equivalence": equiv,
        "execution_eligibility": execution_eligibility,
    }

    repo_root = Path(__file__).resolve().parents[4]
    tracked = set(
        subprocess.run(
            ["git", "ls-files"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
    )
    status_lines = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    dirty_paths = {
        line[3:].split(" -> ")[-1]
        for line in status_lines
        if len(line) > 3
    }
    dependency_paths = sorted(Path(__file__).resolve().parent.glob("*.py"))
    dependency_paths.append(Path(fills_bridge.FILLS_SOURCE_PATH))
    dependency_paths.extend(sorted(prepare.PARENT_015_CODE.glob("*.py")))
    dependency_paths.extend([
        Path(__file__).resolve().parents[3] / "src" / "xen" / "evaluation.py",
        Path(__file__).resolve().parents[3] / "src" / "xen" / "adjudication.py",
        Path(__file__).resolve().parents[3]
        / "src"
        / "xen"
        / "xena"
        / "controls.py",
        Path(__file__).resolve().parents[3]
        / "src"
        / "xen"
        / "nautilus"
        / "catalog_fence.py",
    ])
    dependency_paths = provenance.expand_local_import_closure(
        dependency_paths,
        repo_root=repo_root,
    )
    dependency_manifest = provenance.build_dependency_manifest(
        dependency_paths,
        repo_root=repo_root,
        tracked_paths=tracked,
        dirty_paths=dirty_paths,
    )
    integrity_extra["dependency_manifest"] = dependency_manifest
    integrity_extra["controls"] = ctrl

    eth_posts = parity_map.get("ETHUSDT", [])
    gold = golden.run_golden(
        episodes=episodes,
        events=events_df,
        cell_coverage=cell_cov_df,
        parity_posts_eth=eth_posts,
        metrics_df=metrics_df,
        integrity_extra=integrity_extra,
    )
    write_json("golden_traces.json", gold)

    print("  self-check…", flush=True)
    sc = selfcheck.run_selfcheck(
        metrics_df=metrics_df,
        episodes_df=episodes,
        integrity_extra=integrity_extra,
        controls=ctrl,
        selection=sel,
        golden=gold,
        parent_parity=parity,
        unit_pin=unit_pin,
        determinism_ok=determinism_ok,
        jobs=args.jobs,
    )
    write_json("integrity_selfcheck.json", sc)
    failed = sc.get("failed", [])
    print(
        f"  integrity hard_pass={sc['hard_pass']}  "
        f"failed={failed if failed else 'none'}",
        flush=True,
    )

    write_json("run_summary.json", {
        "elapsed_s": time.time() - t_start,
        "n_symbols": len(syms),
        "n_episodes": len(episodes),
        "n_metric_cells": len(metrics_df),
        "parent_parity_pass": parity.get("hard_pass"),
        "integrity_pass": sc.get("hard_pass"),
        "jobs": args.jobs,
        "n_boot": n_boot,
        "smoke": args.smoke,
        "grade": execution_eligibility["grade"],
        "execution_candidate_eligible": execution_eligibility["eligible"],
        "dependency_provenance_complete": dependency_manifest["complete"],
        "fills_source": fills_bridge.FILLS_SOURCE_PATH,
    })
    print(f"SPDR-020 done in {time.time()-t_start:.0f}s", flush=True)
    return 0 if sc.get("hard_pass") and parity.get("hard_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
