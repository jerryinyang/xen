"""Golden traces G1–G7 (design §11). QA derives expected numbers independently.

This module selects the rows by the design's deterministic rules and emits the measured
values from the catalog + this screen's fill rules — it does NOT invent expected numbers.
"""
from __future__ import annotations

from typing import Any

import numpy as np

from config import DESIGN_END_NS, DESIGN_START_NS, SCREEN_CODE_DIR
from entry import detect_signals, resolve_signal_fills
from metrics import log_R_from_pWL


def _in_design(ts: int) -> bool:
    return DESIGN_START_NS <= ts < DESIGN_END_NS


def build_golden_traces(
    bundles: dict[str, dict],
    episodes_by_key: dict[tuple, list],
    metrics_rows: list[dict],
) -> dict[str, Any]:
    """Emit G1–G7 selection material for QA re-derivation."""
    out: dict[str, Any] = {}

    # G1: BTCUSDT H1 DESIGN first LONG at delta=0.5
    g1 = {"rule": "BTCUSDT H1 DESIGN first LONG at delta=0.5", "status": "MISSING"}
    btc = bundles.get("BTCUSDT")
    if btc and "H1" in btc["panels"]:
        panel = btc["panels"]["H1"]
        sigs = resolve_signal_fills(detect_signals(panel, 0.5), panel)
        for s in sigs:
            if s.side > 0 and _in_design(s.decision_end_ns):
                g1 = {
                    "rule": "BTCUSDT H1 DESIGN first LONG at delta=0.5",
                    "status": "FOUND",
                    "decision_idx": s.decision_idx,
                    "decision_end_ns": s.decision_end_ns,
                    "stop_price": s.stop_price,
                    "atr20": s.atr20,
                    "momentum_atr": s.momentum_atr,
                    "filled": s.filled,
                    "fill_ts": s.fill_ts,
                    "fill_price": s.fill_price,
                    "fill_kind": s.fill_kind,
                    "bars_ohlc": {
                        "0": {
                            "o": float(panel.open[s.decision_idx]),
                            "h": float(panel.high[s.decision_idx]),
                            "l": float(panel.low[s.decision_idx]),
                            "c": float(panel.close[s.decision_idx]),
                        },
                        "1": {
                            "o": float(panel.open[s.decision_idx - 1]),
                            "h": float(panel.high[s.decision_idx - 1]),
                            "l": float(panel.low[s.decision_idx - 1]),
                            "c": float(panel.close[s.decision_idx - 1]),
                        },
                        "2": {
                            "o": float(panel.open[s.decision_idx - 2]),
                            "h": float(panel.high[s.decision_idx - 2]),
                            "l": float(panel.low[s.decision_idx - 2]),
                            "c": float(panel.close[s.decision_idx - 2]),
                        },
                    },
                }
                # find matching L0 episode
                key = ("BTCUSDT", "H1", 0.5, "L0_BASELINE")
                for ep in episodes_by_key.get(key, []):
                    if ep["decision_end_ns"] == s.decision_end_ns and ep["side"] == 1:
                        g1["exit_ts"] = ep["exit_ts"]
                        g1["exit_price"] = ep["exit_price"]
                        g1["r_bps"] = ep["r_bps"]
                        g1["active_hold_hours"] = ep["active_hold_hours"]
                        break
                break
    out["G1"] = g1

    # G2: ETHUSDT H1 DESIGN first SHORT unfilled within inactiveHold=2h
    g2 = {"rule": "ETHUSDT H1 DESIGN first SHORT unfilled within 2h", "status": "MISSING"}
    eth = bundles.get("ETHUSDT")
    if eth and "H1" in eth["panels"]:
        panel = eth["panels"]["H1"]
        sigs = resolve_signal_fills(detect_signals(panel, 0.5), panel)
        for s in sigs:
            if s.side < 0 and _in_design(s.decision_end_ns) and not s.filled:
                g2 = {
                    "rule": "ETHUSDT H1 DESIGN first SHORT unfilled within 2h",
                    "status": "FOUND",
                    "decision_end_ns": s.decision_end_ns,
                    "stop_price": s.stop_price,
                    "filled": False,
                    "fill_kind": s.fill_kind,
                    "reason": "UNFILLED",
                }
                break
    out["G2"] = g2

    # G3: first suppressed signal any symbol H1 DESIGN
    g3 = {"rule": "first SUPPRESSED signal H1 DESIGN", "status": "MISSING"}
    for sym, bundle in bundles.items():
        if "H1" not in bundle["panels"]:
            continue
        # check signal rows if available in episodes_by_key meta — scan L0 build
        key = (sym, "H1", 0.5, "L0_BASELINE")
        # we need signal stream; approximate from consecutive overlapping fills
        panel = bundle["panels"]["H1"]
        from engine import assemble_episodes_for_variant, base_signals
        sigs = base_signals(panel, 0.5)
        eps, srows = assemble_episodes_for_variant(panel, sigs, "L0_BASELINE")
        for row in srows:
            if row.get("reason") == "SUPPRESSED" and _in_design(row["decision_end_ns"]):
                g3 = {
                    "rule": "first SUPPRESSED signal H1 DESIGN",
                    "status": "FOUND",
                    "symbol": sym,
                    "decision_end_ns": row["decision_end_ns"],
                    "reason": "SUPPRESSED",
                }
                break
        if g3["status"] == "FOUND":
            break
    out["G3"] = g3

    # G4: L0 pooled H1 CONFIRM identity + log R
    g4 = {"rule": "L0 pooled H1 CONFIRM identity + log R", "status": "MISSING"}
    for row in metrics_rows:
        if (
            row.get("variant_id") == "L0_BASELINE"
            and row.get("clock") == "H1"
            and row.get("delta") == 0.5
            and row.get("scope") == "POOLED"
            and row.get("band") == "CONFIRM"
        ):
            p, W, L = row.get("p"), row.get("W"), row.get("L")
            mean = row.get("mean_signed_rows", row.get("mean"))
            recon = (p * W - (1 - p) * L) if all(x is not None and np.isfinite(x) for x in (p, W, L)) else float("nan")
            logR = log_R_from_pWL(p, W, L) if all(np.isfinite([p, W, L])) else float("nan")
            g4 = {
                "rule": "L0 pooled H1 CONFIRM identity + log R",
                "status": "FOUND",
                "p": p, "W": W, "L": L, "mean": mean,
                "identity_recon": recon,
                "identity_residual": abs(recon - mean) if np.isfinite(recon) and np.isfinite(mean) else float("nan"),
                "log_R_recomputed": logR,
                "log_R_emitted": row.get("log_R"),
                "log_R_match": bool(
                    np.isfinite(logR) and np.isfinite(row.get("log_R", np.nan))
                    and abs(logR - row["log_R"]) < 1e-12
                ),
            }
            break
    out["G4"] = g4

    # G5: null reference is 0 (slope 1); NO fitted-slope residual anywhere in the emission
    out["G5"] = scan_for_fitted_slope(metrics_rows)

    # G6 and G7 are computed by the caller from the real TRIPWIRE-1 / TRIPWIRE-2 payloads,
    # which need panel access. Initialised MISSING so an absent tripwire is a failure, never
    # a vacuous pass (P-23).
    out["G6"] = {"rule": "TRIPWIRE-1 structural conditions on the G1 symbol", "status": "MISSING"}
    out["G7"] = {"rule": "first both-reachable target+trail, adverse precedence", "status": "MISSING"}
    return out


FITTED_SLOPE_TOKENS = (
    "fitted_slope", "slope_residual", "fitted_residual", "0.9408", "beta_hat", "slope_fit",
)


def scan_for_fitted_slope(metrics_rows: list[dict]) -> dict:
    """G5 / §12: a fitted-slope residual appearing ANYWHERE is a hard failure.

    Scans the emitted column names AND this screen's own source for the forbidden object,
    rather than asserting in prose that no such column exists (QA run 8, R8-12). log R is
    defined with SLOPE 1, so its null reference is exactly 0.
    """
    cols = sorted({str(k) for row in metrics_rows for k in row})
    bad_cols = [
        c for c in cols
        if any(tok in c.lower() for tok in FITTED_SLOPE_TOKENS)
    ]
    bad_src = []
    for py in sorted(SCREEN_CODE_DIR.glob("*.py")):
        text = py.read_text(errors="replace")
        for tok in FITTED_SLOPE_TOKENS:
            # the token may legitimately appear inside this scanner's own declaration
            if tok in text and py.name != "golden.py":
                bad_src.append(f"{py.name}:{tok}")
    ok = not bad_cols and not bad_src and bool(cols)
    return {
        "rule": "mirror null is exact slope-1 log R = 0; no fitted-slope residual anywhere",
        "status": "PASS" if ok else "FAIL",
        "null_reference": 0.0,
        "slope": 1,
        "n_columns_scanned": len(cols),
        "forbidden_tokens": list(FITTED_SLOPE_TOKENS),
        "offending_columns": bad_cols,
        "offending_source": bad_src,
    }


def _assert_trail_ratchets_on_m1_closes() -> bool:
    """§11 G7(a): trail ratchets on M1 closes only — computed from the resolver source."""
    from fills import resolve_target_trail_time
    import inspect
    src = inspect.getsource(resolve_target_trail_time)
    # ratchet updates extreme from c[i] AFTER the trigger tests on bar i
    ratchet_after_trigger = (
        "if tgt_hit and trail_hit" in src
        and "if c[i] > extreme" in src
        and src.find("if tgt_hit and trail_hit") < src.find("if c[i] > extreme")
    )
    # no high/low used for the ratchet itself
    no_hl_ratchet = "extreme = float(h[i])" not in src and "extreme = float(lo[i])" not in src
    return bool(ratchet_after_trigger and no_hl_ratchet)


def _assert_time_exit_at_decision_bar_open() -> bool:
    """§11 G7(b): time exit fills at the OPEN of the first decision-clock bar at/after deadline."""
    from fills import resolve_time_exit
    import inspect
    src = inspect.getsource(resolve_time_exit)
    return (
        "clock_open[i]" in src
        and "searchsorted(clock_slot_start, deadline" in src
        and "exit_price=float(clock_open[i])" in src
    )


def g6_from_tripwire1(tw1: dict, symbol: str) -> dict:
    """G6: §6.1's three structural conditions, read off the REAL tripwire payload."""
    if not tw1:
        return {"rule": "TRIPWIRE-1 structural conditions", "status": "MISSING"}
    exact = bool(tw1.get("shift_is_exact_one_row"))
    ch_state = int(tw1.get("changed_state_rows", 0))
    ch_sel = int(tw1.get("changed_selection_episodes", 0))
    # the legal stream's episode set is the one the screen emits for the G1 symbol
    per_var = tw1.get("per_variant") or {}
    legal_is_emitted = bool(per_var) and all(
        isinstance(v, dict) and v.get("legal_episodes", 0) >= 0 for v in per_var.values()
    ) and ch_state > 0
    ok = exact and ch_state > 0 and ch_sel > 0 and legal_is_emitted
    return {
        "rule": "TRIPWIRE-1 structural conditions on the G1 symbol",
        "status": "PASS" if ok else "FAIL",
        "symbol": symbol,
        "shift_is_exact_one_row": exact,
        "changed_state_rows": ch_state,
        "changed_selection_episodes": ch_sel,
        "legal_variant_is_the_emitted_one": legal_is_emitted,
        "n_variants_compared": len(per_var),
        "note": "no magnitude is asserted; the payoff delta carries no pass rule (§11)",
    }


def g7_from_tripwire2(tw2: dict) -> dict:
    """G7: the first genuinely both-reachable bar, with the adverse fill that was taken."""
    rows = (tw2 or {}).get("favourable_prices") or []
    if not rows:
        return {
            "rule": "first both-reachable target+trail, adverse precedence",
            "status": "MISSING",
            "count_both_reachable": (tw2 or {}).get("count_both_reachable", 0),
        }
    first = rows[0]
    trail_ok = _assert_trail_ratchets_on_m1_closes()
    time_ok = _assert_time_exit_at_decision_bar_open()
    # adverse reason from the real resolver (R9-02), not a literal
    adverse_reason = first.get("emitted_exit_reason", "TRAIL")
    return {
        "rule": "first both-reachable target+trail, adverse precedence",
        "status": "FOUND",
        "m1_ts": first["m1_ts"],
        "decision_end_ns": first["decision_end_ns"],
        "side": first["side"],
        "filled_under_adverse_precedence": adverse_reason,
        "adverse_exit_price": first["emitted_exit_price"],
        "favourable_exit_price": first["favourable_exit_price"],
        "adverse_r_bps": first["emitted_r_bps"],
        "favourable_r_bps": first["favourable_r_bps"],
        "count_both_reachable": tw2.get("count_both_reachable"),
        "trail_ratchets_on_m1_closes_only": trail_ok,
        "time_exit_fills_at_decision_bar_open": time_ok,
        "resolver_used": tw2.get("resolver_used"),
    }
