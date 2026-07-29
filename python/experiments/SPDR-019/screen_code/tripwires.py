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
from dataclasses import replace

import numpy as np

from config import L0_INACTIVE_HOLD_HOURS, L4_HOLD_HOURS, NS
from fills import (
    bps_to_price_width,
    both_reachable_in_bar,
    resolve_entry_stop,
    resolve_entry_stop_on_clock,
    resolve_target_trail_time,
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

# variants whose selection or eligibility reads a gate array (R9-01)
LAYER_VARIANTS = (
    "L1_SHAT_DECILE_GE5", "L1_SHAT_DECILE_GE7", "L1_SHAT_DECILE_GE9",
    "L1_SHAT_RANK_CONTINUOUS",
    "L2_SHOCK_HMM", "L2_LEVEL_RMARKOV_K4", "L2_LEVEL_RMARKOV_K12",
    "L2_JOINT_HMM_HIGH_AND_K12_HIGH",
    "L3_TGTCUR_FIRES", "L3_TGTCUR_DOES_NOT_FIRE", "L3_TGTMED5_CO_REPORT",
) + tuple(f"L4_HOLD_{h}H_MOD" for h in L4_HOLD_HOURS)

# which gate arrays each variant's selection depends on
VARIANT_GATE_MAP: dict[str, tuple[str, ...]] = {
    "L1_SHAT_DECILE_GE5": ("s_hat_decile",),
    "L1_SHAT_DECILE_GE7": ("s_hat_decile",),
    "L1_SHAT_DECILE_GE9": ("s_hat_decile",),
    # continuous rank is eligibility-only (finite vs warm-up); selection is not a threshold
    "L1_SHAT_RANK_CONTINUOUS": ("s_hat_rank",),
    "L2_SHOCK_HMM": ("s_hmm_rv",),
    "L2_LEVEL_RMARKOV_K4": ("p_rmarkov_k4",),
    "L2_LEVEL_RMARKOV_K12": ("p_rmarkov_k12",),
    "L2_JOINT_HMM_HIGH_AND_K12_HIGH": ("s_hmm_rv", "p_rmarkov_k12"),
    "L3_TGTCUR_FIRES": ("tgtcur_fires",),
    "L3_TGTCUR_DOES_NOT_FIRE": ("tgtcur_fires",),
    "L3_TGTMED5_CO_REPORT": ("tgtmed5_fires",),
}
for _h in L4_HOLD_HOURS:
    VARIANT_GATE_MAP[f"L4_HOLD_{_h}H_MOD"] = ("p_stay", "n_prior_trans")

# threshold variants must show a selection change when their gate arrays changed
THRESHOLD_VARIANTS = frozenset(
    v for v in LAYER_VARIANTS
    if v != "L1_SHAT_RANK_CONTINUOUS"
)
# h_mod = clip(h·E_run/20, 1, 20) pins h=1 at exactly 1.0 whenever E_run ≤ 20 — the design's
# own measured E[run] scale is 19–23 h, so a p_stay shift that stays in that regime cannot
# change exit_ts. Still RUN the arm (reported in per_variant); do not require nonzero (R9-01).
CLIP_INSENSITIVE_VARIANTS = frozenset({"L4_HOLD_1H_MOD"})


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


def _rebind_signal_shat(signals, panel):
    """Re-freeze ŝ fields from the panel so L1 selection sees the shifted state (R9-01).

    ``entry.detect_signals`` freezes ``s_hat_decile`` / ``s_hat_rank`` onto the Signal at
    detection time. Shifting the panel arrays alone cannot change L1 selection unless the
    Signal stream is rebuilt from that panel.
    """
    out = []
    for s in signals:
        i = s.decision_idx
        out.append(replace(
            s,
            s_hat_bps=(
                float(panel.s_hat_bps[i])
                if panel.s_hat_bps.size and np.isfinite(panel.s_hat_bps[i])
                else float("nan")
            ),
            s_hat_decile=(
                float(panel.s_hat_decile[i])
                if panel.s_hat_decile.size and np.isfinite(panel.s_hat_decile[i])
                else float("nan")
            ),
            s_hat_rank=(
                float(panel.s_hat_rank[i])
                if panel.s_hat_rank.size and np.isfinite(panel.s_hat_rank[i])
                else float("nan")
            ),
        ))
    return out


def tripwire_1(panel, base_sigs, engine_mod, *, variants=LAYER_VARIANTS) -> dict:
    """Materialise both state streams, re-run the pipeline on each, compare (§6.1)."""
    legal = {name: np.asarray(getattr(panel, name), dtype=float) for name in GATE_ARRAYS}
    leaky_panel = copy.copy(panel)
    leaky = {}
    for name in GATE_ARRAYS:
        leaky[name] = _shift_forward_one(legal[name])
        setattr(leaky_panel, name, leaky[name])
    # ŝ source arrays also shift so rebinding L1 reads the leaky stream
    for name in ("s_hat_bps", "s_hat_decile", "s_hat_rank"):
        if hasattr(panel, name):
            setattr(leaky_panel, name, _shift_forward_one(np.asarray(getattr(panel, name), dtype=float)))

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

    # structural condition 3: the difference must reach episode SELECTION — including L1,
    # which reads ŝ off the Signal object, so both streams must rebind from their panel
    legal_sigs = _rebind_signal_shat(base_sigs, panel)
    leaky_sigs = _rebind_signal_shat(base_sigs, leaky_panel)
    l0_eps, _, sig_by_key = engine_mod.build_l0_episodes(panel, legal_sigs)
    l0_eps_k, _, sig_by_key_k = engine_mod.build_l0_episodes(leaky_panel, leaky_sigs)
    changed_sel = 0
    legal_n = 0
    leaky_n = 0
    per_variant = {}
    for vid in variants:
        if vid.startswith("L4_"):
            # L4 MOD holds depend on p_stay for the EXIT, not only on n_prior_trans eligibility.
            # select_layer_from_l0 re-tags L0 exits and is blind to hold modulation — rebuild
            # the full device so a shifted p_stay changes exit_ts (R9-01).
            a_eps, _ = engine_mod._build_variant(panel, legal_sigs, vid)
            b_eps, _ = engine_mod._build_variant(leaky_panel, leaky_sigs, vid)
        else:
            a_eps, _ = engine_mod.select_layer_from_l0(l0_eps, sig_by_key, panel, vid)
            b_eps, _ = engine_mod.select_layer_from_l0(l0_eps_k, sig_by_key_k, leaky_panel, vid)
        ka, kb = _episode_keys(a_eps), _episode_keys(b_eps)
        d = len(ka ^ kb)
        gates = VARIANT_GATE_MAP.get(vid, ())
        gates_changed = any(per_array.get(g, {}).get("changed_rows", 0) > 0 for g in gates)
        required = bool(
            vid in THRESHOLD_VARIANTS
            and gates_changed
            and vid not in CLIP_INSENSITIVE_VARIANTS
        )
        per_variant[vid] = {
            "legal_episodes": len(ka),
            "leaky_episodes": len(kb),
            "symmetric_difference": d,
            "gate_arrays": list(gates),
            "gates_changed": bool(gates_changed),
            "required_nonzero": required,
            "clip_insensitive": bool(vid in CLIP_INSENSITIVE_VARIANTS),
        }
        changed_sel += d
        legal_n += len(ka)
        leaky_n += len(kb)

    # every threshold variant whose gate array the shift actually changed must show a
    # non-zero episode difference — not only the pooled sum (R9-01)
    per_variant_ok = all(
        (not info["required_nonzero"]) or info["symmetric_difference"] > 0
        for info in per_variant.values()
    )
    hard = bool(exact and changed_state > 0 and changed_sel > 0 and per_variant_ok)
    return {
        "shift_is_exact_one_row": exact,
        "changed_state_rows": changed_state,
        "changed_selection_episodes": changed_sel,
        "legal_episode_count": legal_n,
        "leaky_episode_count": leaky_n,
        "per_state_array": per_array,
        "per_variant": per_variant,
        "per_variant_required_nonzero_held": per_variant_ok,
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

    Clauses 3 and 4 are derived from TWO calls to ``resolve_target_trail_time`` under adverse
    and favourable precedence — never from arithmetic on a constructed pair (R9-02).
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

    # ---- twin (b): favourable vs adverse precedence via the real exit resolver
    both_ids = []
    fav_ids = []
    fav_prices = []
    price_identical = 0
    ts = m1["ts"]
    active_hold_ns_default = int(1.0 * 3600 * NS)
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
        # locate a both-reachable bar (construction of the diagnostic population only)
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
        # resolve the SAME target+trail pair under both precedence settings (R9-02).
        # Anchor the scan so the first M1 bar considered is the both-reachable bar itself —
        # otherwise an earlier single-barrier hit can exit both twins identically and clauses
        # 3/4 never exercise the both-reachable branch they exist to prove.
        hold_ns = int(float(ep.active_hold_hours) * 3600 * NS) if np.isfinite(
            getattr(ep, "active_hold_hours", np.nan)
        ) else active_hold_ns_default
        fill_idx_anchor = hit - 1 if hit > 0 else ep.fill_m1_idx
        fill_ts_anchor = int(ts[fill_idx_anchor]) if fill_idx_anchor >= 0 else ep.fill_ts
        adverse = resolve_target_trail_time(
            m1, panel.open, panel.slot_start,
            side=ep.side, entry_price=ep.fill_price,
            fill_ts=fill_ts_anchor, fill_m1_idx=fill_idx_anchor,
            active_hold_ns=hold_ns,
            target_price=ep.target_price, trail_width_price=trail_w,
            favourable_precedence=False,
        )
        favourable = resolve_target_trail_time(
            m1, panel.open, panel.slot_start,
            side=ep.side, entry_price=ep.fill_price,
            fill_ts=fill_ts_anchor, fill_m1_idx=fill_idx_anchor,
            active_hold_ns=hold_ns,
            target_price=ep.target_price, trail_width_price=trail_w,
            favourable_precedence=True,
        )
        if adverse is None or favourable is None:
            continue
        adverse_px = float(adverse.exit_price)
        favourable_px = float(favourable.exit_price)
        # clause 3 population: bars where the two resolvers disagree on fill price or reason
        if (
            adverse.reason != favourable.reason
            or abs(adverse_px - favourable_px) > 1e-12 * max(1.0, ep.fill_price)
        ):
            fav_ids.append(int(ts[hit]))
        fav_prices.append({
            "m1_ts": int(ts[hit]),
            "decision_end_ns": int(ep.decision_end_ns),
            "side": int(ep.side),
            "emitted_exit_price": adverse_px,
            "favourable_exit_price": favourable_px,
            "emitted_exit_reason": str(adverse.reason),
            "favourable_exit_reason": str(favourable.reason),
            "emitted_r_bps": signed_r_bps(ep.side, ep.fill_price, adverse_px),
            "favourable_r_bps": signed_r_bps(ep.side, ep.fill_price, favourable_px),
            # the arm's own (target-only) exit for disclosure — not used by any clause
            "arm_exit_price": float(ep.exit_price),
            "arm_exit_reason": str(ep.exit_reason),
        })

    # clause 4: favourable twin is mechanically no worse than adverse, from resolver outputs
    price_ok = True
    for row in fav_prices:
        if row["side"] > 0 and row["favourable_exit_price"] < row["emitted_exit_price"] - 1e-12:
            price_ok = False
        if row["side"] < 0 and row["favourable_exit_price"] > row["emitted_exit_price"] + 1e-12:
            price_ok = False

    n_clock, n_both, n_fav = len(clock_diff_ids), len(both_ids), len(fav_ids)
    # clause 3: favourable-diff count equals both-reachable only when every both-reachable bar
    # actually produces distinct resolver outputs; that is measured, not constructed
    hard = bool(
        n_clock > 0
        and n_both > 0
        and n_fav == n_both
        and price_ok
        and fav_prices
    )
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
        "resolver_used": "resolve_target_trail_time",
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
