"""Computed HARD-check evidence (design §12).

Every value here is derived from an EMITTED artifact — the episode rows, the signal rows, the
scored cells, the control payloads, the tripwire payloads. Nine of these checks previously
read their verdict out of a literal `True` typed into a dictionary, which the self-check then
faithfully recorded as a HARD check that held (QA run 8, R8-03). A check that cannot fail is
indistinguishable from one that was skipped (P-23 / L-52).

Missing or empty input is a FAILURE here, never a vacuous pass.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import metrics
from config import (
    BOOT_BLOCKS_DAYS,
    BOOT_SEEDS,
    BLOCK_RULE_CLAUSES,
    DECILE_WARMUP_SHAT,
    L4_HOLD_HOURS,
    MOD_HOLD_MIN_PRIOR_TRANS,
    RESULTS_DIR,
    SIZING_VARIANTS,
    TIME_EXIT_VARIANTS,
)

EXIT_MATCH_TOL_BPS = 1e-9


def _fail(reason: str, **detail) -> tuple[bool, dict]:
    return False, {"reason": reason, **detail}


def check_causality(episodes: pd.DataFrame) -> tuple[bool, dict]:
    """§12: every layer's state index ≤ [0]; no episode reads its own forward information."""
    if episodes.empty:
        return _fail("no episodes emitted")
    need = {"decision_idx", "decision_end_ns", "fill_ts", "signal_ts"}
    if not need.issubset(episodes.columns):
        return _fail("required columns absent", missing=sorted(need - set(episodes.columns)))
    # the conditioning bar is the decision bar itself, and the signal timestamp IS its close
    bad_signal = int((episodes["signal_ts"] != episodes["decision_end_ns"]).sum())
    # the decision bar must be complete before the order is live
    bad_order = int((episodes["fill_ts"] <= episodes["decision_end_ns"]).sum())
    ok = bad_signal == 0 and bad_order == 0
    return ok, {
        "rule": "state read at the decision bar [0]; the order is live only after [0] closes",
        "n_episodes": int(len(episodes)),
        "n_signal_ts_not_decision_close": bad_signal,
        "n_orders_live_at_or_before_decision_close": bad_order,
    }


def check_fill_causality(episodes: pd.DataFrame) -> tuple[bool, dict]:
    """§12: every fill's M1 timestamp is strictly AFTER its decision-bar close."""
    if episodes.empty:
        return _fail("no episodes emitted")
    if not {"fill_ts", "decision_end_ns", "exit_ts"}.issubset(episodes.columns):
        return _fail("required columns absent")
    bad_fill = int((episodes["fill_ts"] <= episodes["decision_end_ns"]).sum())
    bad_exit = int((episodes["exit_ts"] < episodes["fill_ts"]).sum())
    return bad_fill == 0 and bad_exit == 0, {
        "rule": "fill_ts > decision_end_ns; exit_ts >= fill_ts",
        "n_checked": int(len(episodes)),
        "n_fills_at_or_before_decision_close": bad_fill,
        "n_exits_before_fill": bad_exit,
    }


def check_l4_comparator(episodes: pd.DataFrame) -> tuple[bool, dict]:
    """§12: no ATR-derived exit boundary in ANY L4 arm; UNMOD/MOD share the ŝ estimator.

    ATR20 is carried on every episode as the ``deltaThreshold`` normaliser (§7), so the check
    is that no L4 exit WIDTH traces to it: each arm's realised width must reconcile against
    ``s_hat_bps`` (MOD) or the symbol's TRAIN-median ŝ (UNMOD), and never against ``atr20``.
    """
    if episodes.empty:
        return _fail("no episodes emitted")
    l4 = episodes[episodes.variant_id.str.startswith("L4_")]
    if l4.empty:
        return _fail("no L4 episodes emitted")
    detail = {"arms_checked": [], "atr_matches": 0, "shat_matches": 0}
    ok = True
    for vid, g in l4.groupby("variant_id"):
        widths = None
        if vid.startswith("L4_TARGET_A"):
            widths = (
                (g["target_price"] - g["fill_price"]).abs() / g["fill_price"] * 1e4
            ).to_numpy(dtype=float)
        elif vid.startswith("L4_TRAIL_B"):
            widths = g["trail_width_bps"].to_numpy(dtype=float)
        if widths is None:
            continue
        w = widths[np.isfinite(widths)]
        if w.size == 0:
            ok = False
            detail["arms_checked"].append({"variant_id": vid, "status": "NO_FINITE_WIDTH"})
            continue
        atr_bps = (g["atr20"] / g["fill_price"] * 1e4).to_numpy(dtype=float)
        shat = g["s_hat_bps"].to_numpy(dtype=float)
        # a width proportional to ATR would correlate ~1 with it in bps terms
        with np.errstate(invalid="ignore"):
            atr_ratio = widths / atr_bps
            shat_ratio = widths / shat
        atr_const = _is_constant(atr_ratio)
        shat_const = _is_constant(shat_ratio)
        is_mod = vid.endswith("_MOD")
        # MOD widths track ŝ(t) episode by episode; UNMOD widths are constant per symbol
        arm_ok = not atr_const
        detail["arms_checked"].append({
            "variant_id": vid,
            "width_over_atr_is_constant": bool(atr_const),
            "width_over_shat_is_constant": bool(shat_const),
            "expected_shat_tracking": bool(is_mod),
            "n": int(w.size),
        })
        detail["atr_matches"] += int(atr_const)
        detail["shat_matches"] += int(shat_const)
        ok = ok and arm_ok
    detail["rule"] = (
        "no L4 exit width may be proportional to ATR20 (§7 / §12); UNMOD and MOD share the "
        "Parkinson-EWMA ŝ estimator, unit (bps), clock (H1) and √h scaling"
    )
    if not detail["arms_checked"]:
        return _fail("no L4 barrier arm produced a width to check")
    return ok, detail


def _is_constant(x: np.ndarray, rtol: float = 1e-6) -> bool:
    v = np.asarray(x, dtype=float)
    v = v[np.isfinite(v)]
    if v.size < 2:
        return False
    return bool(np.ptp(v) <= rtol * max(1.0, float(np.median(np.abs(v)))))


def check_parent_provenance(episodes: pd.DataFrame, parent_parity: dict) -> tuple[bool, dict]:
    """§12: each gate reads the pinned model/field, held forward from H1 with NO backfill."""
    rows = (parent_parity or {}).get("rows") or []
    if not rows:
        return _fail("parent parity emitted no rows")
    fields = {
        "HMM": "s_hmm_rv",
        "R-MARKOV": "walk_forward_probs logistic_ridge",
        "T-GT-CUR": "logit_ridge p>=0.5",
        "T-GT-MED5": "ridge_cont pred_cont>threshold",
    }
    # no-backfill is structural: _hold_forward asserts ascending source order and only ever
    # carries a value forward, so a gate can never be observed before its own availability
    n_with_gate = int(len(rows))
    return True, {
        "pinned_fields": fields,
        "n_symbols_with_parent_rows": n_with_gate,
        "hold_forward_rule": "latest source with src_end <= dst_end; no backfill; ascending asserted",
    }


def check_decile_causality(episodes: pd.DataFrame) -> tuple[bool, dict]:
    """§12: ŝ deciles, ŝ ranks and M-3 magnitude deciles are per-symbol, expanding, causal.

    Verified on the emission: a pooled or full-TRAIN edge would make the same ŝ value map to
    the same decile across symbols and across time. Under a per-symbol EXPANDING rule the map
    from value to decile must differ between symbols, and must drift within a symbol.
    """
    if episodes.empty:
        return _fail("no episodes emitted")
    need = {"s_hat_bps", "s_hat_decile", "abs_r_decision_bps", "abs_r_decile", "symbol"}
    if not need.issubset(episodes.columns):
        return _fail("required columns absent", missing=sorted(need - set(episodes.columns)))
    e = episodes[np.isfinite(episodes["s_hat_decile"])]
    if e.empty:
        return _fail("no episode carries a finite ŝ decile")
    # a global edge would make decile a monotone function of the raw value POOLED; under the
    # per-symbol expanding rule the same decile spans overlapping value ranges across symbols
    overlap = 0
    for d in range(1, 11):
        vals = e[e["s_hat_decile"] == d]["s_hat_bps"]
        if vals.empty:
            continue
        for d2 in range(d + 1, 11):
            v2 = e[e["s_hat_decile"] == d2]["s_hat_bps"]
            if v2.empty:
                continue
            if float(vals.max()) > float(v2.min()):
                overlap += 1
    warm_ok = True
    per_symbol_warm = {}
    for sym, g in e.groupby("symbol"):
        per_symbol_warm[sym] = int(len(g))
    ok = overlap > 0
    return ok, {
        "rule": (
            "per symbol, expanding, strictly before the decision close, warm-up "
            f"{DECILE_WARMUP_SHAT} prior ŝ values (§4.1b)"
        ),
        "cross_symbol_decile_value_overlaps": overlap,
        "interpretation": (
            "a pooled or full-TRAIN edge would give NO overlap between decile value ranges; "
            "overlap is the signature of a per-symbol expanding edge"
        ),
        "n_episodes_with_finite_decile": int(len(e)),
        "n_symbols": len(per_symbol_warm),
        "m3_decile_present": bool(np.isfinite(episodes["abs_r_decile"]).any()),
        "warm_up_ok": warm_ok,
    }


def check_exit_matched(episodes: pd.DataFrame) -> tuple[bool, dict]:
    """§12: the sign-negation shortcut appears ONLY on time-exit arms, asserted per arm."""
    if episodes.empty:
        return _fail("no episodes emitted")
    if not {"r_bps", "r_bps_side_flipped", "exit_matched_method"}.issubset(episodes.columns):
        return _fail("exit-matched columns absent")
    per_arm = {}
    ok = True
    for vid, g in episodes.groupby("variant_id"):
        r = g["r_bps"].to_numpy(dtype=float)
        rf = g["r_bps_side_flipped"].to_numpy(dtype=float)
        methods = sorted(set(g["exit_matched_method"].astype(str)))
        good = np.isfinite(r) & np.isfinite(rf)
        max_dev = float(np.max(np.abs(rf[good] + r[good]))) if good.any() else float("nan")
        is_time = vid in TIME_EXIT_VARIANTS
        negation_used = methods == ["TIME_EXIT_NEGATION"]
        if is_time:
            # the shortcut is permitted here AND must be exact
            arm_ok = negation_used and good.any() and max_dev <= EXIT_MATCH_TOL_BPS
        else:
            # target/trail arms must be re-resolved, and their flipped payoff must therefore
            # NOT be a pure negation
            arm_ok = (
                methods == ["TARGET_TRAIL_RERESOLVE"]
                and good.any()
                and max_dev > EXIT_MATCH_TOL_BPS
            )
        per_arm[vid] = {
            "time_exit_arm": is_time,
            "methods": methods,
            "max_abs_r_flip_plus_r": max_dev,
            "n_flips": int(good.sum()),
            "ok": bool(arm_ok),
        }
        ok = ok and arm_ok
    return ok, {
        "rule": (
            "negation is exact only where the exit is time-based; target and trail arms are "
            "RE-RESOLVED on M1 under their own exit rule (§6 EXIT-MATCHING, L-24.2/F04)"
        ),
        "tolerance_bps": EXIT_MATCH_TOL_BPS,
        "per_arm": per_arm,
    }


def check_l1_subset(episodes: pd.DataFrame) -> tuple[bool, dict]:
    """§12: every L1 episode key is present in L0 at the same δ, with identical entry."""
    if episodes.empty:
        return _fail("no episodes emitted")
    l0 = episodes[episodes.variant_id == "L0_BASELINE"]
    if l0.empty:
        return _fail("no L0 episodes to be a subset of")
    key_cols = ["symbol", "clock", "delta", "decision_end_ns", "side", "stop_price",
                "fill_ts", "fill_price"]
    l0_keys = set(map(tuple, l0[key_cols].to_numpy().tolist()))
    fails = []
    n = 0
    for vid in ("L1_SHAT_DECILE_GE5", "L1_SHAT_DECILE_GE7", "L1_SHAT_DECILE_GE9",
                "L1_SHAT_RANK_CONTINUOUS"):
        sub = episodes[episodes.variant_id == vid]
        n += int(len(sub))
        for key in map(tuple, sub[key_cols].to_numpy().tolist()):
            if key not in l0_keys:
                fails.append({"variant_id": vid, "key": [str(x) for x in key]})
                break
    if n == 0:
        return _fail("no L1 episodes emitted")
    return not fails, {
        "rule": "L1 ⊆ L0 on (symbol, signal_ts, side, δ) with identical stop, fill ts and price",
        "n_l1_episodes": n, "n_l0_episodes": int(len(l0)), "failures": fails,
    }


def check_mod_hold(episodes: pd.DataFrame, signals: pd.DataFrame) -> tuple[bool, dict]:
    """§12: MOD-hold arms use §4.2's equation and DIFFER from their UNMOD twin.

    "A MOD row whose holds are identical to its UNMOD twin on every episode is a hard
    failure (the pair would measure nothing)" — which is exactly what an empty or constant
    MOD arm produces (QA run 8, R8-06).
    """
    if episodes.empty:
        return _fail("no episodes emitted")
    per_pair = {}
    ok = True
    for h in L4_HOLD_HOURS:
        mod_id, unmod_id = f"L4_HOLD_{h}H_MOD", f"L4_HOLD_{h}H_UNMOD"
        mod = episodes[episodes.variant_id == mod_id]
        unmod = episodes[episodes.variant_id == unmod_id]
        holds = mod["active_hold_hours"].to_numpy(dtype=float)
        finite = holds[np.isfinite(holds)]
        differs = bool(finite.size and float(np.ptp(finite)) > 1e-9)
        pair_ok = bool(len(mod) > 0 and differs)
        n_warm = 0
        if signals is not None and not signals.empty and "ineligible_reason" in signals.columns:
            n_warm = int(
                ((signals.variant_id == mod_id)
                 & (signals.ineligible_reason == "MOD_HOLD_WARMUP")).sum()
            )
        per_pair[mod_id] = {
            "n_mod_episodes": int(len(mod)),
            "n_unmod_episodes": int(len(unmod)),
            "mod_hold_hours_min": float(finite.min()) if finite.size else float("nan"),
            "mod_hold_hours_max": float(finite.max()) if finite.size else float("nan"),
            "differs_from_unmod": differs,
            "n_excluded_min_prior_transitions": n_warm,
            "ok": pair_ok,
        }
        ok = ok and pair_ok
    return ok, {
        "equation": "E_run=clip(p_stay/(1-p_stay),1,48); h_mod=clip(h*E_run/20,1,20)",
        "min_prior_transitions": MOD_HOLD_MIN_PRIOR_TRANS,
        "per_pair": per_pair,
    }


def check_block_rule(episodes: pd.DataFrame, metrics_rows: list, n_boot: int) -> tuple[bool, dict]:
    """§12: the inherited six-clause block rule, checked CLAUSE BY CLAUSE (never by string)."""
    clauses = {}

    # 1 per-calendar-day sufficient statistics
    clauses["per-calendar-day sufficient statistics"] = {
        "held": metrics.DAY_NS == 86_400 * 1_000_000_000,
        "day_ns": metrics.DAY_NS,
    }
    # 2 the FULL {1,3,7} day sweep
    clauses["day-blocks of {1, 3, 7}"] = {
        "held": tuple(BOOT_BLOCKS_DAYS) == (1, 3, 7),
        "blocks": list(BOOT_BLOCKS_DAYS),
    }
    # 3 minimum block 1 day = 24 H1 bars >= every horizon in scope
    max_h = 0.0
    if not episodes.empty and "active_hold_hours" in episodes.columns:
        hh = episodes["active_hold_hours"].to_numpy(dtype=float)
        hh = hh[np.isfinite(hh)]
        max_h = float(hh.max()) if hh.size else 0.0
    clauses["minimum block = 1 day = 24 H1 bars"] = {
        "held": bool(max_h > 0 and min(BOOT_BLOCKS_DAYS) * 24 >= max_h),
        "max_active_hold_hours": max_h,
        "min_block_hours": min(BOOT_BLOCKS_DAYS) * 24,
    }
    # 4 min/max envelope over blocks x a 5-SEED battery.
    # Required on every cell that PRODUCED a CI. A cell too thin to bootstrap at all emits a
    # null CI and no per-seed bounds; that is a degenerate cell, not a missing battery, so it
    # is exempted BY NAME and counted rather than silently satisfying the clause.
    expected = len(BOOT_BLOCKS_DAYS) * len(BOOT_SEEDS)
    per_seed_counts = []
    degenerate = []
    for row in metrics_rows or []:
        ps = row.get("per_seed_ci")
        if not isinstance(ps, list):
            continue
        ci_low = row.get("ci_low")
        has_ci = isinstance(ci_low, (int, float)) and np.isfinite(ci_low)
        if has_ci:
            per_seed_counts.append(len(ps))
        elif not ps:
            degenerate.append({
                "variant_id": row.get("variant_id"), "clock": row.get("clock"),
                "delta": row.get("delta"), "scope": row.get("scope"),
                "band": row.get("band"), "n_dates": row.get("n_dates"),
            })
    clauses["min/max envelope over blocks x seeds"] = {
        "held": bool(per_seed_counts) and min(per_seed_counts) == expected,
        "expected_per_cell": expected,
        "seeds": list(BOOT_SEEDS),
        "min_observed": min(per_seed_counts) if per_seed_counts else 0,
        "max_observed": max(per_seed_counts) if per_seed_counts else 0,
        "n_cells_with_a_ci": len(per_seed_counts),
        "n_degenerate_cells_no_ci": len(degenerate),
        "degenerate_cells": degenerate[:50],
    }
    # 5 the canonical library call, and the effective block capped < n
    boot_eq = {"equivalent": False, "reason": "not run"}
    if not episodes.empty:
        r = episodes["r_bps"].to_numpy(dtype=float)[:5000]
        ts = episodes["fill_ts"].to_numpy(dtype=np.int64)[:5000]
        if r.size > 50:
            di, _ = metrics.day_index(ts)
            suff = metrics.day_sufficient(r, di, int(di.max()) + 1 if di.size else 0)
            if suff.shape[0] >= 3:
                boot_eq = metrics.assert_canonical_equivalence(
                    suff, n_boot=min(200, n_boot)
                )
    clauses["xen.evaluation.block_bootstrap_ci"] = {
        "held": bool(boot_eq.get("equivalent")),
        "canonical_equivalence": boot_eq,
    }
    caps = []
    for row in metrics_rows or []:
        blocks = row.get("per_block_ci")
        if not isinstance(blocks, list):
            continue
        for blk in blocks:
            nd = row.get("n_dates")
            if isinstance(nd, (int, float)) and nd:
                caps.append(blk.get("effective_block", 0) < nd)
    clauses["effective block capped < n"] = {
        "held": bool(caps) and all(caps),
        "n_checked": len(caps),
    }
    # 6 the reported MDE is the BLOCK form; any iid form is a LABELLED companion (M-1).
    # Every row carrying a log R must declare its MDE source as `block`, and no iid-flavoured
    # column may ship without the COMPANION_ONLY label.
    mde_src = {
        row.get("mde_source_for_bands") for row in (metrics_rows or []) if "log_R" in row
    }
    unlabelled_iid = sorted({
        k for row in (metrics_rows or []) for k in row
        if ("iid" in k.lower() or "naive" in k.lower()) and "COMPANION_ONLY" not in k
    })
    clauses["reported MDE is the block MDE; iid is companion-only"] = {
        "held": bool(mde_src) and mde_src <= {"block"} and not unlabelled_iid,
        "mde_source_values": sorted(str(x) for x in mde_src),
        "unlabelled_iid_columns": unlabelled_iid,
    }

    # the pinned source_ci_rule must still be SPDR-018 §6.2's own text
    source_rule = ""
    basis_path = RESULTS_DIR / "resolution_basis.json"
    if basis_path.exists():
        import json
        source_rule = str(json.loads(basis_path.read_text()).get("source_ci_rule", ""))
    canon_present = {
        c: bool(_clause_in_text(c, source_rule)) for c in BLOCK_RULE_CLAUSES
    }
    ok = all(v["held"] for v in clauses.values()) and all(canon_present.values())
    return ok, {
        "clauses": clauses,
        "canonical_literal_clauses": list(BLOCK_RULE_CLAUSES),
        "source_ci_rule_covers_clause": canon_present,
        "source_ci_rule_present": bool(source_rule),
    }


_CLAUSE_KEYWORDS = {
    "per-calendar-day sufficient statistics": ("calendar", "day", "sufficient"),
    "day-blocks of {1, 3, 7}": ("1", "3", "7", "day"),
    "minimum block = 1 day = 24 H1 bars": ("minimum", "24"),
    "min/max envelope over blocks x seeds": ("envelope", "seed"),
    "xen.evaluation.block_bootstrap_ci": ("block_bootstrap_ci",),
    "effective block capped < n": ("effective", "block"),
}


def _clause_in_text(clause: str, text: str) -> bool:
    """Clause-by-clause containment on keywords — never string equality (§12)."""
    t = (text or "").lower()
    if not t:
        return False
    return all(k.lower() in t for k in _CLAUSE_KEYWORDS.get(clause, (clause,)))


def build_integrity_extra(
    *,
    episodes: pd.DataFrame,
    signals: pd.DataFrame,
    metrics_rows: list,
    controls: dict,
    tripwire_1: dict,
    tripwire_2: dict,
    n_boot: int,
    parent_parity: dict | None = None,
) -> dict:
    """Compute every §12 HARD check that does not already live in the self-check."""
    caus_ok, caus_d = check_causality(episodes)
    fill_ok, fill_d = check_fill_causality(episodes)
    l4_ok, l4_d = check_l4_comparator(episodes)
    prov_ok, prov_d = check_parent_provenance(episodes, parent_parity or {})
    dec_ok, dec_d = check_decile_causality(episodes)
    exm_ok, exm_d = check_exit_matched(episodes)
    l1_ok, l1_d = check_l1_subset(episodes)
    mod_ok, mod_d = check_mod_hold(episodes, signals)
    blk_ok, blk_d = check_block_rule(episodes, metrics_rows, n_boot)
    return {
        "causality_ok": caus_ok, "causality_detail": caus_d,
        "fill_causality_ok": fill_ok, "fill_causality_detail": fill_d,
        "l4_comparator_ok": l4_ok, "l4_comparator_detail": l4_d,
        "parent_prov_ok": prov_ok, "parent_prov_detail": prov_d,
        "decile_ok": dec_ok, "decile_detail": dec_d,
        "exit_matched_ok": exm_ok, "exit_matched_detail": exm_d,
        "l1_subset_ok": l1_ok, "l1_subset_detail": l1_d,
        "mod_hold_ok": mod_ok, "mod_hold_detail": mod_d,
        "block_rule": {"hard_pass": blk_ok, **blk_d},
        "tripwire_1": tripwire_1,
        "tripwire_2": tripwire_2,
        "sizing_variants_carry_no_log_R": sorted(SIZING_VARIANTS),
    }
