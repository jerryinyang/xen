"""Arm 2a forecast methods + metrics with mandatory Δ vs persistence (design §2.4–2.5)."""
from __future__ import annotations

import json

import numpy as np

from config import (
    BOOT_BLOCKS,
    BOOT_RESAMPLES,
    BOOT_SEEDS,
    DERANGE_SEEDS,
    HORIZONS_K,
    INITIAL_FIT_FRACTION,
    LOGIT_RIDGE_ALPHA,
    MIN_DATES,
    MIN_ORIGINS,
    MIN_TRANS,
    NS,
)
from controls import label_derange_collapse
from features import future_state_targets, transition_flags
from xen.evaluation import block_bootstrap_ci

# origins per calendar day per clock — converts design's day-blocks (§5 blocks 1/3/7) to
# origin-position blocks for the block bootstrap; block is floored at H (=k) so block≥H holds.
BARS_PER_DAY = {"H1": 24, "H4": 6, "D1": 1}

# 2a cells eligible for the LABEL-SHUFFLE derangement collapse (design §4): the level-regime
# models under the two fitted forecast methods, all horizons. R-SHOCK/persistence excluded.
DERANGE_MODELS_2A = ("R-MARKOV", "R-HMM-RV")
DERANGE_METHODS_2A = ("empirical_p", "logistic_ridge")


def _clip_p(p: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    return np.clip(p, eps, 1.0 - eps)


def brier(y: np.ndarray, p: np.ndarray) -> float:
    m = np.isfinite(p) & (y >= 0)
    if m.sum() < 1:
        return float("nan")
    return float(np.mean((p[m] - y[m].astype(float)) ** 2))


def log_loss(y: np.ndarray, p: np.ndarray) -> float:
    m = np.isfinite(p) & (y >= 0)
    if m.sum() < 1:
        return float("nan")
    pp = _clip_p(p[m])
    yy = y[m].astype(float)
    return float(-np.mean(yy * np.log(pp) + (1.0 - yy) * np.log(1.0 - pp)))


def accuracy(y: np.ndarray, p: np.ndarray, thr: float = 0.5) -> float:
    m = np.isfinite(p) & (y >= 0)
    if m.sum() < 1:
        return float("nan")
    pred = (p[m] >= thr).astype(int)
    return float(np.mean(pred == y[m]))


def balanced_accuracy(y: np.ndarray, p: np.ndarray, thr: float = 0.5) -> float:
    m = np.isfinite(p) & (y >= 0)
    if m.sum() < 1:
        return float("nan")
    pred = (p[m] >= thr).astype(int)
    yy = y[m]
    scores = []
    for cls in (0, 1):
        mask = yy == cls
        if mask.sum() == 0:
            continue
        scores.append(float(np.mean(pred[mask] == cls)))
    return float(np.mean(scores)) if scores else float("nan")


def _month_keys_from_slot_end(slot_end: np.ndarray) -> np.ndarray:
    dt = (slot_end // 1_000_000).astype("datetime64[ms]")
    years = dt.astype("datetime64[Y]").astype(int) + 1970
    months = dt.astype("datetime64[M]").astype(int) % 12 + 1
    return (years * 12 + months).astype(np.int64)


def _logistic_ridge_fit(X: np.ndarray, y: np.ndarray, alpha: float = LOGIT_RIDGE_ALPHA
                        ) -> np.ndarray | None:
    """IRLS logistic ridge; returns weights including intercept column 0."""
    m = np.isfinite(X).all(axis=1) & (y >= 0)
    if m.sum() < 30:
        return None
    Xv = X[m]
    yv = y[m].astype(float)
    mu = Xv.mean(axis=0)
    sd = Xv.std(axis=0)
    sd[sd == 0] = 1.0
    Xs = (Xv - mu) / sd
    ones = np.ones((Xs.shape[0], 1))
    Z = np.hstack([ones, Xs])
    w = np.zeros(Z.shape[1])
    for _ in range(40):
        eta = Z @ w
        p = 1.0 / (1.0 + np.exp(-np.clip(eta, -30, 30)))
        W = p * (1.0 - p)
        W = np.maximum(W, 1e-6)
        z = eta + (yv - p) / W
        # weighted ridge: (Z' W Z + α I) w = Z' W z; no ridge on intercept
        Zw = Z * W[:, None]
        A = Z.T @ Zw
        A[1:, 1:] += alpha * np.eye(A.shape[0] - 1)
        b = Z.T @ (W * z)
        try:
            w_new = np.linalg.solve(A, b)
        except np.linalg.LinAlgError:
            return None
        if np.max(np.abs(w_new - w)) < 1e-6:
            w = w_new
            break
        w = w_new
    return np.concatenate([w, mu, sd])  # pack: w (p+1), mu (p), sd (p)


def _logistic_predict(pack: np.ndarray, X: np.ndarray) -> np.ndarray:
    p = X.shape[1]
    w = pack[: p + 1]
    mu = pack[p + 1 : 2 * p + 1]
    sd = pack[2 * p + 1 : 3 * p + 1]
    Xs = (X - mu) / sd
    ones = np.ones((X.shape[0], 1))
    Z = np.hstack([ones, Xs])
    eta = Z @ w
    return 1.0 / (1.0 + np.exp(-np.clip(eta, -30, 30)))


def _feature_matrix_for_model(df_cols: dict, model: str) -> np.ndarray:
    """Build §2.3 feature matrix for a state model."""
    if model == "R-MARKOV":
        s = df_cols["s_markov"]
        dur = df_cols["dur_markov"]
        n4 = df_cols["n_high_4_markov"]
        n12 = df_cols["n_high_12_markov"]
    elif model == "R-HMM-RV":
        s = df_cols["s_hmm_rv"]
        dur = df_cols["dur_hmm"]
        n4 = df_cols["n_high_4_hmm"]
        n12 = df_cols["n_high_12_hmm"]
    else:  # R-SHOCK — forecast still defined but not titled regime skill
        s = df_cols["s_shock"]
        dur = np.zeros_like(s)
        n4 = np.zeros_like(s, dtype=float)
        n12 = np.zeros_like(s, dtype=float)

    shock = df_cols["s_shock"].astype(float)
    shock = np.where(shock < 0, 0.0, shock)
    X = np.column_stack([
        s.astype(float),
        dur.astype(float),
        df_cols["rv20"],
        df_cols["park_ewma"],
        df_cols["lvl_pct"],
        n4.astype(float),
        n12.astype(float),
        shock,
    ])
    # replace invalid state rows
    bad = s < 0
    X[bad] = np.nan
    return X


def walk_forward_probs(
    state: np.ndarray,
    X: np.ndarray,
    slot_end: np.ndarray,
    is_origin: np.ndarray,
    k: int,
) -> dict[str, np.ndarray]:
    """OOS P(HIGH_{t+k}) for persistence / empirical_p / logistic_ridge."""
    n = state.size
    y = future_state_targets(state, k)
    p_pers = np.full(n, np.nan)
    p_emp = np.full(n, np.nan)
    p_logit = np.full(n, np.nan)

    # persistence: P = current state (as probability 0/1)
    valid_s = state >= 0
    p_pers[valid_s] = state[valid_s].astype(float)

    origin_idx = np.where(is_origin & valid_s & (y >= 0))[0]
    if origin_idx.size < 40:
        return {"persistence": p_pers, "empirical_p": p_emp, "logistic_ridge": p_logit, "y": y}

    # initial fit boundary
    n_fit0 = max(30, int(INITIAL_FIT_FRACTION * origin_idx.size))
    fit_end_origin = origin_idx[n_fit0 - 1]
    month_keys = _month_keys_from_slot_end(slot_end)

    # empirical expanding transition counts for horizon-k: count s_t -> s_{t+k}
    # at each origin, use only past origins
    # logistic monthly refit

    # precompute month change points among origins after fit_end
    oos_origins = origin_idx[origin_idx > fit_end_origin]
    if oos_origins.size == 0:
        return {"persistence": p_pers, "empirical_p": p_emp, "logistic_ridge": p_logit, "y": y}

    # empirical: for each oos origin t, use all prior origins with valid y
    for t in oos_origins:
        past = origin_idx[origin_idx < t]
        if past.size < 20:
            continue
        # stay/switch conditional on s_t class
        st = state[t]
        same = past[state[past] == st]
        if same.size < 5:
            p_emp[t] = float(st)  # fall back
        else:
            # P(y=1 | s_t = st)
            p_emp[t] = float(np.mean(y[same] == 1))

    # logistic ridge: monthly expanding
    points = [int(oos_origins[0])]
    for i in range(1, oos_origins.size):
        t = int(oos_origins[i])
        if month_keys[t] != month_keys[oos_origins[i - 1]]:
            points.append(t)
    points.append(int(oos_origins[-1]) + 1)

    for a, b in zip(points[:-1], points[1:]):
        train_idx = origin_idx[origin_idx < a]
        if train_idx.size < 30:
            continue
        Xtr = X[train_idx]
        ytr = y[train_idx]
        pack = _logistic_ridge_fit(Xtr, ytr)
        if pack is None:
            continue
        # predict all origins in [a, b)
        pred_idx = origin_idx[(origin_idx >= a) & (origin_idx < b)]
        if pred_idx.size == 0:
            continue
        p_logit[pred_idx] = _logistic_predict(pack, X[pred_idx])

    return {"persistence": p_pers, "empirical_p": p_emp, "logistic_ridge": p_logit, "y": y}


def metrics_row(
    symbol: str,
    clock: str,
    model: str,
    method: str,
    k: int,
    y: np.ndarray,
    p: np.ndarray,
    p_pers: np.ndarray,
    is_origin: np.ndarray,
    dates: np.ndarray,
    state: np.ndarray,
    next_abs_oo: np.ndarray | None = None,
) -> dict:
    """One metrics row with levels + Δ vs persistence."""
    m = is_origin & np.isfinite(p) & np.isfinite(p_pers) & (y >= 0) & (state >= 0)
    n_origins = int(m.sum())
    n_dates = int(np.unique(dates[m]).size) if n_origins else 0
    yy = y[m].astype(float) if n_origins else np.array([])
    pp = p[m] if n_origins else np.array([])
    p0 = p_pers[m] if n_origins else np.array([])

    acc = accuracy(y, p) if n_origins else float("nan")
    bacc = balanced_accuracy(y, p) if n_origins else float("nan")
    br = brier(y, p) if n_origins else float("nan")
    ll = log_loss(y, p) if n_origins else float("nan")
    acc0 = accuracy(y, p_pers) if n_origins else float("nan")
    br0 = brier(y, p_pers) if n_origins else float("nan")
    ll0 = log_loss(y, p_pers) if n_origins else float("nan")

    d_brier = br - br0 if np.isfinite(br) and np.isfinite(br0) else float("nan")
    d_ll = ll - ll0 if np.isfinite(ll) and np.isfinite(ll0) else float("nan")
    d_acc = acc - acc0 if np.isfinite(acc) and np.isfinite(acc0) else float("nan")

    powered = n_origins >= MIN_ORIGINS and n_dates >= MIN_DATES

    # block-bootstrap CI on Δ Brier — design §5 (blocks 1/3/7 days, 5-seed envelope, 2000
    # resamples, block≥H); conservative envelope across the sweep drives the band (QA Issue 3).
    # Only powered, non-persistence cells are band-eligible: UNPOWERED cells label UNPOWERED
    # regardless, and persistence's Δ vs itself is identically 0 — skipping both is band-neutral
    # and avoids running the bootstrap where it cannot change the label.
    run_ci = powered and method != "persistence"
    ci_sweep = _delta_brier_ci_sweep(yy, pp, p0, clock, k) if run_ci else {"ci": [float("nan")] * 2, "sweep": []}
    d_brier_ci_lo, d_brier_ci_hi = ci_sweep["ci"]

    if not powered:
        band = "UNPOWERED"
    elif np.isfinite(d_brier) and d_brier < 0 and np.isfinite(d_brier_ci_hi) and d_brier_ci_hi < 0:
        band = "SUPPORTED"
    elif np.isfinite(d_brier) and d_brier > 0 and np.isfinite(d_brier_ci_lo) and d_brier_ci_lo > 0:
        band = "CONTRADICTED"
    else:
        band = "WASH"

    # stickiness: fraction of times s_t == s_{t+k} (persistence ceiling)
    stickiness = (
        float(np.mean(state[m] == y[m].astype(np.int64))) if n_origins else float("nan")
    )

    row = {
        "symbol": symbol,
        "clock": clock,
        "model": model,
        "method": method,
        "horizon_k": k,
        "n_origins": n_origins,
        "n_dates": n_dates,
        "accuracy": acc,
        "balanced_accuracy": bacc,
        "brier": br,
        "log_loss": ll,
        "accuracy_persistence": acc0,
        "brier_persistence": br0,
        "log_loss_persistence": ll0,
        "delta_accuracy_vs_pers": d_acc,
        "delta_brier_vs_pers": d_brier,  # negative = better
        "delta_logloss_vs_pers": d_ll,
        "delta_brier_ci_lo": d_brier_ci_lo,  # conservative envelope (min over block sweep)
        "delta_brier_ci_hi": d_brier_ci_hi,  # conservative envelope (max over block sweep)
        "delta_brier_ci_sweep_json": json.dumps(ci_sweep.get("sweep", [])),
        "stickiness": stickiness,
        "base_rate_high": float(np.mean(yy)) if n_origins else float("nan"),
        "band_label": band,
        "is_shock_comparator": model == "R-SHOCK",
        "note": "R-SHOCK is shock flag not regime" if model == "R-SHOCK" else "",
    }

    # state gap (HIGH - LOW next |oo|) for level models only
    if next_abs_oo is not None and model != "R-SHOCK" and n_origins:
        sm = state[m]
        nao = next_abs_oo[m]
        hi = nao[sm == 1]
        lo = nao[sm == 0]
        hi = hi[np.isfinite(hi)]
        lo = lo[np.isfinite(lo)]
        row["state_gap_bps"] = (
            float(np.mean(hi) - np.mean(lo)) if hi.size and lo.size else float("nan")
        )
        row["mean_next_abs_oo_HIGH"] = float(np.mean(hi)) if hi.size else float("nan")
        row["mean_next_abs_oo_LOW"] = float(np.mean(lo)) if lo.size else float("nan")
    else:
        row["state_gap_bps"] = float("nan")
        row["mean_next_abs_oo_HIGH"] = float("nan")
        row["mean_next_abs_oo_LOW"] = float("nan")

    return row


def _delta_brier_ci_sweep(
    y: np.ndarray, p: np.ndarray, p0: np.ndarray, clock: str, k: int,
) -> dict:
    """Block-bootstrap CI for Δ Brier vs persistence — design §5 inference (QA Issue 3 fix).

    Δ Brier = mean over origins of the per-origin contribution
    ``d_i = (p_i - y_i)^2 - (p0_i - y_i)^2`` — a plain sample mean, so the canonical
    circular block bootstrap (`xen.evaluation.block_bootstrap_ci`) applies directly.

    Design §5 declares blocks 1/3/7 (days) + a multi-seed envelope + 2000 resamples. Origins
    at horizon k have forward windows overlapping k adjacent origins, so the HARD dependence
    unit is k origin-positions (Phase-010 block≥H). Each day-block is converted to
    ``day * BARS_PER_DAY[clock]`` origin-positions and floored at k, so block≥H holds on every
    cell (including the H4 k=12 cell QA flagged as under-blocked at a bare 1-day = 6 bars).

    Band CI (`ci` = [ci_lo_min, ci_hi_max]) is the **conservative envelope across the block
    sweep** (widest interval) — block-fragile inference cannot manufacture a SUPPORTED label
    (IN-4). The full sweep + per-seed range are emitted for disclosure.
    """
    d = (p - y.astype(float)) ** 2 - (p0 - y.astype(float)) ** 2
    d = d[np.isfinite(d)]
    n = int(d.size)
    if n < 30:
        return {"ci": [float("nan"), float("nan")], "n": n, "sweep": []}
    bpd = BARS_PER_DAY.get(clock, 1)
    sweep = []
    for bd in BOOT_BLOCKS:
        eff_block = max(int(bd) * bpd, int(k))  # HARD: block ≥ H (=k origin-positions)
        r = block_bootstrap_ci(
            d, np.mean, block=eff_block, n_boot=BOOT_RESAMPLES,
            seed=int(BOOT_SEEDS[0]), n_seeds=len(BOOT_SEEDS),
        )
        sweep.append({
            "block_days": int(bd), "eff_block_bars": eff_block,
            "ci_lo": r["ci"][0], "ci_hi": r["ci"][1],
            "ci_lo_seed_range": r["ci_low_seed_range"],
            "ci_hi_seed_range": r["ci_high_seed_range"],
        })
    ci_lo_min = min(s["ci_lo"] for s in sweep)
    ci_hi_max = max(s["ci_hi"] for s in sweep)
    return {"ci": [ci_lo_min, ci_hi_max], "n": n, "sweep": sweep}


def transition_metric_rows(
    symbol: str,
    clock: str,
    model: str,
    state: np.ndarray,
    is_origin: np.ndarray,
    dates: np.ndarray,
    k_list: tuple[int, ...] = (4, 12),
) -> list[dict]:
    """Transition hit rates vs base (often UNPOWERED)."""
    rows = []
    for k in k_list:
        up, dn = transition_flags(state, k)
        m = is_origin & (state >= 0)
        for name, flag, cond in (
            ("trans_up", up, state == 0),
            ("trans_dn", dn, state == 1),
        ):
            mm = m & cond
            n = int(mm.sum())
            n_trans = int(flag[mm].sum()) if n else 0
            rate = float(np.mean(flag[mm])) if n else float("nan")
            band = "UNPOWERED" if n_trans < MIN_TRANS or n < MIN_ORIGINS else "DISCLOSURE"
            rows.append({
                "symbol": symbol, "clock": clock, "model": model,
                "metric": name, "horizon_k": k,
                "n_eligible": n, "n_trans": n_trans,
                "hit_rate": rate, "band_label": band,
                "is_shock_comparator": model == "R-SHOCK",
            })
    return rows


def run_length_mae(
    symbol: str,
    clock: str,
    model: str,
    state: np.ndarray,
    run_len: np.ndarray,
    is_origin: np.ndarray,
) -> dict:
    """Predicted E[run_len] ≈ remaining under geometric from empirical P(stay)."""
    m = is_origin & (state >= 0) & np.isfinite(run_len)
    if m.sum() < 30:
        return {
            "symbol": symbol, "clock": clock, "model": model,
            "metric": "run_len_mae", "mae": float("nan"), "n": int(m.sum()),
            "band_label": "UNPOWERED",
        }
    # empirical P(stay) from consecutive pairs
    s = state
    stay = []
    for i in range(len(s) - 1):
        if s[i] >= 0 and s[i + 1] >= 0:
            stay.append(1.0 if s[i] == s[i + 1] else 0.0)
    p_stay = float(np.mean(stay)) if stay else 0.9
    # E[remaining] under geometric, censored mental model: p_stay/(1-p_stay) capped
    e_run = min(48.0, p_stay / max(1e-6, 1.0 - p_stay))
    mae = float(np.mean(np.abs(run_len[m] - e_run)))
    return {
        "symbol": symbol, "clock": clock, "model": model,
        "metric": "run_len_mae", "mae": mae, "n": int(m.sum()),
        "e_run_pred": e_run, "mean_actual": float(np.mean(run_len[m])),
        "p_stay": p_stay, "band_label": "DISCLOSURE",
    }


def evaluate_symbol_clock(
    symbol: str,
    clock: str,
    df,  # polars
) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """Full 2a evaluation for one symbol×clock.

    Returns (metric rows, trans rows, run rows, derangement-collapse rows).
    """
    import polars as pl

    if df.height == 0:
        return [], [], [], []

    cols = {c: df[c].to_numpy() for c in df.columns}
    is_origin = cols["is_origin"]
    dates = cols["target_date"]
    slot_end = cols["slot_end"]
    next_abs_oo = cols["next_abs_oo"]

    metric_rows: list[dict] = []
    trans_rows: list[dict] = []
    run_rows: list[dict] = []
    derange_rows: list[dict] = []

    model_state = {
        "R-MARKOV": cols["s_markov"],
        "R-HMM-RV": cols["s_hmm_rv"],
        "R-SHOCK": cols["s_shock"],
    }
    model_run = {
        "R-MARKOV": cols["run_len_markov"],
        "R-HMM-RV": cols["run_len_hmm"],
        "R-SHOCK": np.full(df.height, np.nan),
    }

    for model, state in model_state.items():
        X = _feature_matrix_for_model(cols, model)
        for k in HORIZONS_K:
            probs = walk_forward_probs(state, X, slot_end, is_origin, k)
            y = probs["y"]
            p_pers = probs["persistence"]
            for method in ("persistence", "empirical_p", "logistic_ridge"):
                p = probs[method]
                row = metrics_row(
                    symbol, clock, model, method, k,
                    y, p, p_pers, is_origin, dates, state,
                    next_abs_oo=next_abs_oo if model != "R-SHOCK" else None,
                )
                metric_rows.append(row)

                # LABEL-SHUFFLE derangement collapse on powered level-regime cells (design §4).
                if (
                    model in DERANGE_MODELS_2A
                    and method in DERANGE_METHODS_2A
                    and row["band_label"] != "UNPOWERED"
                ):
                    mm = is_origin & np.isfinite(p) & (y >= 0) & (state >= 0)
                    col = label_derange_collapse(y[mm], p[mm], DERANGE_SEEDS)
                    col.update({
                        "arm": "2a", "symbol": symbol, "clock": clock,
                        "model": model, "method": method, "horizon_k": k,
                    })
                    derange_rows.append(col)
        trans_rows.extend(transition_metric_rows(symbol, clock, model, state, is_origin, dates))
        if model != "R-SHOCK":
            run_rows.append(run_length_mae(
                symbol, clock, model, state, model_run[model], is_origin
            ))

    return metric_rows, trans_rows, run_rows, derange_rows
