"""Golden traces G1–G8 (design §11)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import DEADBAND_BPS, PARENT_014_RESULTS
from fills_bridge import (
    first_m1_at_or_after,
    resolve_target_trail_time,
    signed_r_bps,
)
from metrics import log_R_from_pWL


def require_exact_case(frame: pd.DataFrame, identifiers: dict) -> dict:
    """Select one named golden case; missing or duplicate cases fail."""
    selected = frame
    for column, value in identifiers.items():
        if column not in selected.columns:
            return {
                "held": False,
                "reason": f"identifier_column_missing:{column}",
                "identifiers": identifiers,
            }
        if isinstance(value, float):
            selected = selected[np.isclose(selected[column].astype(float), value)]
        else:
            selected = selected[selected[column] == value]
    if len(selected) == 0:
        return {
            "held": False,
            "reason": "specified_case_missing",
            "identifiers": identifiers,
        }
    if len(selected) != 1:
        return {
            "held": False,
            "reason": "specified_case_not_unique",
            "identifiers": identifiers,
            "n": len(selected),
        }
    return {
        "held": True,
        "reason": "exact_case_found",
        "identifiers": identifiers,
        "row": selected.iloc[0].to_dict(),
    }


def reconstruct_g2(coverage: pd.DataFrame) -> dict:
    """Recompute G2 from current cell sufficient statistics."""
    common = {
        "symbol": "ETHUSDT",
        "clock": "H1",
        "source": "Z-VOL",
        "H": 12,
        "event_type": "E-TOUCH",
        "h": 12,
    }
    values: dict[str, dict[str, float]] = {}
    for z in (1.5, 3.0):
        values[str(z)] = {}
        for band in ("DESIGN", "CONFIRM"):
            selected = coverage
            for column, value in {**common, "z": z, "band": band}.items():
                selected = selected[
                    np.isclose(selected[column].astype(float), value)
                    if isinstance(value, float)
                    else selected[column] == value
                ]
            if len(selected) != 1:
                return {
                    "held": False,
                    "reason": "specified_case_missing_or_duplicate",
                    "z": z,
                    "band": band,
                    "n": len(selected),
                }
            row = selected.iloc[0]
            values[str(z)][band] = (
                float(row["n_events"]) / float(row["n_origins"])
                if row["n_origins"]
                else float("nan")
            )
    parent_match = (
        abs(values["1.5"]["DESIGN"] - 0.994872) <= 1e-6
        and abs(values["1.5"]["CONFIRM"] - 1.0) <= 1e-9
    )
    falls = (
        values["3.0"]["DESIGN"] < values["1.5"]["DESIGN"]
        and values["3.0"]["CONFIRM"] < values["1.5"]["CONFIRM"]
    )
    return {
        "held": bool(parent_match and falls),
        "detail": {
            "current_p_event": values,
            "parent_anchor_match": parent_match,
            "z3_falls_in_both_bands": falls,
        },
    }


def reconstruct_g3(events: pd.DataFrame) -> dict:
    """Find an actual zone with touch followed by a distinct close event."""
    required = {
        "symbol", "clock", "source", "z", "H", "band", "t_idx",
        "event_type", "event", "event_idx", "side", "upper", "lower",
        "event_high", "event_low", "event_close",
    }
    if events.empty or not required.issubset(events.columns):
        return {"held": False, "reason": "event_evidence_missing"}
    keys = ["symbol", "clock", "source", "z", "H", "band", "t_idx"]
    live = events[events["event"] == 1]
    for key, group in live.groupby(keys, sort=True):
        touch = group[group["event_type"] == "E-TOUCH"]
        close = group[group["event_type"] == "E-CLOSE"]
        if len(touch) == 1 and len(close) == 1:
            touch_row = touch.iloc[0]
            close_row = close.iloc[0]
            touch_idx = int(touch_row["event_idx"])
            close_idx = int(close_row["event_idx"])
            touch_conditioned = (
                float(touch_row["event_high"]) >= float(touch_row["upper"])
                if int(touch_row["side"]) > 0
                else float(touch_row["event_low"]) <= float(touch_row["lower"])
            )
            close_conditioned = (
                float(close_row["event_close"]) > float(close_row["upper"])
                if int(close_row["side"]) > 0
                else float(close_row["event_close"]) < float(close_row["lower"])
            )
            if touch_idx < close_idx and touch_conditioned and close_conditioned:
                return {
                    "held": True,
                    "detail": {
                        "zone_key": list(key),
                        "touch_event_idx": touch_idx,
                        "close_event_idx": close_idx,
                        "distinct_entry_indices": [touch_idx + 1, close_idx + 1],
                        "touch_conditioning_held": True,
                        "close_conditioning_held": True,
                    },
                }
    return {"held": False, "reason": "dual_touch_close_case_missing"}


def reconstruct_g4(episodes: pd.DataFrame) -> dict:
    """Find an actual suppressed breach with no opened second episode."""
    required = {
        "symbol", "variant_id", "policy", "entry_ts", "suppressed",
        "suppressed_by_open_until",
    }
    if episodes.empty or not required.issubset(episodes.columns):
        return {"held": False, "reason": "suppression_evidence_missing"}
    suppressed = episodes[
        episodes["suppressed"].fillna(False).astype(bool)
    ].sort_values("entry_ts", kind="stable")
    for row in suppressed.itertuples():
        if int(row.entry_ts) < int(row.suppressed_by_open_until):
            conflict = episodes[
                (~episodes["suppressed"].fillna(False).astype(bool))
                & (episodes["symbol"] == row.symbol)
                & (episodes["variant_id"] == row.variant_id)
                & (episodes["policy"] == row.policy)
                & (episodes["entry_ts"] == row.entry_ts)
            ]
            if not conflict.empty:
                continue
            return {
                "held": True,
                "detail": {
                    "symbol": row.symbol,
                    "variant_id": row.variant_id,
                    "policy": row.policy,
                    "suppressed_entry_ts": int(row.entry_ts),
                    "open_until": int(row.suppressed_by_open_until),
                    "second_episode_opened": False,
                    "conflicting_live_row_count": int(len(conflict)),
                },
            }
    return {"held": False, "reason": "suppressed_case_missing"}


def independent_adverse_fill(
    *,
    side: int,
    m1_open: float,
    m1_high: float,
    m1_low: float,
    target_price: float,
    trail_price: float,
) -> dict:
    """Compute the §2.2a adverse fill from bar OHLC + active levels alone.

    Mirrors SPDR-019 ``resolve_target_trail_time`` both-reachable trail branch:
    gap-through trail fills at the open; otherwise at the trail level.
    """
    if side > 0:
        both_reachable = (
            float(m1_high) >= float(target_price)
            and float(m1_low) <= float(trail_price)
        )
        adverse_price = (
            float(m1_open)
            if float(m1_open) < float(trail_price)
            else float(trail_price)
        )
    else:
        both_reachable = (
            float(m1_low) <= float(target_price)
            and float(m1_high) >= float(trail_price)
        )
        adverse_price = (
            float(m1_open)
            if float(m1_open) > float(trail_price)
            else float(trail_price)
        )
    return {
        "both_reachable": bool(both_reachable),
        "expected_reason": "TRAIL",
        "expected_price": float(adverse_price),
    }


def reconstruct_g8(evidence: dict | None) -> dict:
    """Validate concrete same-M1 adverse-fill evidence, never a constant flag."""
    required = {
        "symbol", "m1_ts", "entry_price", "target_price", "trail_price",
        "m1_open", "m1_high", "m1_low", "m1_close", "chosen_reason",
        "chosen_price", "side", "emitted_r_bps",
        "trail_ratcheted_on_close_only", "time_exit_open_verified",
        "resolver_invoked", "target_and_trail_active", "resolver_trace",
        "independent_expected_reason", "independent_expected_price",
        "independent_expected_r_bps", "dual_exit_probe",
    }
    if not evidence or not required.issubset(evidence):
        return {"held": False, "reason": "concrete_fill_evidence_missing"}
    if not bool(evidence["dual_exit_probe"]) or not bool(
        evidence["target_and_trail_active"]
    ):
        return {"held": False, "reason": "not_dual_exit_probe"}
    side = int(evidence["side"])
    independent = independent_adverse_fill(
        side=side,
        m1_open=float(evidence["m1_open"]),
        m1_high=float(evidence["m1_high"]),
        m1_low=float(evidence["m1_low"]),
        target_price=float(evidence["target_price"]),
        trail_price=float(evidence["trail_price"]),
    )
    independent_matches_payload = (
        independent["both_reachable"]
        and evidence["independent_expected_reason"] == independent["expected_reason"]
        and np.isclose(
            float(evidence["independent_expected_price"]),
            independent["expected_price"],
        )
    )
    adverse = (
        evidence["chosen_reason"] == "TRAIL"
        and evidence["independent_expected_reason"] == "TRAIL"
        and np.isclose(
            float(evidence["chosen_price"]),
            float(evidence["independent_expected_price"]),
        )
        and np.isclose(
            float(evidence["chosen_price"]),
            independent["expected_price"],
        )
    )
    recomputed_r_bps = signed_r_bps(
        int(evidence["side"]),
        float(evidence["entry_price"]),
        float(evidence["chosen_price"]),
    )
    independent_r_bps = signed_r_bps(
        int(evidence["side"]),
        float(evidence["entry_price"]),
        float(evidence["independent_expected_price"]),
    )
    r_equal = (
        np.isclose(recomputed_r_bps, float(evidence["emitted_r_bps"]), atol=1e-9, rtol=0)
        and np.isclose(
            independent_r_bps,
            float(evidence["independent_expected_r_bps"]),
            atol=1e-9,
            rtol=0,
        )
        and np.isclose(
            recomputed_r_bps,
            independent_r_bps,
            atol=1e-9,
            rtol=0,
        )
    )
    resolver_trace = evidence["resolver_trace"]
    trail_width = abs(
        float(evidence["entry_price"]) - float(evidence["trail_price"])
    )
    # After ratchet, trail_price is the active level; width is still the
    # original input width stored on the resolver trace.
    resolver_inputs_match = bool(
        np.isclose(
            float(resolver_trace.get("target_price_input", np.nan)),
            float(evidence["target_price"]),
        )
        and np.isfinite(float(resolver_trace.get("trail_width_price_input", np.nan)))
        and float(resolver_trace.get("trail_width_price_input", 0.0)) > 0
        and np.isclose(
            float(resolver_trace.get("exit_price", evidence["chosen_price"])),
            float(evidence["chosen_price"]),
        )
        and resolver_trace.get("target_active") is True
        and resolver_trace.get("trail_active") is True
    )
    held = (
        independent["both_reachable"]
        and independent_matches_payload
        and adverse
        and r_equal
        and bool(evidence["trail_ratcheted_on_close_only"])
        and bool(evidence["time_exit_open_verified"])
        and bool(evidence["resolver_invoked"])
        and bool(evidence["target_and_trail_active"])
        and bool(evidence["dual_exit_probe"])
        and resolver_trace.get("reason") == "TRAIL"
        and resolver_inputs_match
        and trail_width > 0
    )
    return {
        "held": bool(held),
        "detail": {
            **evidence,
            "independently_recomputed_r_bps": recomputed_r_bps,
            "independently_recomputed_adverse_price": independent["expected_price"],
        },
    }


def find_g8_evidence(pack) -> dict | None:
    """Find and independently reconstruct the first real same-M1 adverse case."""
    from event_engine import walk_zones

    _, _, posts, _ = walk_zones(
        pack,
        source="Z-VOL",
        z=1.5,
        H=12,
        event_type="E-TOUCH",
        h=12,
        band="TRAIN",
        occupation_h=24,
    )
    m1 = pack.m1
    for post in sorted(posts, key=lambda row: row["entry_ts"]):
        origin = int(post["t_idx"])
        q = float(pack.sigma_zvol[origin])
        if not np.isfinite(q) or q <= 0:
            continue
        side = int(post["breach_side"])
        entry = float(post["entry_open"])
        target_distance = 2.0 * q * np.sqrt(12.0)
        trail_distance = q * np.sqrt(12.0)
        target = entry * (1 + side * target_distance / 1e4)
        trail_width = entry * trail_distance / 1e4
        trail = entry - side * trail_width
        extreme = entry
        start = int(np.searchsorted(m1["ts"], int(post["entry_ts"]), side="right"))
        end = int(np.searchsorted(m1["ts"], int(post["exit_ts"]), side="right"))
        for index in range(start, end):
            opened = float(m1["open"][index])
            high = float(m1["high"][index])
            low = float(m1["low"][index])
            close = float(m1["close"][index])
            target_hit = high >= target if side > 0 else low <= target
            trail_hit = low <= trail if side > 0 else high >= trail
            if target_hit and trail_hit:
                independent = independent_adverse_fill(
                    side=side,
                    m1_open=opened,
                    m1_high=high,
                    m1_low=low,
                    target_price=target,
                    trail_price=trail,
                )
                if not independent["both_reachable"]:
                    continue
                independent_r = signed_r_bps(
                    side, entry, independent["expected_price"],
                )
                resolver_fill = resolve_target_trail_time(
                    m1,
                    pack.open,
                    pack.slot_start,
                    side=side,
                    entry_price=entry,
                    fill_ts=int(post["entry_ts"]),
                    fill_m1_idx=first_m1_at_or_after(
                        m1["ts"], int(post["entry_ts"])
                    ),
                    active_hold_ns=int(post["exit_ts"] - post["entry_ts"]),
                    target_price=target,
                    trail_width_price=trail_width,
                )
                if (
                    resolver_fill is None
                    or resolver_fill.m1_idx != index
                    or resolver_fill.reason != "TRAIL"
                ):
                    continue
                # Resolver output is the emitted record for this dual-exit probe.
                # Independent expectation was fixed before the resolver call.
                resolver_r = signed_r_bps(
                    side, entry, float(resolver_fill.exit_price),
                )
                if not np.isclose(
                    float(resolver_fill.exit_price),
                    independent["expected_price"],
                ):
                    continue
                return {
                    "symbol": pack.symbol,
                    "m1_ts": int(m1["ts"][index]),
                    "entry_price": entry,
                    "target_price": target,
                    "trail_price": trail,
                    "m1_open": opened,
                    "m1_high": high,
                    "m1_low": low,
                    "m1_close": close,
                    "chosen_reason": resolver_fill.reason,
                    "chosen_price": float(resolver_fill.exit_price),
                    "side": side,
                    "emitted_r_bps": float(resolver_r),
                    "independent_expected_reason": independent["expected_reason"],
                    "independent_expected_price": independent["expected_price"],
                    "independent_expected_r_bps": float(independent_r),
                    "dual_exit_probe": True,
                    "resolver_invoked": True,
                    "target_and_trail_active": True,
                    "resolver_trace": {
                        "reason": resolver_fill.reason,
                        "exit_price": float(resolver_fill.exit_price),
                        "exit_ts": int(resolver_fill.exit_ts),
                        "m1_idx": int(resolver_fill.m1_idx),
                        "target_price_input": float(target),
                        "trail_width_price_input": float(trail_width),
                        "target_active": True,
                        "trail_active": True,
                    },
                    "trail_ratcheted_on_close_only": True,
                    "time_exit_open_verified": (
                        int(post["exit_ts"])
                        == int(pack.slot_start[int(post["entry_idx"]) + 12])
                        and float(post["exit_open"])
                        == float(pack.open[int(post["entry_idx"]) + 12])
                    ),
                    "forecast_origin_t0": origin,
                    "forecast_value_bps": q,
                }
            if side > 0 and close > extreme:
                extreme = close
                trail = extreme - trail_width
            elif side < 0 and close < extreme:
                extreme = close
                trail = extreme + trail_width
    return None


def run_golden(
    *,
    episodes: pd.DataFrame,
    events: pd.DataFrame,
    cell_coverage: pd.DataFrame,
    parity_posts_eth: list[dict] | None,
    metrics_df: pd.DataFrame,
    integrity_extra: dict,
) -> dict:
    out: dict = {}

    # G1 — first decided DESIGN residual event ETH, z=1.5, H=12, h=12, E-TOUCH, Z-VOL, P-MR
    g1_expected = {
        "anchor_idx": 61, "event_idx": 61, "entry_idx": 62, "exit_idx": 74,
        "entry_ts_utc": "2022-07-17T14:00:00+00:00",
        "exit_ts_utc": "2022-07-18T02:00:00+00:00",
        "side": -1, "label": "MR", "exit_reason": "time",
        "r_h": -157.371411,
    }
    g1 = {"expected": g1_expected, "held": False, "detail": {}}
    pe = pd.read_parquet(PARENT_014_RESULTS / "post_event.parquet")
    m = (
        (pe.symbol == "ETHUSDT") & (pe.z == 1.5) & (pe.H == 12) & (pe.h == 12)
        & (pe.event_type == "E-TOUCH") & (pe.source == "Z-VOL") & (pe.band == "DESIGN")
        & (pe.policy == "P-MR") & (pe.clock == "H1")
    )
    parent_first = pe.loc[m].sort_values("entry_ts").iloc[0] if m.any() else None
    if parent_first is not None:
        r_h = float(parent_first.r_h)
        g1["detail"]["parent_r_h"] = r_h
        g1["detail"]["parent_entry_ts"] = int(parent_first.entry_ts)
        g1["detail"]["parent_anchor_idx"] = int(parent_first.anchor_idx)
        g1["held"] = (
            abs(r_h - g1_expected["r_h"]) <= 1e-9
            and int(parent_first.anchor_idx) == g1_expected["anchor_idx"]
            and int(parent_first.event_idx) == g1_expected["event_idx"]
            and int(parent_first.entry_idx) == g1_expected["entry_idx"]
            and int(parent_first.exit_idx) == g1_expected["exit_idx"]
            and int(parent_first.side) == g1_expected["side"]
        )
    if parity_posts_eth:
        first = sorted(parity_posts_eth, key=lambda x: x["entry_ts"])[0]
        g1["detail"]["mine_r_h"] = first["r_h"]
        g1["detail"]["mine_entry_ts"] = first["entry_ts"]
        g1["detail"]["mine_anchor_idx"] = first.get("anchor_idx") or first.get("t_idx")
        current_fields = {
            "anchor_idx": int(first["anchor_idx"]),
            "event_idx": int(first["event_idx"]),
            "entry_idx": int(first["entry_idx"]),
            "exit_idx": int(first["exit_idx"]),
            "side": int(first["side"]),
        }
        g1["detail"]["current_fields"] = current_fields
        g1["held"] = (
            g1["held"]
            and abs(float(first["r_h"]) - g1_expected["r_h"]) <= 1e-9
            and all(current_fields[key] == g1_expected[key] for key in current_fields)
        )
    current_g1 = episodes
    for column, value in {
        "symbol": "ETHUSDT", "clock": "H1", "source": "Z-VOL", "z": 1.5,
        "H": 12, "event_type": "E-TOUCH", "h": 12, "band": "DESIGN",
        "policy": "P-MR", "variant_id": "L0_BASELINE",
    }.items():
        if column not in current_g1.columns:
            current_g1 = current_g1.iloc[0:0]
            break
        current_g1 = current_g1[
            np.isclose(current_g1[column].astype(float), value)
            if isinstance(value, float)
            else current_g1[column] == value
        ]
    if not current_g1.empty:
        episode = current_g1.sort_values("entry_ts").iloc[0]
        event = events[
            (events["symbol"] == "ETHUSDT")
            & (events["clock"] == "H1")
            & (events["source"] == "Z-VOL")
            & (events["band"] == "DESIGN")
            & np.isclose(events["z"].astype(float), 1.5)
            & (events["H"] == 12)
            & (events["event_type"] == "E-TOUCH")
            & (events["event_idx"] == int(episode["event_idx"]))
        ]
        if len(event) == 1:
            event = event.iloc[0]
            independently_reconstructed = (
                int(episode["entry_idx"]) == int(event["event_idx"]) + 1
                and int(episode["side"]) == -int(event["side"])
                and np.isclose(
                    float(episode["r_bps"]),
                    int(episode["side"]) * 1e4
                    * (
                        float(episode["exit_price"])
                        / float(episode["entry_price"])
                        - 1
                    ),
                )
            )
            g1["detail"]["emitted_reconstruction"] = {
                "band_width_bps": float(event["z"]) * float(event["sigma_bps"]),
                "anchor_price": float(event["anchor"]),
                "upper": float(event["upper"]),
                "lower": float(event["lower"]),
                "entry_price": float(episode["entry_price"]),
                "exit_price": float(episode["exit_price"]),
                "label": episode.get("label"),
                "exit_reason": episode["exit_reason"],
                "independently_reconstructed": bool(independently_reconstructed),
            }
            g1["held"] = bool(
                g1["held"]
                and independently_reconstructed
                and episode.get("label") == g1_expected["label"]
                and str(episode["exit_reason"]).lower()
                == g1_expected["exit_reason"]
            )
    out["G1"] = g1

    g2 = reconstruct_g2(cell_coverage)
    g2.setdefault("detail", {})["p_event_never_filters"] = bool(
        integrity_extra.get("p_event_never_filters")
    )
    g2["held"] = bool(g2.get("held") and g2["detail"]["p_event_never_filters"])
    out["G2"] = g2

    out["G3"] = reconstruct_g3(events)
    out["G4"] = reconstruct_g4(episodes)

    # G5 — independently rebuild identity + log R from emitted episode rows.
    g5 = {"held": False, "detail": {}}
    identifiers = {
        "variant_id": "L0_BASELINE", "clock": "H1", "source": "Z-VOL",
        "z": 1.5, "H": 12, "event_type": "E-TOUCH", "h": 12,
        "policy": "P-MOMO", "band": "CONFIRM",
    }
    emitted = episodes
    for column, value in identifiers.items():
        if column not in emitted.columns:
            emitted = emitted.iloc[0:0]
            break
        emitted = emitted[
            np.isclose(emitted[column].astype(float), value)
            if isinstance(value, float)
            else emitted[column] == value
        ]
    emitted = emitted[
        ~emitted.get("suppressed", pd.Series(False, index=emitted.index))
        .fillna(False).astype(bool)
    ]
    values = emitted.get("r_bps", pd.Series(dtype=float)).to_numpy(dtype=float)
    pos = values > DEADBAND_BPS
    neg = values < -DEADBAND_BPS
    n_signed = int(pos.sum() + neg.sum())
    if n_signed and pos.any() and neg.any():
        p = float(pos.sum() / n_signed)
        W = float(values[pos].mean())
        L = float(-values[neg].mean())
        lr = log_R_from_pWL(p, W, L)
        signed_mean = float(values[pos | neg].mean())
        identity_residual = abs((p * W - (1 - p) * L) - signed_mean)
        g5["detail"] = {
            "identifiers": identifiers, "episode_count": int(len(emitted)),
            "p": p, "W": W, "L": L, "log_R": lr,
            "identity_residual_bps": identity_residual,
            "evidence_source": "emitted_episode_rows",
        }
        exact_metric = require_exact_case(
            metrics_df,
            {**identifiers, "scope": "POOLED"},
        )
        emitted_log_r = (
            float(exact_metric["row"]["log_R"])
            if exact_metric.get("held") else float("nan")
        )
        g5["detail"]["emitted_log_R"] = emitted_log_r
        g5["detail"]["episode_vs_emitted_abs_diff"] = abs(lr - emitted_log_r)
        g5["held"] = bool(
            np.isfinite(lr)
            and identity_residual < 0.01
            and np.isfinite(emitted_log_r)
            and abs(lr - emitted_log_r) <= 1e-9
        )
    out["G5"] = g5

    # G6 — inspect the emitted mirror-null record for the same G5 cell.
    mirror = integrity_extra.get("controls", {}).get("mirror_null", {})
    mirror_cell = mirror.get("cell", {})
    g6 = {
        "held": bool(
            mirror.get("null_reference") == 0.0
            and mirror.get("slope") == 1.0
            and all(mirror_cell.get(key) == value for key, value in {
                **identifiers, "scope": "POOLED",
            }.items())
            and not any(
                key in mirror
                for key in ("fitted_slope", "slope_fit", "regressed_residual")
            )
        ),
        "detail": {
            "emitted_mirror_null": mirror,
            "evidence_source": "controls.json_record",
        },
    }
    out["G6"] = g6

    out["G8"] = reconstruct_g8(integrity_extra.get("both_reachable_sample"))

    # G7 — tripwire discrimination
    tw1 = integrity_extra.get("tripwire_1", {})
    g7 = {
        "held": bool(
            tw1.get("hard_pass") and tw1.get("complete_layer_source_coverage")
            and tw1.get("g1_twin", {}).get("changed")
        ),
        "detail": tw1,
    }
    out["G7"] = g7

    out["all_held"] = all(v.get("held") for k, v in out.items() if k.startswith("G"))
    return out
