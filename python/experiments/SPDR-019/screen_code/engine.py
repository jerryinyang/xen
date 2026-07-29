"""Episode construction for all 33 phase-(a) variants (design §4)."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np

from config import (
    E_RUN_CLIP,
    H_MOD_CLIP,
    H_MOD_DIVISOR,
    L0_ACTIVE_HOLD_HOURS,
    L0_INACTIVE_HOLD_HOURS,
    L4_HOLD_HOURS,
    L4_TARGET_A,
    L4_TRAIL_B,
    MOD_HOLD_MIN_PRIOR_TRANS,
    NS,
    SIZE_CLIP,
    TIME_EXIT_VARIANTS,
)
from entry import Signal, detect_signals, resolve_signal_fills
from fills import (
    bps_to_price_width,
    mfe_bps,
    resolve_target_trail_time,
    signed_r_bps,
)
from panel import SymbolPanel


@dataclass
class Episode:
    symbol: str
    clock: str
    delta: float
    variant_id: str
    side: int
    decision_idx: int
    decision_end_ns: int
    signal_ts: int  # == decision_end_ns
    stop_price: float
    fill_ts: int
    fill_price: float
    fill_kind: str
    fill_m1_idx: int
    exit_ts: int
    exit_price: float
    exit_reason: str
    r_bps: float
    active_hold_hours: float
    weight: float  # sizing; 1.0 elsewhere
    s_hat_bps: float
    s_hat_decile: float
    s_hat_rank: float
    abs_r_decision_bps: float
    abs_r_decile: float
    atr20: float
    # exit-matched side-derangement material (design §6 EXIT-MATCHING, §12 EXIT-MATCHED NULLS):
    # r under the SAME entry fill with the position's side flipped, with the barrier levels and
    # the exit RE-RESOLVED from M1 under this arm's own exit rule.
    r_bps_side_flipped: float = float("nan")
    exit_matched_method: str = ""  # TIME_EXIT_NEGATION | TARGET_TRAIL_RERESOLVE
    mfe_bps: float = float("nan")  # κ denominator (§5), disclosure diagnostic
    target_price: float = float("nan")
    trail_width_bps: float = float("nan")
    band: str = "TRAIN"
    extra: dict[str, Any] = field(default_factory=dict)


def _band_of(ts: int) -> str:
    from config import DESIGN_END_NS, DESIGN_START_NS, TRAIN_END_NS
    if DESIGN_START_NS <= ts < DESIGN_END_NS:
        return "DESIGN"
    if DESIGN_END_NS <= ts < TRAIN_END_NS:
        return "CONFIRM"
    return "OUT"


def _horizon_scale_bps(s_hat_bps: float, h_hours: float) -> float:
    """ŝ(t,h) = ŝ_H1(t) * sqrt(h_hours) (design §4.2)."""
    if not np.isfinite(s_hat_bps) or h_hours <= 0:
        return float("nan")
    return float(s_hat_bps * np.sqrt(h_hours))


def _parse_l4(variant_id: str) -> dict[str, Any]:
    """Parse L4 variant into device parameters."""
    if variant_id.startswith("L4_TARGET_A"):
        # L4_TARGET_A{1,2,3}_{UNMOD,MOD}
        rest = variant_id[len("L4_TARGET_A"):]
        a = int(rest[0])
        mod = rest.endswith("_MOD")
        return {"device": "target", "a": a, "mod": mod, "h_hours": L0_ACTIVE_HOLD_HOURS}
    if variant_id.startswith("L4_TRAIL_B"):
        rest = variant_id[len("L4_TRAIL_B"):]
        b = int(rest[0])
        mod = rest.endswith("_MOD")
        return {"device": "trail", "b": b, "mod": mod, "h_hours": L0_ACTIVE_HOLD_HOURS}
    if variant_id.startswith("L4_HOLD_"):
        # L4_HOLD_{1,4,12,20}H_{UNMOD,MOD}
        body = variant_id[len("L4_HOLD_"):]
        h_str, mode = body.split("H_", 1)
        h = float(h_str)
        mod = mode == "MOD"
        return {"device": "hold", "h_hours": h, "mod": mod}
    if variant_id.startswith("L4_SIZE_"):
        mod = variant_id.endswith("_MOD")
        return {"device": "size", "mod": mod, "h_hours": L0_ACTIVE_HOLD_HOURS}
    raise KeyError(variant_id)


def base_signals(panel: SymbolPanel, delta: float) -> list[Signal]:
    """Detect + M1-resolve entry fills. Suppression is variant-specific."""
    sigs = detect_signals(panel, delta)
    return resolve_signal_fills(sigs, panel, inactive_hold_hours=L0_INACTIVE_HOLD_HOURS)


def _select_mask(sig: Signal, variant_id: str, panel: SymbolPanel) -> tuple[bool, str]:
    """Whether a filled signal is eligible for this variant's population."""
    if variant_id == "L0_BASELINE":
        return True, "OK"
    if variant_id == "L1_SHAT_DECILE_GE5":
        if not np.isfinite(sig.s_hat_decile):
            return False, "L1_WARMUP"
        return sig.s_hat_decile >= 5, "L1_DECILE"
    if variant_id == "L1_SHAT_DECILE_GE7":
        if not np.isfinite(sig.s_hat_decile):
            return False, "L1_WARMUP"
        return sig.s_hat_decile >= 7, "L1_DECILE"
    if variant_id == "L1_SHAT_DECILE_GE9":
        if not np.isfinite(sig.s_hat_decile):
            return False, "L1_WARMUP"
        return sig.s_hat_decile >= 9, "L1_DECILE"
    if variant_id == "L1_SHAT_RANK_CONTINUOUS":
        if not np.isfinite(sig.s_hat_rank):
            return False, "L1_WARMUP"
        return True, "OK"
    if variant_id == "L2_SHOCK_HMM":
        i = sig.decision_idx
        v = panel.s_hmm_rv[i] if panel.s_hmm_rv.size else np.nan
        if not np.isfinite(v) or v < 0:
            return False, "HMM_NO_STATE"
        return int(v) == 1, "HMM_LOW"
    if variant_id == "L2_LEVEL_RMARKOV_K4":
        i = sig.decision_idx
        p = panel.p_rmarkov_k4[i] if panel.p_rmarkov_k4.size else np.nan
        if not np.isfinite(p):
            return False, "RMARKOV_K4_NA"
        return p >= 0.5, "RMARKOV_K4_LOW"
    if variant_id == "L2_LEVEL_RMARKOV_K12":
        i = sig.decision_idx
        p = panel.p_rmarkov_k12[i] if panel.p_rmarkov_k12.size else np.nan
        if not np.isfinite(p):
            return False, "RMARKOV_K12_NA"
        return p >= 0.5, "RMARKOV_K12_LOW"
    if variant_id == "L2_JOINT_HMM_HIGH_AND_K12_HIGH":
        i = sig.decision_idx
        v = panel.s_hmm_rv[i] if panel.s_hmm_rv.size else np.nan
        p = panel.p_rmarkov_k12[i] if panel.p_rmarkov_k12.size else np.nan
        if not np.isfinite(v) or v < 0 or not np.isfinite(p):
            return False, "JOINT_NA"
        return (int(v) == 1) and (p >= 0.5), "JOINT_OFF"
    if variant_id == "L3_TGTCUR_FIRES":
        i = sig.decision_idx
        v = panel.tgtcur_fires[i] if panel.tgtcur_fires.size else np.nan
        if not np.isfinite(v):
            return False, "TGTCUR_NA"
        return int(v) == 1, "TGTCUR_OFF"
    if variant_id == "L3_TGTCUR_DOES_NOT_FIRE":
        i = sig.decision_idx
        v = panel.tgtcur_fires[i] if panel.tgtcur_fires.size else np.nan
        if not np.isfinite(v):
            return False, "TGTCUR_NA"
        return int(v) == 0, "TGTCUR_ON"
    if variant_id == "L3_TGTMED5_CO_REPORT":
        i = sig.decision_idx
        v = panel.tgtmed5_fires[i] if panel.tgtmed5_fires.size else np.nan
        if not np.isfinite(v):
            return False, "TGTMED5_NA"
        return int(v) == 1, "TGTMED5_OFF"
    # L4 variants: all L0 filled signals (device changes exit, not entry selection)
    if variant_id.startswith("L4_"):
        if variant_id.endswith("_MOD") and "HOLD" in variant_id:
            i = sig.decision_idx
            npr = panel.n_prior_trans[i] if panel.n_prior_trans.size else 0
            if not np.isfinite(npr) or npr < MOD_HOLD_MIN_PRIOR_TRANS:
                return False, "MOD_HOLD_WARMUP"
        return True, "OK"
    return False, "UNKNOWN_VARIANT"


def _active_hold_hours(sig: Signal, variant_id: str, panel: SymbolPanel, meta: dict) -> float:
    if not variant_id.startswith("L4_"):
        return L0_ACTIVE_HOLD_HOURS
    if meta["device"] == "hold":
        h = float(meta["h_hours"])
        if meta["mod"]:
            i = sig.decision_idx
            p_stay = panel.p_stay[i] if panel.p_stay.size else np.nan
            if not np.isfinite(p_stay) or p_stay <= 0 or p_stay >= 1:
                return float("nan")
            e_run = float(np.clip(p_stay / (1.0 - p_stay), E_RUN_CLIP[0], E_RUN_CLIP[1]))
            return float(np.clip(h * e_run / H_MOD_DIVISOR, H_MOD_CLIP[0], H_MOD_CLIP[1]))
        return h
    return float(meta.get("h_hours", L0_ACTIVE_HOLD_HOURS))


def _exit_params(
    sig: Signal, variant_id: str, panel: SymbolPanel, meta: dict, h_hours: float
) -> tuple[float | None, float | None, float]:
    """Return (target_WIDTH_price, trail_width_price, weight).

    The target is returned as a side-free absolute price DISTANCE from the entry fill; the
    caller applies the side. That is what lets the exit-matched side derangement (§6) rebuild
    the flipped-side barrier from the same width rather than re-deriving it.
    """
    weight = 1.0
    if not variant_id.startswith("L4_"):
        return None, None, weight

    s_hat = sig.s_hat_bps
    s_uncond = panel.s_hat_uncond
    if meta["device"] == "target":
        a = meta["a"]
        if meta["mod"]:
            w_bps = a * _horizon_scale_bps(s_hat, h_hours)
        else:
            w_bps = a * _horizon_scale_bps(s_uncond, h_hours)
        if not np.isfinite(w_bps):
            return None, None, weight
        return bps_to_price_width(sig.fill_price, w_bps), None, weight
    if meta["device"] == "trail":
        b = meta["b"]
        if meta["mod"]:
            w_bps = b * _horizon_scale_bps(s_hat, h_hours)
        else:
            w_bps = b * _horizon_scale_bps(s_uncond, h_hours)
        if not np.isfinite(w_bps):
            return None, None, weight
        return None, bps_to_price_width(sig.fill_price, w_bps), weight
    if meta["device"] == "size":
        if meta["mod"]:
            if not (np.isfinite(s_hat) and s_hat > 0 and np.isfinite(s_uncond) and s_uncond > 0):
                return None, None, float("nan")
            w = s_uncond / s_hat
            weight = float(np.clip(w, SIZE_CLIP[0], SIZE_CLIP[1]))
        return None, None, weight
    # hold: time only
    return None, None, weight


def _resolve_exit(
    panel: SymbolPanel,
    sig: Signal,
    *,
    side: int,
    active_ns: int,
    tgt_width: float | None,
    trail_w: float | None,
    favourable_precedence: bool = False,
):
    """Resolve one exit at the frozen entry fill, for an arbitrary position side."""
    tgt = None
    if tgt_width is not None:
        tgt = sig.fill_price + side * tgt_width
    return resolve_target_trail_time(
        panel.m1, panel.open, panel.slot_start,
        side=side, entry_price=sig.fill_price,
        fill_ts=sig.fill_ts, fill_m1_idx=sig.fill_m1_idx,
        active_hold_ns=active_ns, target_price=tgt, trail_width_price=trail_w,
        favourable_precedence=favourable_precedence,
    )


def _episode_from_signal(
    sig: Signal,
    variant_id: str,
    panel: SymbolPanel,
    meta: dict,
    h_hours: float,
    tgt: float | None,
    trail_w: float | None,
    weight: float,
    exit_ts: int,
    exit_price: float,
    exit_reason: str,
    r: float,
    r_flip: float,
    exit_matched_method: str,
    mfe: float,
) -> Episode:
    return Episode(
        symbol=sig.symbol, clock=sig.clock, delta=sig.delta,
        variant_id=variant_id, side=sig.side,
        decision_idx=sig.decision_idx, decision_end_ns=sig.decision_end_ns,
        signal_ts=sig.decision_end_ns, stop_price=sig.stop_price,
        fill_ts=sig.fill_ts, fill_price=sig.fill_price, fill_kind=sig.fill_kind,
        fill_m1_idx=sig.fill_m1_idx,
        exit_ts=exit_ts, exit_price=exit_price, exit_reason=exit_reason,
        r_bps=r, active_hold_hours=h_hours, weight=weight,
        s_hat_bps=sig.s_hat_bps, s_hat_decile=sig.s_hat_decile,
        s_hat_rank=sig.s_hat_rank, abs_r_decision_bps=sig.abs_r_decision_bps,
        abs_r_decile=sig.abs_r_decile,
        atr20=sig.atr20,
        r_bps_side_flipped=r_flip,
        exit_matched_method=exit_matched_method,
        mfe_bps=mfe,
        target_price=float(tgt) if tgt is not None else float("nan"),
        trail_width_bps=(
            float(trail_w / sig.fill_price * 1e4)
            if trail_w is not None and sig.fill_price > 0 else float("nan")
        ),
        band=_band_of(sig.fill_ts),
    )


def _apply_exclusivity_in_fill_order(candidates: list[dict]) -> tuple[list[dict], list[dict]]:
    """§3: at most ONE open episode per symbol, decided in FILL order.

    ``fill_ts`` is not monotonic in ``decision_end_ns`` — a stop order may fill anywhere in the
    2-hour pending window — so resolving occupancy in decision order suppresses the wrong
    member of an overlapping pair (QA run 8, R8-17). Occupancy is a property of the interval
    ``[fill_ts, exit_ts)``, so it is decided on ``fill_ts``.
    """
    admitted: list[dict] = []
    suppressed: list[dict] = []
    open_until = -1
    for cand in sorted(
        candidates, key=lambda c: (c["fill_ts"], c["decision_end_ns"], -c["side"])
    ):
        if cand["fill_ts"] < open_until:
            suppressed.append(cand)
            continue
        admitted.append(cand)
        open_until = cand["exit_ts"]
    return admitted, suppressed


def build_l0_episodes(
    panel: SymbolPanel,
    signals: list[Signal],
) -> tuple[list[Episode], list[dict], dict[tuple, Signal]]:
    """L0 baseline: fixed 1h time exit; exclusivity on this exit window."""
    eps, rows = _build_variant(panel, signals, "L0_BASELINE", keep_signal=True)
    sig_by_key = {
        (e.symbol, e.decision_end_ns, e.side, e.delta, e.stop_price): s
        for e, s in ((e, e.extra["signal"]) for e in eps)
    }
    for e in eps:
        e.extra.pop("signal", None)
    return eps, rows, sig_by_key


def select_layer_from_l0(
    l0_episodes: list[Episode],
    sig_by_key: dict[tuple, Signal],
    panel: SymbolPanel,
    variant_id: str,
) -> tuple[list[Episode], list[dict]]:
    """L1–L3: strict subset of L0 episodes (design §4.1, §12 L1 FIXED-ENTRY SUBSET)."""
    episodes: list[Episode] = []
    rows: list[dict] = []
    for ep0 in l0_episodes:
        key = (ep0.symbol, ep0.decision_end_ns, ep0.side, ep0.delta, ep0.stop_price)
        sig = sig_by_key.get(key)
        if sig is None:
            continue
        ok, why = _select_mask(sig, variant_id, panel)
        row = {
            "symbol": ep0.symbol, "clock": ep0.clock, "delta": ep0.delta,
            "variant_id": variant_id, "side": ep0.side,
            "decision_end_ns": ep0.decision_end_ns, "stop_price": ep0.stop_price,
            "fill_ts": ep0.fill_ts, "fill_price": ep0.fill_price, "fill_kind": ep0.fill_kind,
            "filled": True, "suppressed": False, "eligible": ok,
            "ineligible_reason": "" if ok else why,
            "reason": "EPISODE" if ok else "INELIGIBLE",
            "band": ep0.band,
        }
        rows.append(row)
        if not ok:
            continue
        # same entry+exit as L0; only variant tag changes
        ep = Episode(**{**ep0.__dict__, "variant_id": variant_id, "extra": {}})
        episodes.append(ep)
    return episodes, rows


def _build_variant(
    panel: SymbolPanel,
    signals: list[Signal],
    variant_id: str,
    *,
    keep_signal: bool = False,
) -> tuple[list[Episode], list[dict]]:
    """L0 and every L4 device: frozen entry signals, device exit, exclusivity in fill order."""
    meta = _parse_l4(variant_id) if variant_id.startswith("L4_") else {}
    signal_rows: list[dict] = []
    candidates: list[dict] = []

    for sig in sorted(signals, key=lambda s: (s.decision_end_ns, -s.side)):
        row = {
            "symbol": sig.symbol, "clock": sig.clock, "delta": sig.delta,
            "variant_id": variant_id, "side": sig.side,
            "decision_end_ns": sig.decision_end_ns, "stop_price": sig.stop_price,
            "fill_ts": sig.fill_ts, "fill_price": sig.fill_price, "fill_kind": sig.fill_kind,
            "filled": sig.filled, "suppressed": False, "reason": sig.reason,
            "eligible": False, "ineligible_reason": "",
            # band from the fill where one exists, else from the decision close, so unfilled
            # and suppressed signals still land in a band and enter the fill-rate denominator
            "band": _band_of(sig.fill_ts if sig.filled else sig.decision_end_ns),
        }
        if not sig.filled or sig.fill_kind == "EXPIRED":
            row["reason"] = "UNFILLED"
            signal_rows.append(row)
            continue
        ok, why = _select_mask(sig, variant_id, panel)
        if not ok:
            row["ineligible_reason"] = why
            row["reason"] = "INELIGIBLE"
            signal_rows.append(row)
            continue
        row["eligible"] = True
        h_hours = _active_hold_hours(sig, variant_id, panel, meta)
        if not np.isfinite(h_hours):
            row["ineligible_reason"] = "HOLD_NA"
            row["reason"] = "INELIGIBLE"
            signal_rows.append(row)
            continue
        tgt_width, trail_w, weight = _exit_params(sig, variant_id, panel, meta, h_hours)
        if meta.get("device") in ("target", "trail"):
            if (meta["device"] == "target" and tgt_width is None) or (
                meta["device"] == "trail" and trail_w is None
            ):
                row["ineligible_reason"] = "EXIT_WIDTH_NA"
                row["reason"] = "INELIGIBLE"
                signal_rows.append(row)
                continue
        if not np.isfinite(weight):
            row["ineligible_reason"] = "SIZE_NA"
            row["reason"] = "INELIGIBLE"
            signal_rows.append(row)
            continue
        active_ns = int(h_hours * 3600 * NS)
        ex = _resolve_exit(
            panel, sig, side=sig.side, active_ns=active_ns,
            tgt_width=tgt_width, trail_w=trail_w,
        )
        if ex is None:
            row["reason"] = "NO_EXIT"
            signal_rows.append(row)
            continue
        r = signed_r_bps(sig.side, sig.fill_price, ex.exit_price)

        # exit-matched side-derangement material (§6 EXIT-MATCHING). On a time-exit arm no
        # side-dependent branch exists, so the flipped payoff is the negation of the same exit
        # and §12 asserts that equality; on a target/trail arm the barrier is rebuilt on the
        # flipped side and the exit is RE-RESOLVED from M1.
        if meta.get("device") in ("target", "trail"):
            ex_f = _resolve_exit(
                panel, sig, side=-sig.side, active_ns=active_ns,
                tgt_width=tgt_width, trail_w=trail_w,
            )
            r_flip = (
                signed_r_bps(-sig.side, sig.fill_price, ex_f.exit_price)
                if ex_f is not None else float("nan")
            )
            method = "TARGET_TRAIL_RERESOLVE"
        else:
            r_flip = signed_r_bps(-sig.side, sig.fill_price, ex.exit_price)
            method = "TIME_EXIT_NEGATION"

        if meta.get("device") == "size":
            r = r * weight
            r_flip = r_flip * weight
        tgt_price = (
            sig.fill_price + sig.side * tgt_width if tgt_width is not None else None
        )
        mfe = mfe_bps(
            panel.m1, side=sig.side, entry_price=sig.fill_price,
            fill_m1_idx=sig.fill_m1_idx, exit_ts=ex.exit_ts,
        )
        ep = _episode_from_signal(
            sig, variant_id, panel, meta, h_hours, tgt_price, trail_w, weight,
            ex.exit_ts, ex.exit_price, ex.reason, r, r_flip, method, mfe,
        )
        if keep_signal:
            ep.extra["signal"] = sig
        candidates.append({
            "episode": ep, "row": row, "fill_ts": sig.fill_ts,
            "exit_ts": ex.exit_ts, "decision_end_ns": sig.decision_end_ns, "side": sig.side,
            "r_bps": r,
        })
        signal_rows.append(row)

    admitted, suppressed = _apply_exclusivity_in_fill_order(candidates)
    for cand in suppressed:
        cand["row"]["suppressed"] = True
        cand["row"]["eligible"] = True
        cand["row"]["reason"] = "SUPPRESSED"
    episodes = []
    for cand in admitted:
        cand["row"]["reason"] = "EPISODE"
        cand["row"]["exit_ts"] = cand["exit_ts"]
        cand["row"]["r_bps"] = cand["r_bps"]
        episodes.append(cand["episode"])
    return episodes, signal_rows


def assemble_episodes_for_variant(
    panel: SymbolPanel,
    signals: list[Signal],
    variant_id: str,
    *,
    l0_cache: tuple[list[Episode], dict[tuple, Signal]] | None = None,
) -> tuple[list[Episode], list[dict]]:
    """Dispatch: L0 build, L1–L3 subset of L0, L4 device exits."""
    if variant_id == "L2_INTERACTION_HMM_X_K12":
        return [], []
    if variant_id == "L0_BASELINE":
        eps, rows, _ = build_l0_episodes(panel, signals)
        return eps, rows
    if variant_id.startswith("L4_"):
        return _build_variant(panel, signals, variant_id)
    # L1–L3
    if l0_cache is None:
        l0_eps, _, sig_by_key = build_l0_episodes(panel, signals)
    else:
        l0_eps, sig_by_key = l0_cache
    return select_layer_from_l0(l0_eps, sig_by_key, panel, variant_id)


def episode_to_row(ep: Episode) -> dict:
    d = asdict(ep)
    d.pop("extra", None)
    return d


def is_time_exit_variant(variant_id: str) -> bool:
    return variant_id in TIME_EXIT_VARIANTS
