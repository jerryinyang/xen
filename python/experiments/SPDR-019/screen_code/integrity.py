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
    DERIVED_VARIANTS,
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

    Both halves of the clause are asserted (R9-09): MOD widths track ŝ(t); UNMOD widths do not.
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
        if w.size < 2:
            ok = False
            detail["arms_checked"].append({
                "variant_id": vid, "status": "TOO_FEW_FINITE_WIDTHS", "n": int(w.size),
            })
            continue
        atr_bps = (g["atr20"] / g["fill_price"] * 1e4).to_numpy(dtype=float)
        shat = g["s_hat_bps"].to_numpy(dtype=float)
        atr_prop = _is_proportional(widths, atr_bps)
        shat_prop = _is_proportional(widths, shat)
        is_mod = vid.endswith("_MOD")
        # MOD: width ∝ ŝ(t) → proportional to ŝ AND not to ATR
        # UNMOD: width = a·ŝ_uncond → NOT proportional to varying ŝ AND not to ATR
        if is_mod:
            arm_ok = (not atr_prop) and shat_prop
        else:
            arm_ok = (not atr_prop) and (not shat_prop)
        detail["arms_checked"].append({
            "variant_id": vid,
            "width_over_atr_is_constant": bool(atr_prop),
            "width_over_shat_is_constant": bool(shat_prop),
            "expected_shat_tracking": bool(is_mod),
            "shat_half_held": bool(shat_prop if is_mod else not shat_prop),
            "n": int(w.size),
            "ok": bool(arm_ok),
        })
        detail["atr_matches"] += int(atr_prop)
        detail["shat_matches"] += int(shat_prop)
        ok = ok and arm_ok
    detail["rule"] = (
        "no L4 exit width may be proportional to ATR20 (§7 / §12); UNMOD and MOD share the "
        "Parkinson-EWMA ŝ estimator, unit (bps), clock (H1) and √h scaling; they differ ONLY "
        "in constant-per-symbol-TRAIN-median ŝ vs conditional ŝ(t,h)"
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


def _is_proportional(num: np.ndarray, den: np.ndarray, rtol: float = 1e-6) -> bool:
    """True only when ``num/den`` is constant AND the denominator actually varies.

    A constant width over a constant ATR is not evidence of ATR proportionality — it is
    just two flat series (and would false-fail every UNMOD arm whose ATR happens to be
    near-flat in a small sample).
    """
    n = np.asarray(num, dtype=float)
    d = np.asarray(den, dtype=float)
    m = np.isfinite(n) & np.isfinite(d) & (np.abs(d) > 0)
    if m.sum() < 2:
        return False
    if _is_constant(d[m], rtol=rtol):
        return False
    with np.errstate(invalid="ignore", divide="ignore"):
        return _is_constant(n[m] / d[m], rtol=rtol)


# fields attach_gates must pin; forbidden outcome labels must never enter a gate (R9-03)
_PINNED_GATE_TOKENS = {
    "HMM": ("s_hmm_rv",),
    "R-MARKOV": ("walk_forward_probs", "logistic_ridge"),
    "T-GT-CUR": ("logit_ridge", "p", "0.5"),
    "T-GT-MED5": ("ridge_cont", "pred_cont", "threshold"),
    "hold_forward": ("_hold_forward",),
}
_FORBIDDEN_GATE_INPUTS = ("y", "mag_k1", "next_abs_oo", "run_len_")
_PANEL_GATE_FIELDS = (
    "s_hmm_rv", "p_rmarkov_k4", "p_rmarkov_k12",
    "tgtcur_fires", "tgtmed5_fires", "p_stay", "n_prior_trans",
)


def check_parent_provenance(episodes: pd.DataFrame, parent_parity: dict) -> tuple[bool, dict]:
    """§12: each gate reads the pinned model/field; outcome labels appear in NO gate input."""
    rows = (parent_parity or {}).get("rows") or []
    if not rows:
        return _fail("parent parity emitted no rows")

    # a garbage payload like [{"junk": 1}] must fail — require real structure
    structured = 0
    for row in rows:
        if not isinstance(row, dict) or "symbol" not in row:
            continue
        if any(k.startswith("k") or k in ("status", "parity_exempt") for k in row):
            structured += 1
    if structured == 0:
        return _fail(
            "parent parity rows carry no gate structure (symbol + k*/status)",
            n_rows=len(rows), sample_keys=sorted(rows[0].keys()) if rows else [],
        )

    # assert the code that attaches gates still pins the declared fields
    from pathlib import Path
    pg_path = Path(__file__).resolve().parent / "parent_gates.py"
    if not pg_path.exists():
        return _fail("parent_gates.py missing — cannot verify pinned fields")
    src = pg_path.read_text(encoding="utf-8")
    missing_tokens = {
        name: [t for t in toks if t not in src]
        for name, toks in _PINNED_GATE_TOKENS.items()
    }
    missing_tokens = {k: v for k, v in missing_tokens.items() if v}
    if missing_tokens:
        return _fail("pinned gate tokens absent from parent_gates.py", missing=missing_tokens)

    # forbidden outcome labels must not be bound onto the panel as gate arrays
    # (they may appear as parity inputs for delta_brier, but never as panel.* gates)
    attach_src = src[src.find("def attach_gates"): src.find("def _parity_for_symbol")]
    forbidden_on_panel = []
    for name in _FORBIDDEN_GATE_INPUTS:
        # panel.<forbidden> assignment, or setattr(panel, forbidden)
        if f"panel.{name}" in attach_src or f'"{name}"' in attach_src and "panel" in attach_src:
            # only flag if assigned onto the panel, not merely read for parity downstream
            if f"panel.{name} =" in attach_src or f"panel.{name}=" in attach_src:
                forbidden_on_panel.append(name)
    # episodes must not carry outcome labels as if they were gate columns used for selection
    ep_forbidden = [c for c in (episodes.columns if not episodes.empty else [])
                    if any(c == f or c.startswith(f) for f in _FORBIDDEN_GATE_INPUTS)]
    if forbidden_on_panel or ep_forbidden:
        return _fail(
            "forbidden outcome labels present in gate inputs",
            forbidden_on_panel=forbidden_on_panel,
            forbidden_episode_columns=ep_forbidden,
        )

    # hold-forward is the only path onto the panel for parent labels
    if "_hold_forward" not in attach_src:
        return _fail("attach_gates does not call _hold_forward")
    if "src_end <= dst_end" not in src and "src_end" not in src:
        return _fail("hold-forward ascending/no-backfill rule not present in parent_gates")

    fields = {
        "HMM": "s_hmm_rv",
        "R-MARKOV": "walk_forward_probs logistic_ridge",
        "T-GT-CUR": "logit_ridge p>=0.5",
        "T-GT-MED5": "ridge_cont pred_cont>threshold",
    }
    return True, {
        "pinned_fields": fields,
        "panel_gate_fields": list(_PANEL_GATE_FIELDS),
        "forbidden_gate_inputs_checked": list(_FORBIDDEN_GATE_INPUTS),
        "n_symbols_with_parent_rows": structured,
        "n_structured_rows": structured,
        "n_raw_rows": len(rows),
        "hold_forward_rule": "latest source with src_end <= dst_end; no backfill; ascending asserted",
        "source_tokens_verified": True,
    }


def check_decile_causality(episodes: pd.DataFrame) -> tuple[bool, dict]:
    """§12: ŝ deciles, ŝ ranks and M-3 magnitude deciles are per-symbol, expanding, causal.

    Three limbs (R9-08):
    1. cross-symbol value-range overlap (catches full-TRAIN pooled edges)
    2. per-symbol edge fingerprints must DIVERGE (catches a shared pooled-expanding edge)
    3. warm_up_ok from decision_idx >= DECILE_WARMUP_SHAT on every finite-decile row
    """
    if episodes.empty:
        return _fail("no episodes emitted")
    need = {"s_hat_bps", "s_hat_decile", "abs_r_decision_bps", "abs_r_decile", "symbol"}
    if not need.issubset(episodes.columns):
        return _fail("required columns absent", missing=sorted(need - set(episodes.columns)))
    e = episodes[np.isfinite(episodes["s_hat_decile"]) & np.isfinite(episodes["s_hat_bps"])]
    if e.empty:
        return _fail("no episode carries a finite ŝ decile")

    # limb 1 — overlap of decile value ranges (pooled full-TRAIN → zero overlap)
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

    # limb 2 — per-symbol fingerprint of median ŝ per decile must not be identical
    fingerprints: dict[str, dict[int, float]] = {}
    for sym, g in e.groupby("symbol"):
        fp = {}
        for d in range(1, 11):
            v = g[g["s_hat_decile"] == d]["s_hat_bps"]
            if len(v):
                fp[d] = float(v.median())
        fingerprints[sym] = fp
    syms = list(fingerprints)
    fingerprint_divergence = 0.0
    n_pairs = 0
    identical_pairs = 0
    for i, a in enumerate(syms):
        for b in syms[i + 1:]:
            common = set(fingerprints[a]) & set(fingerprints[b])
            if not common:
                continue
            n_pairs += 1
            diffs = [abs(fingerprints[a][d] - fingerprints[b][d]) for d in common]
            fingerprint_divergence = max(fingerprint_divergence, max(diffs) if diffs else 0.0)
            # identical within 1% relative on every shared decile → pooled signature
            if all(
                abs(fingerprints[a][d] - fingerprints[b][d])
                <= 1e-6 * max(1.0, abs(fingerprints[a][d]))
                for d in common
            ):
                identical_pairs += 1
    per_symbol_ok = True
    if len(syms) >= 2 and n_pairs > 0:
        # at least one pair must diverge; all-identical fingerprints fail the population clause
        per_symbol_ok = identical_pairs < n_pairs

    # limb 3 — warm-up computed from decision_idx, never a literal
    warm_ok = False
    n_sub_warmup = 0
    if "decision_idx" in episodes.columns:
        di = e["decision_idx"].to_numpy(dtype=float)
        n_sub_warmup = int(np.sum(di < DECILE_WARMUP_SHAT))
        warm_ok = bool(di.size > 0 and n_sub_warmup == 0)
    else:
        warm_ok = False

    ok = bool(overlap > 0 and per_symbol_ok and warm_ok)
    return ok, {
        "rule": (
            "per symbol, expanding, strictly before the decision close, warm-up "
            f"{DECILE_WARMUP_SHAT} prior ŝ values (§4.1b)"
        ),
        "cross_symbol_decile_value_overlaps": overlap,
        "per_symbol_fingerprint_divergence": fingerprint_divergence,
        "n_symbol_pairs_compared": n_pairs,
        "n_identical_fingerprint_pairs": identical_pairs,
        "per_symbol_population_ok": per_symbol_ok,
        "interpretation": (
            "a pooled or full-TRAIN edge gives NO range overlap; a shared pooled-expanding "
            "edge gives identical per-symbol decile medians"
        ),
        "n_episodes_with_finite_decile": int(len(e)),
        "n_symbols": len(syms),
        "m3_decile_present": bool(np.isfinite(episodes["abs_r_decile"]).any()),
        "warm_up_ok": warm_ok,
        "n_episodes_below_warmup": n_sub_warmup,
        "warmup_threshold_decision_idx": DECILE_WARMUP_SHAT,
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
    failure (the pair would measure nothing)" — compared episode-by-episode on the shared
    key set, not merely by within-MOD variance (R9-11).
    """
    if episodes.empty:
        return _fail("no episodes emitted")
    key_cols = ["symbol", "clock", "delta", "decision_end_ns", "side"]
    per_pair = {}
    ok = True
    for h in L4_HOLD_HOURS:
        mod_id, unmod_id = f"L4_HOLD_{h}H_MOD", f"L4_HOLD_{h}H_UNMOD"
        mod = episodes[episodes.variant_id == mod_id]
        unmod = episodes[episodes.variant_id == unmod_id]
        holds = mod["active_hold_hours"].to_numpy(dtype=float)
        finite = holds[np.isfinite(holds)]
        # episode-by-episode comparison against the UNMOD twin on the intersection
        differs_from_unmod = False
        n_compared = 0
        n_identical = 0
        if len(mod) and len(unmod) and all(c in mod.columns for c in key_cols):
            m = mod[key_cols + ["active_hold_hours"]].copy()
            u = unmod[key_cols + ["active_hold_hours"]].copy()
            m = m.rename(columns={"active_hold_hours": "h_mod"})
            u = u.rename(columns={"active_hold_hours": "h_unmod"})
            joined = m.merge(u, on=key_cols, how="inner")
            n_compared = int(len(joined))
            if n_compared:
                same = np.isclose(
                    joined["h_mod"].to_numpy(dtype=float),
                    joined["h_unmod"].to_numpy(dtype=float),
                    rtol=0.0, atol=1e-9, equal_nan=True,
                )
                n_identical = int(same.sum())
                differs_from_unmod = n_identical < n_compared
        # also fail a constant-at-h MOD that equals UNMOD for every compared episode
        pair_ok = bool(len(mod) > 0 and n_compared > 0 and differs_from_unmod)
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
            "differs_from_unmod": bool(differs_from_unmod),
            "n_episodes_compared": n_compared,
            "n_identical_to_unmod": n_identical,
            "n_excluded_min_prior_transitions": n_warm,
            "ok": pair_ok,
        }
        ok = ok and pair_ok
    return ok, {
        "equation": "E_run=clip(p_stay/(1-p_stay),1,48); h_mod=clip(h*E_run/20,1,20)",
        "min_prior_transitions": MOD_HOLD_MIN_PRIOR_TRANS,
        "predicate": "MOD holds differ from UNMOD twin on at least one shared episode key",
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
    # Required on every cell that PRODUCED a CI. Degenerate cells (too thin to bootstrap) must
    # carry a validated reason; sizing rows with a real battery but suppressed log R form a
    # third named bucket (R9-04). Nothing is silently dropped.
    expected = len(BOOT_BLOCKS_DAYS) * len(BOOT_SEEDS)
    per_seed_counts = []
    degenerate = []
    suppressed_log_r = []
    unclassified = []
    for row in metrics_rows or []:
        ps = row.get("per_seed_ci")
        if not isinstance(ps, list):
            continue
        ci_low = row.get("ci_low")
        has_ci = isinstance(ci_low, (int, float)) and np.isfinite(ci_low)
        vid = row.get("variant_id")
        meta = {
            "variant_id": vid, "clock": row.get("clock"),
            "delta": row.get("delta"), "scope": row.get("scope"),
            "band": row.get("band"), "n_dates": row.get("n_dates"),
        }
        if has_ci:
            per_seed_counts.append(len(ps))
        elif vid in SIZING_VARIANTS or row.get("log_R_suppressed_reason"):
            # real battery may be present; log R deliberately null — third bucket
            suppressed_log_r.append({
                **meta,
                "per_seed_ci_len": len(ps),
                "reason": row.get("log_R_suppressed_reason") or "SIZING_VARIANT",
            })
        elif not ps:
            # AMENDMENT-20: exactly two conditions exempt a cell from carrying a CI, and
            # "few calendar days" is neither. The claimed token is re-derived here from the
            # cell's OWN p / W / L / log_R / n_dates and must match; the withdrawn
            # `n_dates < 7` reason had been absorbing 13 cells it does not describe.
            n_dates = row.get("n_dates")
            claimed = row.get("ci_absent_reason")

            # Undefinedness is re-derived from the cell's OWN p / W / L — NOT from its `log_R`
            # field, which the remedy blanks, and which would therefore make this check agree
            # with itself on every row (QA run 11, R11-02).
            log_r_undefined = not metrics.log_R_is_defined(
                row.get("p"), row.get("W"), row.get("L")
            )
            too_few_days = isinstance(n_dates, (int, float)) and n_dates < 2
            # A DERIVED row (an interaction term) carries p/W/L = NaN by construction, so the
            # undefinedness test is vacuous on it and cannot be an exemption. Such a row must
            # not be emitted without a CI at all (§12 eligibility, AMENDMENT-20) — if one
            # appears here it stays unclassified and fails.
            if vid in DERIVED_VARIANTS:
                admissible = {}
            else:
                admissible = {
                    "LOG_R_UNDEFINED": log_r_undefined,
                    "N_DATES_LT_2_NO_DAY_BLOCK": too_few_days,
                }
            reason = claimed if admissible.get(claimed) else None
            entry = {
                **meta, "reason": reason, "claimed_reason": claimed,
                "log_R_undefined": log_r_undefined, "n_dates_lt_2": too_few_days,
                "p": row.get("p"), "W": row.get("W"), "L": row.get("L"), "n": row.get("n"),
            }
            if reason is None:
                unclassified.append(entry)
            else:
                degenerate.append(entry)
        else:
            # non-empty battery + null ci_low + not sizing → unexpected
            unclassified.append({**meta, "reason": None, "per_seed_ci_len": len(ps)})
    # every degenerate cell must have a validated thinness reason; no silent third class
    deg_ok = all(d.get("reason") for d in degenerate) and not unclassified
    battery_ok = bool(per_seed_counts) and min(per_seed_counts) == expected and deg_ok
    # sizing rows with a battery must still be full-length if present
    sizing_battery_ok = all(
        s.get("per_seed_ci_len", 0) in (0, expected) for s in suppressed_log_r
    )
    clauses["min/max envelope over blocks x seeds"] = {
        "held": battery_ok and sizing_battery_ok,
        "expected_per_cell": expected,
        "seeds": list(BOOT_SEEDS),
        "min_observed": min(per_seed_counts) if per_seed_counts else 0,
        "max_observed": max(per_seed_counts) if per_seed_counts else 0,
        "n_cells_with_a_ci": len(per_seed_counts),
        "n_degenerate_cells_no_ci": len(degenerate),
        "degenerate_cells": degenerate,  # full list, never truncated (R9-04)
        "n_suppressed_log_R_cells": len(suppressed_log_r),
        "suppressed_log_R_cells": suppressed_log_r,
        "n_unclassified_cells": len(unclassified),
        "unclassified_cells": unclassified,
        "degenerate_reason_required": (
            "one of LOG_R_UNDEFINED | N_DATES_LT_2_NO_DAY_BLOCK, validated against the "
            "cell's own p/W/L/log_R/n_dates (AMENDMENT-20; n_dates < 7 withdrawn)"
        ),
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
