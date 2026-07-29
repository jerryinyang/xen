"""Parent gates: HMM, T-GT-CUR, T-GT-MED5, R-MARKOV k=4/12 (design §4.1a).

R-MARKOV probabilities are regenerated via SPDR-015's frozen walk_forward_probs — never
reimplemented. Parent parity is HARD.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import polars as pl

from config import (
    MOD_HOLD_MIN_PRIOR_TRANS as MIN_PRIOR_TRANSITIONS,
    NS,
    PARENT_015_CODE,
    PARENT_015_RESULTS,
    PARITY_EXEMPT_SYMBOLS,
)
from panel import SymbolPanel, _hold_forward


_TRANS_CACHE = {}

# dependency order: transitions -> {config, controls, features}; features -> {config, hmm}
_PARENT_MODULE_NAMES = ("config", "hmm", "features", "controls", "transitions")


def _load_by_path(name: str, path: Path):
    """Import one module from an explicit file path under a private module name.

    The parent's modules bind each other by bare name (``import config``), so they are
    registered under both their private key and their bare name for the duration of the load,
    then the bare names are restored. Nothing this screen imported is ever deleted from
    ``sys.modules`` and ``sys.path`` is never mutated (QA run 8, R8-29).
    """
    private = f"_SPDR_015__{name}"
    if private in sys.modules:
        return sys.modules[private]
    spec = importlib.util.spec_from_file_location(private, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {name} from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[private] = mod
    saved = {n: sys.modules.get(n) for n in _PARENT_MODULE_NAMES}
    try:
        for n in _PARENT_MODULE_NAMES:
            key = f"_SPDR_015__{n}"
            if key in sys.modules:
                sys.modules[n] = sys.modules[key]
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(private, None)
        raise
    finally:
        for n, prev in saved.items():
            if prev is None:
                sys.modules.pop(n, None)
            else:
                sys.modules[n] = prev
    return mod


def _load_015_transitions():
    """Isolated import of SPDR-015 walk_forward_probs, by explicit path."""
    if "transitions" in _TRANS_CACHE:
        return _TRANS_CACHE["transitions"]
    for name in _PARENT_MODULE_NAMES:
        mod = _load_by_path(name, PARENT_015_CODE / f"{name}.py")
        _TRANS_CACHE[name] = mod
    return _TRANS_CACHE["transitions"]


def load_regime_states(symbol: str) -> pl.DataFrame:
    path = PARENT_015_RESULTS / "regime_states.parquet"
    df = pl.read_parquet(path)
    return df.filter((pl.col("symbol") == symbol) & (pl.col("clock") == "H1")).sort("slot_end")


def load_zz_ordinal(symbol: str) -> pl.DataFrame:
    path = PARENT_015_RESULTS / "zz_ordinal.parquet"
    df = pl.read_parquet(path)
    # the hold-forward walk requires ascending source order; never depend on the parent
    # artifact's storage order (QA run 8, R8-21)
    return df.filter(
        (pl.col("symbol") == symbol) & (pl.col("clock") == "H1")
    ).sort("confirm_slot_end")


def attach_gates(panel: SymbolPanel, symbol: str, *, trans_mod=None) -> dict:
    """Attach held-forward parent gates onto a decision panel. Returns parity payload piece."""
    rs = load_regime_states(symbol)
    parity: dict = {"symbol": symbol}

    if rs.height == 0:
        n = panel.close.size
        panel.s_hmm_rv = np.full(n, np.nan)
        panel.p_rmarkov_k4 = np.full(n, np.nan)
        panel.p_rmarkov_k12 = np.full(n, np.nan)
        panel.tgtcur_fires = np.full(n, np.nan)
        panel.tgtmed5_fires = np.full(n, np.nan)
        panel.p_stay = np.full(n, np.nan)
        panel.n_prior_trans = np.zeros(n)
        parity["status"] = "NO_REGIME_ROWS"
        return parity

    src_end = rs["slot_end"].to_numpy().astype(np.int64)
    s_hmm = rs["s_hmm_rv"].to_numpy().astype(float)
    panel.s_hmm_rv = _hold_forward(src_end, s_hmm, panel.slot_end)

    # R-MARKOV walk-forward probs via parent function
    if trans_mod is None:
        trans_mod = _load_015_transitions()

    # build feature matrix exactly as parent: columns from regime_states
    cols = {
        "s_markov": rs["s_markov"].to_numpy().astype(float),
        "dur_markov": rs["dur_markov"].to_numpy().astype(float),
        "rv20": rs["rv20"].to_numpy().astype(float),
        "park_ewma": rs["park_ewma"].to_numpy().astype(float),
        "lvl_pct": rs["lvl_pct"].to_numpy().astype(float),
        "n_high_4_markov": rs["n_high_4_markov"].to_numpy().astype(float),
        "n_high_12_markov": rs["n_high_12_markov"].to_numpy().astype(float),
        "s_shock": rs["s_shock"].to_numpy().astype(float),
    }
    state = cols["s_markov"].astype(np.int64)
    # parent uses int state with -1 for invalid
    state_i = np.where(np.isfinite(cols["s_markov"]), cols["s_markov"].astype(np.int64), -1)
    X = trans_mod._feature_matrix_for_model(cols, "R-MARKOV")
    slot_end = src_end
    is_origin = rs["is_origin"].to_numpy().astype(bool)

    probs4 = trans_mod.walk_forward_probs(state_i, X, slot_end, is_origin, 4)
    probs12 = trans_mod.walk_forward_probs(state_i, X, slot_end, is_origin, 12)
    p4 = probs4["logistic_ridge"]
    p12 = probs12["logistic_ridge"]
    panel.p_rmarkov_k4 = _hold_forward(src_end, p4, panel.slot_end)
    panel.p_rmarkov_k12 = _hold_forward(src_end, p12, panel.slot_end)

    # parity: recompute delta_brier_vs_pers for k=4,12
    parity.update(_parity_for_symbol(symbol, state_i, probs4, probs12, is_origin, rs, trans_mod))

    # p_stay for MOD hold: same-state transition rate on ≥30 prior transitions
    panel.p_stay, panel.n_prior_trans = _p_stay_series(state_i, src_end, panel.slot_end)

    # T-GT-CUR / T-GT-MED5
    zz = load_zz_ordinal(symbol)
    n = panel.close.size
    tgtcur = np.full(n, np.nan)
    tgtmed5 = np.full(n, np.nan)
    if zz.height:
        cur = zz.filter((pl.col("target") == "T-GT-CUR") & (pl.col("model") == "logit_ridge"))
        med = zz.filter((pl.col("target") == "T-GT-MED5") & (pl.col("model") == "ridge_cont"))
        if cur.height:
            # FIRES when p >= 0.5; hold forward from confirm_slot_end
            c_end = cur["confirm_slot_end"].to_numpy().astype(np.int64)
            c_fire = (cur["p"].to_numpy().astype(float) >= 0.5).astype(float)
            tgtcur = _hold_forward(c_end, c_fire, panel.slot_end)
        if med.height:
            m_end = med["confirm_slot_end"].to_numpy().astype(np.int64)
            pred = med["pred_cont"].to_numpy().astype(float)
            thr = med["threshold"].to_numpy().astype(float)
            m_fire = (pred > thr).astype(float)
            tgtmed5 = _hold_forward(m_end, m_fire, panel.slot_end)
    panel.tgtcur_fires = tgtcur
    panel.tgtmed5_fires = tgtmed5
    return parity


def _parity_for_symbol(symbol, state, probs4, probs12, is_origin, rs, trans_mod) -> dict:
    """Compare regenerated delta_brier_vs_pers to SPDR-015 emission (|Δ| ≤ 1e-9)."""
    tm = pl.read_parquet(PARENT_015_RESULTS / "transition_metrics.parquet")
    parent = tm.filter(
        (pl.col("symbol") == symbol)
        & (pl.col("clock") == "H1")
        & (pl.col("model") == "R-MARKOV")
        & (pl.col("method") == "logistic_ridge")
    )
    out: dict = {"symbol": symbol, "parity_exempt": symbol in PARITY_EXEMPT_SYMBOLS}
    dates = rs["target_date"].to_numpy() if "target_date" in rs.columns else (rs["slot_end"].to_numpy() // NS // 86400)
    next_abs = rs["next_abs_oo"].to_numpy() if "next_abs_oo" in rs.columns else None

    for k, probs in ((4, probs4), (12, probs12)):
        y = probs["y"]
        p = probs["logistic_ridge"]
        p_pers = probs["persistence"]
        row = trans_mod.metrics_row(
            symbol, "H1", "R-MARKOV", "logistic_ridge", k,
            y, p, p_pers, is_origin, dates, state, next_abs,
        )
        ours = row.get("delta_brier_vs_pers", float("nan"))
        pref = parent.filter(pl.col("horizon_k") == k)
        if pref.height == 0:
            out[f"k{k}"] = {"status": "NO_PARENT_ROW", "ours": ours}
            continue
        theirs = float(pref["delta_brier_vs_pers"][0])
        if symbol in PARITY_EXEMPT_SYMBOLS:
            out[f"k{k}"] = {
                "status": "PARITY_EXEMPT",
                "ours": ours, "parent": theirs,
                "reason": "parent null / <40 origins",
            }
            continue
        if not np.isfinite(theirs):
            out[f"k{k}"] = {"status": "PARENT_NAN", "ours": ours, "parent": theirs}
            continue
        d = abs(ours - theirs) if np.isfinite(ours) else float("inf")
        out[f"k{k}"] = {
            "status": "OK" if d <= 1e-9 else "FAIL",
            "ours": ours, "parent": theirs, "abs_diff": d,
        }
    return out


def _p_stay_series(
    state: np.ndarray, src_end: np.ndarray, dst_end: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """p_stay(t): same-state transition rate on ≥30 PRIOR transitions with both ends < t.

    Transition at origin i is (state[i] -> state[i+1]), available after slot_end[i+1].
    """
    n = state.size
    p_src = np.full(n, np.nan)
    n_src = np.zeros(n, dtype=float)
    if n < 2:
        return _hold_forward(src_end, p_src, dst_end), np.zeros(dst_end.size)

    # completed transitions: transition at origin i is (state[i] -> state[i+1]), available
    # once slot_end[i+1] has passed
    valid = (state[:-1] >= 0) & (state[1:] >= 0)
    av_ts = src_end[1:][valid]
    origin = state[:-1][valid]
    stayed = (state[:-1][valid] == state[1:][valid]).astype(float)

    # per origin state, cumulative counts over transitions available STRICTLY BEFORE src_end[i].
    # searchsorted over the per-state available-timestamp list replaces the O(n^2) scan; the
    # transitions are already in ascending availability order because src_end is ascending.
    for st in np.unique(origin):
        sel = origin == st
        ts_st = av_ts[sel]
        stayed_st = stayed[sel]
        c_n = np.concatenate(([0.0], np.cumsum(np.ones(ts_st.size))))
        c_s = np.concatenate(([0.0], np.cumsum(stayed_st)))
        rows = np.where(state == st)[0]
        if rows.size == 0:
            continue
        k = np.searchsorted(ts_st, src_end[rows], side="left")  # strictly before src_end[i]
        n_src[rows] = c_n[k]
        enough = k >= MIN_PRIOR_TRANSITIONS
        idx = rows[enough]
        if idx.size:
            kk = k[enough]
            p_src[idx] = c_s[kk] / c_n[kk]
    p_dst = _hold_forward(src_end, p_src, dst_end)
    n_dst = _hold_forward(src_end, n_src, dst_end)
    n_dst = np.where(np.isfinite(n_dst), n_dst, 0.0)
    return p_dst, n_dst


def run_all_parity(symbols: list[str]) -> dict:
    """Parent-gate parity for all symbols → results/parent_gate_parity.json payload."""
    trans = _load_015_transitions()
    rows = []
    for sym in symbols:
        # need a dummy panel size from regime states only for parity calc
        rs = load_regime_states(sym)
        if rs.height == 0:
            rows.append({"symbol": sym, "status": "NO_REGIME_ROWS",
                         "parity_exempt": sym in PARITY_EXEMPT_SYMBOLS})
            continue
        # minimal panel for attach path's parity section
        dummy = SymbolPanel(
            symbol=sym, clock="H1",
            slot_start=np.array([0], dtype=np.int64),
            slot_end=np.array([int(rs["slot_end"][-1])], dtype=np.int64),
            open=np.array([1.0]), high=np.array([1.0]), low=np.array([1.0]),
            close=np.array([1.0]), atr20=np.array([1.0]),
            s_hat_bps=np.array([1.0]), s_hat_decile=np.array([5.0]),
            s_hat_rank=np.array([0.5]), s_hat_uncond=1.0,
            abs_r_decision_bps=np.array([1.0]),
            abs_r_decile=np.array([5.0]),
            m1={"ts": np.array([0], dtype=np.int64), "open": np.array([1.0]),
                "high": np.array([1.0]), "low": np.array([1.0]), "close": np.array([1.0])},
        )
        rows.append(attach_gates(dummy, sym, trans_mod=trans))
    # HARD: every non-exempt symbol must produce an OK on BOTH k=4 and k=12. Any other
    # status — FAIL, NO_PARENT_ROW, PARENT_NAN, NO_REGIME_ROWS, or a missing cell — is a
    # failure, never a vacuous pass (P-23/L-52; QA run 8, R8-15).
    failures = []
    exempt = []
    ok = []
    for r in rows:
        if r.get("parity_exempt"):
            exempt.append(r["symbol"])
            continue
        if r.get("status") == "NO_REGIME_ROWS":
            failures.append({"symbol": r["symbol"], "k": "both", "status": "NO_REGIME_ROWS"})
            continue
        for k in ("k4", "k12"):
            cell = r.get(k)
            if cell is None:
                failures.append({"symbol": r["symbol"], "k": k, "status": "CHECK_MISSING"})
            elif cell.get("status") == "OK":
                ok.append({"symbol": r["symbol"], "k": k})
            else:
                failures.append({"symbol": r["symbol"], "k": k, **cell})
    n_non_exempt = len([s for s in symbols if s not in PARITY_EXEMPT_SYMBOLS])
    required_ok = 2 * n_non_exempt
    return {
        "n_symbols": len(symbols),
        "parity_exempt_by_name": sorted(PARITY_EXEMPT_SYMBOLS),
        "n_parity_exempt": len(PARITY_EXEMPT_SYMBOLS),
        "n_checked": n_non_exempt,
        "failures": failures,
        "n_ok": len(ok),
        "n_ok_required": required_ok,
        "rows": rows,
        "hard_pass": bool(len(failures) == 0 and len(ok) == required_ok and n_non_exempt > 0),
        "tol": 1e-9,
        "note": (
            "regenerated via SPDR-015 walk_forward_probs; compared to transition_metrics "
            "delta_brier_vs_pers for R-MARKOV logistic_ridge k=4,12"
        ),
    }
