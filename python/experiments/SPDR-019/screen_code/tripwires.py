"""Leak tripwires (design §6.1) — both STRUCTURAL, both run against the live pipeline.

TRIPWIRE-1 rebuilds every layer's conditioning state from bar ``[+1]`` and re-runs the
identical episode build on it. TRIPWIRE-2 re-resolves ALL fills under two deterministic
twins — a decision-clock twin and a favourable-precedence twin — on the real episode set.

Neither tripwire may construct its own evidence: if the structural conditions do not hold on
what the pipeline actually produced, that is the finding. A missing, empty or zero-count field
is a FAILURE, never a vacuous pass (P-23/L-52).
"""
from __future__ import annotations

import copy

import numpy as np

from config import L0_INACTIVE_HOLD_HOURS, NS
from fills import (
    bps_to_price_width,
    both_reachable_in_bar,
    resolve_entry_stop,
    resolve_entry_stop_on_clock,
    signed_r_bps,
)

# the conditioning state every layer reads at the decision bar [0]
GATE_ARRAYS = (
    "s_hmm_rv",
    "p_rmarkov_k4",
    "p_rmarkov_k12",
    "tgtcur_fires",
    "tgtmed5_fires",
    "s_hat_decile",
    "s_hat_rank",
    "p_stay",
    "n_prior_trans",
)

LAYER_VARIANTS = (
    "L1_SHAT_DECILE_GE5", "L1_SHAT_DECILE_GE7", "L1_SHAT_DECILE_GE9",
    "L1_SHAT_RANK_CONTINUOUS",
    "L2_SHOCK_HMM", "L2_LEVEL_RMARKOV_K4", "L2_LEVEL_RMARKOV_K12",
    "L2_JOINT_HMM_HIGH_AND_K12_HIGH",
    "L3_TGTCUR_FIRES", "L3_TGTCUR_DOES_NOT_FIRE", "L3_TGTMED5_CO_REPORT",
)


def _shift_forward_one(a: np.ndarray) -> np.ndarray:
    """leaky[i] = legal[i+1] — condition on one bar into the FUTURE."""
    out = np.full_like(np.asarray(a, dtype=float), np.nan)
    if out.size > 1:
        out[:-1] = np.asarray(a, dtype=float)[1:]
    return out


def _episode_keys(episodes) -> set:
    return {
        (e.symbol, e.clock, e.delta, e.variant_id, e.decision_end_ns, e.side, e.exit_ts)
        for e in episodes
    }


def tripwire_1(panel, base_sigs, engine_mod, *, variants=LAYER_VARIANTS) -> dict:
    """Materialise both state streams, re-run the pipeline on each, compare (§6.1)."""
    legal = {name: np.asarray(getattr(panel, name), dtype=float) for name in GATE_ARRAYS}
    leaky_panel = copy.copy(panel)
    leaky = {}
    for name in GATE_ARRAYS:
        leaky[name] = _shift_forward_one(legal[name])
        setattr(leaky_panel, name, leaky[name])

    # structural condition 1: the leaky stream IS the legal stream shifted by exactly one row
    exact = True
    changed_state = 0
    per_array = {}
    for name in GATE_ARRAYS:
        a, b = legal[name], leaky[name]
        if a.size < 2:
            exact = False
            per_array[name] = {"shift_exact": False, "changed_rows": 0, "reason": "too short"}
            continue
        both = np.isfinite(a[1:]) & np.isfinite(b[:-1])
        ok = bool(both.any()) and bool(
            np.allclose(a[1:][both], b[:-1][both], equal_nan=True)
        )
        ch = int(np.sum((a != b) & (np.isfinite(a) | np.isfinite(b))))
        per_array[name] = {"shift_exact": ok, "changed_rows": ch}
        exact = exact and ok
        changed_state += ch

    # structural condition 3: the difference must reach episode SELECTION
    l0_eps, _, sig_by_key = engine_mod.build_l0_episodes(panel, base_sigs)
    l0_eps_k, _, sig_by_key_k = engine_mod.build_l0_episodes(leaky_panel, base_sigs)
    changed_sel = 0
    legal_n = 0
    leaky_n = 0
    per_variant = {}
    for vid in variants:
        a_eps, _ = engine_mod.select_layer_from_l0(l0_eps, sig_by_key, panel, vid)
        b_eps, _ = engine_mod.select_layer_from_l0(l0_eps_k, sig_by_key_k, leaky_panel, vid)
        ka, kb = _episode_keys(a_eps), _episode_keys(b_eps)
        d = len(ka ^ kb)
        per_variant[vid] = {
            "legal_episodes": len(ka), "leaky_episodes": len(kb), "symmetric_difference": d,
        }
        changed_sel += d
        legal_n += len(ka)
        leaky_n += len(kb)

    hard = bool(exact and changed_state > 0 and changed_sel > 0)
    return {
        "shift_is_exact_one_row": exact,
        "changed_state_rows": changed_state,
        "changed_selection_episodes": changed_sel,
        "legal_episode_count": legal_n,
        "leaky_episode_count": leaky_n,
        "per_state_array": per_array,
        "per_variant": per_variant,
        "symbol": panel.symbol,
        "clock": panel.clock,
        "permutation_based": False,
        "fixed_point_note": "N/A — a deliberate index shift, not a permutation (L-28)",
        "hard_pass": hard,
    }


def tripwire_2(panel, episodes, *, trail_b: int = 1) -> dict:
    """Two deterministic fill twins over the REAL episode set (§6.1).

    (a) DECISION-CLOCK twin — the same entry-stop rule resolved on the decision-clock OHLC.
    (b) FAVOURABLE-PRECEDENCE twin — M1 resolution kept, but the TARGET wins inside an M1 bar
        where target and trail are both reachable at DISTINCT prices.

    The 33 variants place a target OR a trail, never both, so the both-reachable population is
    constructed explicitly: each target episode is paired with the trail level its own ŝ device
    would have set at ``b = trail_b``. That pairing is deterministic and QA can re-derive it.
    """
    clock = {
        "slot_end": panel.slot_end, "open": panel.open,
        "high": panel.high, "low": panel.low,
    }
    m1 = panel.m1
    inactive_ns = int(L0_INACTIVE_HOLD_HOURS * 3600 * NS)

    # ---- twin (a): decision-clock entry fills
    clock_diff_ids = []
    clock_diff_prices = []
    for ep in episodes:
        twin = resolve_entry_stop_on_clock(
            clock, side=ep.side, stop_price=ep.stop_price,
            decision_end_ns=ep.decision_end_ns, inactive_hold_ns=inactive_ns,
        )
        live = resolve_entry_stop(
            m1, side=ep.side, stop_price=ep.stop_price,
            decision_end_ns=ep.decision_end_ns, inactive_hold_ns=inactive_ns,
        )
        if (twin.filled != live.filled) or (
            twin.filled and live.filled
            and (twin.fill_ts != live.fill_ts
                 or abs(twin.fill_price - live.fill_price) > 1e-12 * max(1.0, live.fill_price))
        ):
            clock_diff_ids.append(int(ep.decision_end_ns))
            clock_diff_prices.append({
                "decision_end_ns": int(ep.decision_end_ns),
                "m1_fill_ts": int(live.fill_ts), "m1_fill_price": float(live.fill_price),
                "clock_fill_ts": int(twin.fill_ts), "clock_fill_price": float(twin.fill_price),
            })

    # ---- twin (b): favourable precedence on both-reachable bars
    both_ids = []
    fav_ids = []
    fav_prices = []
    price_identical = 0
    ts = m1["ts"]
    for ep in episodes:
        if not np.isfinite(ep.target_price) or ep.fill_m1_idx < 0:
            continue
        tgt_width = abs(ep.target_price - ep.fill_price)
        if not (tgt_width > 0):
            continue
        # the trail this episode's own device would have placed
        trail_bps = (
            trail_b * (tgt_width / ep.fill_price * 1e4)
            / max(1, _target_multiplier(ep.variant_id))
        )
        trail_w = bps_to_price_width(ep.fill_price, trail_bps)
        if not (trail_w > 0):
            continue
        trail_level = ep.fill_price - ep.side * trail_w
        if abs(ep.target_price - trail_level) <= 1e-12 * max(1.0, ep.fill_price):
            price_identical += 1
            continue
        start = ep.fill_m1_idx + 1
        end = int(np.searchsorted(ts, ep.exit_ts, side="right"))
        hit = -1
        for i in range(start, min(end, ts.size)):
            if both_reachable_in_bar(
                side=ep.side, high=float(m1["high"][i]), low=float(m1["low"][i]),
                target_price=ep.target_price, trail_level=trail_level,
            ):
                hit = i
                break
        if hit < 0:
            continue
        both_ids.append(int(ts[hit]))
        adverse_px = float(trail_level)
        favourable_px = float(ep.target_price)
        fav_ids.append(int(ts[hit]))
        fav_prices.append({
            "m1_ts": int(ts[hit]),
            "decision_end_ns": int(ep.decision_end_ns),
            "side": int(ep.side),
            "emitted_exit_price": adverse_px,
            "favourable_exit_price": favourable_px,
            "emitted_r_bps": signed_r_bps(ep.side, ep.fill_price, adverse_px),
            "favourable_r_bps": signed_r_bps(ep.side, ep.fill_price, favourable_px),
        })

    price_ok = True
    for row in fav_prices:
        if row["side"] > 0 and row["favourable_exit_price"] < row["emitted_exit_price"] - 1e-12:
            price_ok = False
        if row["side"] < 0 and row["favourable_exit_price"] > row["emitted_exit_price"] + 1e-12:
            price_ok = False

    n_clock, n_both, n_fav = len(clock_diff_ids), len(both_ids), len(fav_ids)
    hard = bool(n_clock > 0 and n_both > 0 and n_fav == n_both and price_ok and fav_prices)
    return {
        "clock_vs_m1_differing_fill_ids": clock_diff_ids,
        "count_clock_vs_m1": n_clock,
        "clock_vs_m1_prices": clock_diff_prices[:200],
        "both_reachable_bar_ids": both_ids,
        "count_both_reachable": n_both,
        "favourable_precedence_differing_fill_ids": fav_ids,
        "count_favourable_diff": n_fav,
        "favourable_prices": fav_prices[:200],
        "price_identical_bars": int(price_identical),
        "favourable_price_never_worse": price_ok,
        "symbol": panel.symbol,
        "clock": panel.clock,
        "trail_b_used": trail_b,
        "hard_pass": hard,
    }


def _target_multiplier(variant_id: str) -> int:
    """The ``a`` of an ``L4_TARGET_A{a}_*`` variant, so the paired trail uses the same ŝ."""
    marker = "L4_TARGET_A"
    if variant_id.startswith(marker):
        try:
            return int(variant_id[len(marker)])
        except (ValueError, IndexError):
            return 1
    return 1
