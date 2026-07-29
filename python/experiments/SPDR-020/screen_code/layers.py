"""Layer protocol L0–L4 on the SPDR-014 event object (design §4). Phase (a): no L5.

L0: parent fixed exit open[entry+h], both MOMO and MR trade sides.
L1: three central L4 pairs (no extra rows).
L2/L3: selection on L0 episodes at the breach bar.
L4: path-dependent exits via SPDR-019 M1 fills (imported).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from config import (
    DESIGN_END_NS,
    DESIGN_START_NS,
    E_RUN_CLIP,
    H_MOD_CLIP_BARS,
    H_MOD_DIVISOR,
    H_POST as _H_POST_DEFAULT,
    MOD_HOLD_MIN_PRIOR_TRANS,
    SIZE_CLIP,
    TRAIN_END_NS,
)
from event_engine import posts_from_events, walk_zones
from fills_bridge import (
    EXIT_TIME,
    bps_to_price_width,
    first_m1_at_or_after,
    resolve_target_trail_time,
    signed_r_bps,
)
from prepare import SeriesPack


def cell_manifest_key(row: dict) -> tuple:
    return (
        row["variant_id"],
        row["source"],
        row["clock"],
        row["z"],
        row["H"],
        row["event_type"],
        row["policy"],
        row.get("base_h"),
        row.get("hold_bars"),
    )


def expected_primary_cell_manifest() -> list[dict]:
    """Exact no-L5 phase-(a) primary manifest (1,584 unique cells)."""
    rows: list[dict] = []
    non_l4 = (
        "L0_BASELINE",
        "L2_SHOCK_HMM",
        "L2_LEVEL_RMARKOV_K4",
        "L2_LEVEL_RMARKOV_K12",
        "L2_JOINT_HMM_HIGH_AND_K12_HIGH",
        "L2_INTERACTION_HMM_X_K12",
        "L3_TGTCUR_FIRES",
        "L3_TGTCUR_DOES_NOT_FIRE",
    )
    l4_h_bound = tuple(
        v for v in (
            "L4_TARGET_A1_UNMOD", "L4_TARGET_A1_MOD",
            "L4_TARGET_A2_UNMOD", "L4_TARGET_A2_MOD",
            "L4_TARGET_A3_UNMOD", "L4_TARGET_A3_MOD",
            "L4_TRAIL_B1_UNMOD", "L4_TRAIL_B1_MOD",
            "L4_TRAIL_B2_UNMOD", "L4_TRAIL_B2_MOD",
            "L4_SIZE_UNMOD", "L4_SIZE_MOD",
        )
    )
    holds = tuple(v for v in (
        "L4_HOLD_4_UNMOD", "L4_HOLD_4_MOD",
        "L4_HOLD_12_UNMOD", "L4_HOLD_12_MOD",
        "L4_HOLD_24_UNMOD", "L4_HOLD_24_MOD",
    ))
    common = {
        "source": "Z-VOL",
        "clock": "H1",
        "H": 12,
    }
    for z in (1.5, 2.0, 2.5, 3.0):
        for event_type in ("E-TOUCH", "E-CLOSE", "E-HORIZON"):
            for policy in ("P-MOMO", "P-MR"):
                for base_h in (4, 12, 24):
                    for variant_id in non_l4 + l4_h_bound:
                        rows.append({
                            **common,
                            "z": z,
                            "event_type": event_type,
                            "policy": policy,
                            "variant_id": variant_id,
                            "base_h": base_h,
                            "h": base_h,
                            "hold_bars": None,
                        })
                for variant_id in holds:
                    hold_bars = int(variant_id.split("_")[2])
                    rows.append({
                        **common,
                        "z": z,
                        "event_type": event_type,
                        "policy": policy,
                        "variant_id": variant_id,
                        "base_h": None,
                        "h": hold_bars,
                        "hold_bars": hold_bars,
                    })
    if len({cell_manifest_key(row) for row in rows}) != len(rows):
        raise AssertionError("primary cell manifest contains duplicate keys")
    return rows


def expected_full_cell_manifest() -> list[dict]:
    """Expand the exact no-L5 phase-(a) shape over clock/source/H."""
    rows = []
    for clock in ("H1", "H4"):
        for source in ("Z-VOL", "Z-MAG", "Z-MAG-SENS"):
            for horizon in (4, 12, 24):
                for base in expected_primary_cell_manifest():
                    rows.append({
                        **base,
                        "clock": clock,
                        "source": source,
                        "H": horizon,
                    })
    if len({cell_manifest_key(row) for row in rows}) != len(rows):
        raise AssertionError("full cell manifest contains duplicate keys")
    return rows


def expand_manifest_bands(rows: list[dict]) -> list[dict]:
    return [
        {**row, "band": band}
        for row in rows
        for band in ("TRAIN", "DESIGN", "CONFIRM")
    ]


def reconcile_metrics_to_manifest(
    metrics_frame: pd.DataFrame,
    structural_manifest: list[dict],
) -> pd.DataFrame:
    """Left-join scored rows onto the exact 3-band manifest.

    Missing cells remain explicit empty rows instead of disappearing.
    """
    declared = pd.DataFrame(expand_manifest_bands(structural_manifest))
    key_columns = [
        "variant_id", "source", "clock", "z", "H", "event_type", "policy",
        "base_h", "hold_bars", "band",
    ]
    actual = metrics_frame.copy()
    if "base_h" not in actual.columns:
        is_hold = actual["variant_id"].astype(str).str.startswith("L4_HOLD_")
        actual["base_h"] = actual["h"].where(~is_hold, None)
    if "hold_bars" not in actual.columns:
        is_hold = actual["variant_id"].astype(str).str.startswith("L4_HOLD_")
        actual["hold_bars"] = actual["h"].where(is_hold, None)

    def add_key(frame: pd.DataFrame) -> pd.DataFrame:
        frame = frame.copy()
        keys = frame[key_columns].fillna("<NONE>").astype(str)
        frame["manifest_key"] = keys.apply(
            lambda row: "|".join(map(str, row)),
            axis=1,
        )
        return frame

    declared = add_key(declared)
    actual = add_key(actual)
    if actual["manifest_key"].duplicated().any():
        raise ValueError("scored metrics contain duplicate structural cells")
    payload_columns = [
        column
        for column in actual.columns
        if column not in key_columns and column != "h"
    ]
    reconciled = declared.merge(
        actual[payload_columns],
        on="manifest_key",
        how="left",
        validate="one_to_one",
    )
    reconciled["empty"] = reconciled["log_R"].isna()
    return reconciled


def aggregate_cell_population(coverage: "Any", *, band: str) -> dict:
    """Pool exact sufficient counts for one already-filtered cell."""
    frame = coverage
    if band != "TRAIN":
        frame = frame[frame["band"] == band]
    totals = {
        key: int(frame[key].fillna(0).sum()) if len(frame) else 0
        for key in ("n_origins", "n_events", "n_undecided")
    }
    totals["p_event"] = (
        totals["n_events"] / totals["n_origins"]
        if totals["n_origins"]
        else float("nan")
    )
    return totals


def exact_complement(
    population: "Any",
    selected: "Any",
    *,
    key_columns: tuple[str, ...],
):
    """Return population minus selected keys, asserting a true partition."""
    selected_keys = set(map(tuple, selected.loc[:, key_columns].itertuples(index=False, name=None)))
    base_keys = population.loc[:, key_columns].apply(tuple, axis=1)
    complement = population.loc[~base_keys.isin(selected_keys)].copy()
    complement_keys = set(
        map(tuple, complement.loc[:, key_columns].itertuples(index=False, name=None))
    )
    if selected_keys & complement_keys:
        raise AssertionError("selection and complement overlap")
    if selected_keys | complement_keys != set(base_keys):
        raise AssertionError("selection and complement are not exhaustive")
    return complement


def l4_boundary_source(device: str, source: str) -> str:
    if device == "hold":
        return "NONE_TIME_EXIT"
    if device == "size":
        return "NONE"
    if device in ("target", "trail"):
        return source
    raise ValueError(f"unknown L4 device: {device}")


def l4_source_distance_bps(
    *,
    source: str,
    forecast_bps: float,
    median_bps: float,
    h_hours: float,
    multiplier: float,
    modulated: bool,
) -> dict:
    """Resolve the AMENDMENT-19 source-local target/trail distance."""
    chosen = forecast_bps if modulated else median_bps
    if not np.isfinite(chosen) or chosen <= 0:
        raise ValueError(f"missing source-specific forecast for {source}")
    if source == "Z-VOL":
        geometry = float(chosen * np.sqrt(h_hours))
    elif source in ("Z-MAG", "Z-MAG-SENS"):
        geometry = float(chosen)
    else:
        raise ValueError(f"unknown source: {source}")
    return {
        "distance_bps": float(multiplier * geometry),
        "boundary_source": source,
        "forecast_value_bps": float(forecast_bps),
        "forecast_median_bps": float(median_bps),
    }


@dataclass
class Episode:
    symbol: str
    clock: str
    source: str
    z: float
    H: int
    event_type: str
    h: int
    policy: str
    variant_id: str
    side: int  # trade side
    breach_side: int
    event_idx: int
    entry_idx: int
    entry_ts: int
    entry_price: float
    exit_ts: int
    exit_price: float
    exit_reason: str
    r_bps: float
    weight: float
    s_hat_bps: float
    band: str
    suppressed: bool = False
    target_price: float = float("nan")
    trail_width_bps: float = float("nan")
    fill_m1_idx: int = -1
    undecided: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


def _band_of(ts: int) -> str:
    if DESIGN_START_NS <= ts < DESIGN_END_NS:
        return "DESIGN"
    if DESIGN_END_NS <= ts < TRAIN_END_NS:
        return "CONFIRM"
    return "OUT"


def _horizon_hours(clock: str, h_bars: float) -> float:
    minutes = 60 if clock == "H1" else 240
    return float(h_bars) * minutes / 60.0


def _horizon_scale_bps(s_hat_bps: float, h_hours: float) -> float:
    if not np.isfinite(s_hat_bps) or h_hours <= 0:
        return float("nan")
    return float(s_hat_bps * np.sqrt(h_hours))


def _parse_l4(variant_id: str) -> dict[str, Any]:
    if variant_id.startswith("L4_TARGET_A"):
        rest = variant_id[len("L4_TARGET_A"):]
        a = int(rest[0])
        return {"device": "target", "a": a, "mod": rest.endswith("_MOD")}
    if variant_id.startswith("L4_TRAIL_B"):
        rest = variant_id[len("L4_TRAIL_B"):]
        b = int(rest[0])
        return {"device": "trail", "b": b, "mod": rest.endswith("_MOD")}
    if variant_id.startswith("L4_HOLD_"):
        body = variant_id[len("L4_HOLD_"):]
        h_str, mode = body.split("_", 1)
        return {"device": "hold", "h_bars": float(h_str), "mod": mode == "MOD"}
    if variant_id.startswith("L4_SIZE_"):
        return {"device": "size", "mod": variant_id.endswith("_MOD")}
    raise KeyError(variant_id)


def _select_at_breach(pack: SeriesPack, event_idx: int, variant_id: str) -> tuple[bool, str]:
    if variant_id == "L0_BASELINE" or variant_id.startswith("L4_"):
        if variant_id.endswith("_MOD") and "HOLD" in variant_id:
            npr = pack.n_prior_trans[event_idx] if pack.n_prior_trans.size else 0
            if not np.isfinite(npr) or npr < MOD_HOLD_MIN_PRIOR_TRANS:
                return False, "MOD_HOLD_WARMUP"
        return True, "OK"
    i = event_idx
    if variant_id == "L2_SHOCK_HMM":
        v = pack.s_hmm_rv[i] if pack.s_hmm_rv.size else np.nan
        if not np.isfinite(v) or v < 0:
            return False, "HMM_NO_STATE"
        return int(v) == 1, "HMM_LOW"
    if variant_id == "L2_LEVEL_RMARKOV_K4":
        p = pack.p_rmarkov_k4[i] if pack.p_rmarkov_k4.size else np.nan
        if not np.isfinite(p):
            return False, "RMARKOV_K4_NA"
        return p >= 0.5, "RMARKOV_K4_LOW"
    if variant_id == "L2_LEVEL_RMARKOV_K12":
        p = pack.p_rmarkov_k12[i] if pack.p_rmarkov_k12.size else np.nan
        if not np.isfinite(p):
            return False, "RMARKOV_K12_NA"
        return p >= 0.5, "RMARKOV_K12_LOW"
    if variant_id == "L2_JOINT_HMM_HIGH_AND_K12_HIGH":
        v = pack.s_hmm_rv[i] if pack.s_hmm_rv.size else np.nan
        p = pack.p_rmarkov_k12[i] if pack.p_rmarkov_k12.size else np.nan
        if not np.isfinite(v) or v < 0 or not np.isfinite(p):
            return False, "JOINT_NA"
        return (int(v) == 1) and (p >= 0.5), "JOINT_OFF"
    if variant_id == "L3_TGTCUR_FIRES":
        v = pack.tgtcur_fires[i] if pack.tgtcur_fires.size else np.nan
        if not np.isfinite(v):
            return False, "TGTCUR_NA"
        return int(v) == 1, "TGTCUR_OFF"
    if variant_id == "L3_TGTCUR_DOES_NOT_FIRE":
        v = pack.tgtcur_fires[i] if pack.tgtcur_fires.size else np.nan
        if not np.isfinite(v):
            return False, "TGTCUR_NA"
        return int(v) == 0, "TGTCUR_ON"
    return False, "UNKNOWN_VARIANT"


def _active_hold_bars(pack: SeriesPack, event_idx: int, variant_id: str, meta: dict, h_default: int) -> float:
    if not variant_id.startswith("L4_") or meta.get("device") != "hold":
        return float(h_default)
    h = float(meta["h_bars"])
    if not meta["mod"]:
        return h
    p_stay = pack.p_stay[event_idx] if pack.p_stay.size else np.nan
    if not np.isfinite(p_stay) or p_stay <= 0 or p_stay >= 1:
        return float("nan")
    e_run = float(np.clip(p_stay / (1.0 - p_stay), E_RUN_CLIP[0], E_RUN_CLIP[1]))
    return float(np.clip(h * e_run / H_MOD_DIVISOR, H_MOD_CLIP_BARS[0], H_MOD_CLIP_BARS[1]))


def _exit_params(
    pack: SeriesPack,
    *,
    entry_price: float,
    event_idx: int,
    source: str,
    trade_side: int,
    variant_id: str,
    meta: dict,
    h_bars: float,
    clock: str,
) -> tuple[float | None, float | None, float, dict]:
    weight = 1.0
    if not variant_id.startswith("L4_"):
        return None, None, weight, {}
    if source == "Z-VOL":
        series = pack.sigma_zvol
    elif source == "Z-MAG":
        series = pack.sigma_zmag
    elif source == "Z-MAG-SENS":
        series = pack.sigma_zmag / 2.0
    else:
        raise ValueError(source)
    source_value = float(series[event_idx]) if event_idx < series.size else float("nan")
    source_median = float(pack.source_train_medians.get(source, float("nan")))
    if not (
        np.isfinite(source_value)
        and source_value > 0
        and np.isfinite(source_median)
        and source_median > 0
    ):
        raise ValueError(f"missing source-specific forecast for {source}")
    h_hours = _horizon_hours(clock, h_bars)
    provenance = {
        "cell_source": source,
        "forecast_origin_t0": int(event_idx),
        "forecast_value_bps": source_value,
        "forecast_median_bps": source_median,
        "boundary_source": l4_boundary_source(meta["device"], source),
    }
    if meta["device"] == "target":
        resolved = l4_source_distance_bps(
            source=source,
            forecast_bps=source_value,
            median_bps=source_median,
            h_hours=h_hours,
            multiplier=meta["a"],
            modulated=meta["mod"],
        )
        w_bps = resolved["distance_bps"]
        width = bps_to_price_width(entry_price, w_bps)
        return entry_price + trade_side * width, None, weight, provenance
    if meta["device"] == "trail":
        resolved = l4_source_distance_bps(
            source=source,
            forecast_bps=source_value,
            median_bps=source_median,
            h_hours=h_hours,
            multiplier=meta["b"],
            modulated=meta["mod"],
        )
        return (
            None,
            bps_to_price_width(entry_price, resolved["distance_bps"]),
            weight,
            provenance,
        )
    if meta["device"] == "size":
        if meta["mod"]:
            if not (
                np.isfinite(source_value)
                and source_value > 0
                and np.isfinite(source_median)
                and source_median > 0
            ):
                raise ValueError(f"missing source-specific forecast for {source}")
            weight = float(
                np.clip(source_median / source_value, SIZE_CLIP[0], SIZE_CLIP[1])
            )
        return None, None, weight, provenance
    return None, None, weight, provenance


def build_l0_from_posts(
    pack: SeriesPack,
    posts: list[dict],
    *,
    source: str,
    z: float,
    H: int,
    event_type: str,
    h: int,
    p_event: float,
    n_undecided: int,
    n_origins: int,
    n_events: int,
) -> list[Episode]:
    """L0: both trade sides on residual time-exit posts (unstopped r_h)."""
    episodes: list[Episode] = []
    for p in posts:
        breach_side = int(p["breach_side"])
        for policy, trade_side in (("P-MOMO", breach_side), ("P-MR", -breach_side)):
            r = float(trade_side * 1e4 * (p["exit_open"] / p["entry_open"] - 1.0))
            episodes.append(Episode(
                symbol=pack.symbol, clock=pack.clock, source=source, z=z, H=H,
                event_type=event_type, h=h, policy=policy, variant_id="L0_BASELINE",
                side=trade_side, breach_side=breach_side,
                event_idx=int(p["event_idx"]), entry_idx=int(p["entry_idx"]),
                entry_ts=int(p["entry_ts"]), entry_price=float(p["entry_open"]),
                exit_ts=int(p["exit_ts"]), exit_price=float(p["exit_open"]),
                exit_reason=EXIT_TIME, r_bps=r, weight=1.0,
                s_hat_bps=float(p.get("sigma_bps", float("nan"))),
                band=p.get("band") or _band_of(int(p["entry_ts"])),
                extra={
                    "p_event": p_event, "n_undecided": n_undecided,
                    "n_origins": n_origins, "n_events": n_events,
                    "label": p.get("label"),
                    "decision_move_bps": (
                        float(pack.abs_oo[int(p["event_idx"])])
                        if int(p["event_idx"]) < pack.abs_oo.size
                        else float("nan")
                    ),
                },
            ))
    return episodes


def select_layer(l0: list[Episode], pack: SeriesPack, variant_id: str) -> list[Episode]:
    out: list[Episode] = []
    for ep in l0:
        ok, _why = _select_at_breach(pack, ep.event_idx, variant_id)
        if not ok:
            continue
        out.append(Episode(**{**ep.__dict__, "variant_id": variant_id}))
    return out


def build_l4_episodes(
    pack: SeriesPack,
    posts: list[dict],
    *,
    source: str,
    z: float,
    H: int,
    event_type: str,
    h: int,
    variant_id: str,
    p_event: float,
    n_undecided: int,
    n_origins: int,
    n_events: int,
) -> list[Episode]:
    """L4: same entries as residual posts; device-specific M1 exit; per-side exclusivity."""
    meta = _parse_l4(variant_id)
    episodes: list[Episode] = []
    # exclusivity per trade side stream
    open_until = {"P-MOMO": -1, "P-MR": -1}
    m1 = pack.m1
    if not m1 or m1["ts"].size == 0:
        return episodes

    for p in sorted(posts, key=lambda x: x["entry_ts"]):
        breach_side = int(p["breach_side"])
        entry_ts = int(p["entry_ts"])
        entry_price = float(p["entry_open"])
        event_idx = int(p["event_idx"])
        fill_m1 = first_m1_at_or_after(m1["ts"], entry_ts)
        if fill_m1 >= m1["ts"].size:
            continue
        # entry M1 is at open; resolver starts after fill_m1
        for policy, trade_side in (("P-MOMO", breach_side), ("P-MR", -breach_side)):
            ok, _ = _select_at_breach(pack, event_idx, variant_id)
            if not ok:
                continue
            if entry_ts < open_until[policy]:
                episodes.append(Episode(
                    symbol=pack.symbol,
                    clock=pack.clock,
                    source=source,
                    z=z,
                    H=H,
                    event_type=event_type,
                    h=h,
                    policy=policy,
                    variant_id=variant_id,
                    side=trade_side,
                    breach_side=breach_side,
                    event_idx=event_idx,
                    entry_idx=int(p["entry_idx"]),
                    entry_ts=entry_ts,
                    entry_price=entry_price,
                    exit_ts=-1,
                    exit_price=float("nan"),
                    exit_reason="SUPPRESSED",
                    r_bps=float("nan"),
                    weight=1.0,
                    s_hat_bps=float("nan"),
                    band=p.get("band") or _band_of(entry_ts),
                    suppressed=True,
                    extra={
                        "p_event": p_event,
                        "n_undecided": n_undecided,
                        "n_origins": n_origins,
                        "n_events": n_events,
                        "suppressed_by_open_until": open_until[policy],
                    },
                ))
                continue
            h_bars = _active_hold_bars(pack, event_idx, variant_id, meta, h)
            if not np.isfinite(h_bars):
                continue
            # hold device overrides h; others use the grid h for time exit
            if meta.get("device") == "hold":
                h_use = h_bars
            else:
                h_use = float(h)
            forecast_origin_t0 = int(p["t_idx"])
            try:
                tgt, trail_w, weight, boundary_provenance = _exit_params(
                    pack,
                    entry_price=entry_price,
                    event_idx=forecast_origin_t0,
                    source=source,
                    trade_side=trade_side,
                    variant_id=variant_id,
                    meta=meta,
                    h_bars=h_use,
                    clock=pack.clock,
                )
            except ValueError:
                episodes.append(Episode(
                    symbol=pack.symbol,
                    clock=pack.clock,
                    source=source,
                    z=z,
                    H=H,
                    event_type=event_type,
                    h=h,
                    policy=policy,
                    variant_id=variant_id,
                    side=trade_side,
                    breach_side=breach_side,
                    event_idx=event_idx,
                    entry_idx=int(p["entry_idx"]),
                    entry_ts=entry_ts,
                    entry_price=entry_price,
                    exit_ts=-1,
                    exit_price=float("nan"),
                    exit_reason="INELIGIBLE_MISSING_SOURCE",
                    r_bps=float("nan"),
                    weight=float("nan"),
                    s_hat_bps=float("nan"),
                    band=p.get("band") or _band_of(entry_ts),
                    extra={
                        "p_event": p_event,
                        "n_undecided": n_undecided,
                        "n_origins": n_origins,
                        "n_events": n_events,
                        "cell_source": source,
                        "forecast_origin_t0": forecast_origin_t0,
                        "forecast_value_bps": float("nan"),
                        "forecast_median_bps": float(
                            pack.source_train_medians.get(source, float("nan"))
                        ),
                        "boundary_source": l4_boundary_source(meta["device"], source),
                        "ineligible_missing_source": True,
                    },
                ))
                continue
            if meta.get("device") in ("target", "trail"):
                if (meta["device"] == "target" and tgt is None) or (
                    meta["device"] == "trail" and trail_w is None
                ):
                    continue
            if not np.isfinite(weight):
                continue
            # time exit: open of bar at entry_idx + h_use (parent rule, re-expressed)
            entry_idx = int(p["entry_idx"])
            exit_i = entry_idx + int(round(h_use))
            if exit_i >= pack.open.size:
                continue
            if int(pack.slot_start[exit_i]) >= TRAIN_END_NS:
                continue
            active_ns = int(pack.slot_start[exit_i]) - entry_ts
            if active_ns < 0:
                continue
            # For pure time/size: use parent open exit (bit-identity with residual)
            if meta.get("device") in ("hold", "size") or (
                tgt is None and trail_w is None
            ):
                exit_ts = int(pack.slot_start[exit_i])
                exit_price = float(pack.open[exit_i])
                exit_reason = EXIT_TIME
            else:
                ex = resolve_target_trail_time(
                    m1, pack.open, pack.slot_start,
                    side=trade_side, entry_price=entry_price,
                    fill_ts=entry_ts, fill_m1_idx=fill_m1,
                    active_hold_ns=active_ns,
                    target_price=tgt, trail_width_price=trail_w,
                )
                if ex is None:
                    continue
                exit_ts, exit_price, exit_reason = ex.exit_ts, ex.exit_price, ex.reason
            r = signed_r_bps(trade_side, entry_price, exit_price)
            if meta.get("device") == "size":
                r = r * weight
            s_hat = float(pack.sigma_zvol[event_idx]) if event_idx < pack.sigma_zvol.size else float("nan")
            episodes.append(Episode(
                symbol=pack.symbol, clock=pack.clock, source=source, z=z, H=H,
                event_type=event_type, h=h, policy=policy, variant_id=variant_id,
                side=trade_side, breach_side=breach_side,
                event_idx=event_idx, entry_idx=entry_idx,
                entry_ts=entry_ts, entry_price=entry_price,
                exit_ts=int(exit_ts), exit_price=float(exit_price),
                exit_reason=str(exit_reason), r_bps=float(r), weight=float(weight),
                s_hat_bps=s_hat, band=p.get("band") or _band_of(entry_ts),
                target_price=float(tgt) if tgt is not None else float("nan"),
                trail_width_bps=(
                    float(trail_w / entry_price * 1e4)
                    if trail_w is not None and entry_price > 0 else float("nan")
                ),
                fill_m1_idx=fill_m1,
                extra={
                    "p_event": p_event, "n_undecided": n_undecided,
                    "n_origins": n_origins, "n_events": n_events,
                    "h_use": h_use,
                    "decision_move_bps": (
                        float(pack.abs_oo[event_idx])
                        if event_idx < pack.abs_oo.size
                        else float("nan")
                    ),
                    **boundary_provenance,
                },
            ))
            open_until[policy] = int(exit_ts)
    return episodes


def run_grid_for_pack(
    pack: SeriesPack,
    *,
    sources: tuple[str, ...] = ("Z-VOL",),
    z_values: tuple[float, ...] = (1.5, 2.0, 2.5, 3.0),
    H_values: tuple[int, ...] = (12,),
    h_values: tuple[int, ...] = (4, 12, 24),
    event_types: tuple[str, ...] = ("E-TOUCH", "E-CLOSE", "E-HORIZON"),
    variants: tuple[str, ...] | None = None,
    bands: tuple[str, ...] = ("DESIGN", "CONFIRM"),
) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """Build zones/events/episodes for one pack. Work-unit inner loop."""
    from config import DERIVED_VARIANTS, VARIANT_IDS

    if variants is None:
        variants = VARIANT_IDS
    zones_all: list[dict] = []
    events_all: list[dict] = []
    episodes_all: list[dict] = []
    parity_posts: list[dict] = []  # residual posts for parent parity
    cell_cov: list[dict] = []

    # Parent always occupies with max hold 24, even when the reported h grid is a subset.
    occ_h = max(max(h_values) if h_values else 0, max(_H_POST_DEFAULT))

    for source in sources:
        for z in z_values:
            for H in H_values:
                for event_type in event_types:
                    # walk once per band with occupation_h=occ_h
                    events_by_band: dict[str, list] = {}
                    counts_by_band: dict[str, dict] = {}
                    for band in bands:
                        zones, events, _posts24, counts = walk_zones(
                            pack, source=source, z=z, H=H,
                            event_type=event_type, h=occ_h, band=band,
                            occupation_h=occ_h,
                        )
                        zones_all.extend(zones)
                        events_all.extend(events)
                        events_by_band[band] = events
                        counts_by_band[band] = counts

                    for h in h_values:
                        posts_by_band: dict[str, list] = {}
                        for band in bands:
                            posts = posts_from_events(pack, events_by_band.get(band, []), h=h)
                            posts_by_band[band] = posts
                            c = dict(counts_by_band.get(band, {}))
                            c["n_decided"] = len(posts)
                            cell_cov.append({
                                "symbol": pack.symbol, "clock": pack.clock,
                                "source": source, "z": z, "H": H,
                                "event_type": event_type, "h": h, "band": band,
                                **c,
                            })
                            if (
                                source == "Z-VOL" and z == 1.5 and H == 12 and h == 12
                                and event_type == "E-TOUCH" and band == "DESIGN"
                            ):
                                parity_posts.extend(posts)

                        l0: list[Episode] = []
                        for band in bands:
                            counts = counts_by_band.get(band, {})
                            n_orig = int(counts.get("n_origins", 0))
                            n_ev = int(counts.get("n_events", 0))
                            n_und = int(counts.get("n_undecided", 0))
                            p_event = n_ev / n_orig if n_orig else float("nan")
                            l0.extend(build_l0_from_posts(
                                pack,
                                posts_by_band.get(band, []),
                                source=source,
                                z=z,
                                H=H,
                                event_type=event_type,
                                h=h,
                                p_event=p_event,
                                n_undecided=n_und,
                                n_origins=n_orig,
                                n_events=n_ev,
                            ))
                        for ep in l0:
                            episodes_all.append(episode_to_row(ep))

                        for vid in variants:
                            if vid in DERIVED_VARIANTS or vid == "L0_BASELINE":
                                continue
                            if vid.startswith("L4_"):
                                meta = _parse_l4(vid)
                                if (
                                    meta.get("device") == "hold"
                                    and int(meta["h_bars"]) != h
                                ):
                                    continue
                                eps = []
                                for band in bands:
                                    counts = counts_by_band.get(band, {})
                                    n_orig = int(counts.get("n_origins", 0))
                                    n_ev = int(counts.get("n_events", 0))
                                    n_und = int(counts.get("n_undecided", 0))
                                    p_event = n_ev / n_orig if n_orig else float("nan")
                                    eps.extend(build_l4_episodes(
                                        pack,
                                        posts_by_band.get(band, []),
                                        source=source,
                                        z=z,
                                        H=H,
                                        event_type=event_type,
                                        h=h,
                                        variant_id=vid,
                                        p_event=p_event,
                                        n_undecided=n_und,
                                        n_origins=n_orig,
                                        n_events=n_ev,
                                    ))
                            else:
                                eps = select_layer(l0, pack, vid)
                            for ep in eps:
                                episodes_all.append(episode_to_row(ep))

    return zones_all, events_all, episodes_all, parity_posts, cell_cov


def episode_to_row(ep: Episode) -> dict:
    d = asdict(ep)
    extra = d.pop("extra", {}) or {}
    d.update({f"x_{k}" if k in d else k: v for k, v in extra.items()})
    # flatten known covariate keys
    for k in (
        "p_event", "n_undecided", "n_origins", "n_events", "label", "h_use",
        "cell_source", "forecast_origin_t0", "forecast_value_bps",
        "forecast_median_bps", "boundary_source",
        "decision_move_bps",
        "ineligible_missing_source",
    ):
        if k in extra:
            d[k] = extra[k]
    return d
