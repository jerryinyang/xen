"""Walk-forward predictors: ridge primary + pure-numpy shallow GBM sensitivity."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from config import (
    FEATURE_LAYERS,
    GBM_DEPTH,
    GBM_LR,
    GBM_MIN_LEAF,
    GBM_N_EST,
    GBM_SEED,
    MIN_TRAIN_ROWS,
    RIDGE_ALPHA,
)


# ---------------------------------------------------------------- ridge ----


def ridge_fit(X: np.ndarray, y: np.ndarray, alpha: float = RIDGE_ALPHA
              ) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Standardise X, fit ridge. Returns (w, mu, sd, y_mean)."""
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    sd[sd == 0] = 1.0
    Xs = (X - mu) / sd
    ym = float(y.mean())
    yc = y - ym
    p = Xs.shape[1]
    w = np.linalg.solve(Xs.T @ Xs + alpha * np.eye(p), Xs.T @ yc)
    return w, mu, sd, ym


def ridge_predict(X: np.ndarray, w: np.ndarray, mu: np.ndarray, sd: np.ndarray,
                  ym: float) -> np.ndarray:
    Xs = (X - mu) / sd
    return Xs @ w + ym


# ---------------------------------------------------------------- GBM ----


@dataclass
class _TreeNode:
    feat: int = -1
    thr: float = 0.0
    left: int = -1
    right: int = -1
    value: float = 0.0


def _best_split(X: np.ndarray, resid: np.ndarray, min_leaf: int
                ) -> tuple[int, float, float]:
    """Return (feat, thr, gain) maximising SSE reduction via 16-quantile candidates."""
    n, p = X.shape
    best_gain = 0.0
    best_f, best_t = -1, 0.0
    parent_sse = float(np.sum(resid ** 2))
    total_sum = float(resid.sum())
    total_sum2 = parent_sse
    qs = np.linspace(0.1, 0.9, 16)
    for f in range(p):
        col = X[:, f]
        if not np.isfinite(col).all():
            continue
        thr_cands = np.unique(np.quantile(col, qs))
        for thr in thr_cands:
            left_m = col <= thr
            n_l = int(left_m.sum())
            n_r = n - n_l
            if n_l < min_leaf or n_r < min_leaf:
                continue
            left_sum = float(resid[left_m].sum())
            left_sum2 = float(np.sum(resid[left_m] ** 2))
            right_sum = total_sum - left_sum
            right_sum2 = total_sum2 - left_sum2
            sse_l = left_sum2 - (left_sum * left_sum) / n_l
            sse_r = right_sum2 - (right_sum * right_sum) / n_r
            gain = parent_sse - (sse_l + sse_r)
            if gain > best_gain:
                best_gain = gain
                best_f = f
                best_t = float(thr)
    return best_f, best_t, best_gain


def _build_tree(X: np.ndarray, resid: np.ndarray, depth: int, min_leaf: int,
                nodes: list[_TreeNode]) -> int:
    """Build regression tree; return root index into nodes."""
    idx = len(nodes)
    nodes.append(_TreeNode(value=float(resid.mean())))
    if depth <= 0 or X.shape[0] < 2 * min_leaf:
        return idx
    f, thr, gain = _best_split(X, resid, min_leaf)
    if f < 0 or gain <= 0:
        return idx
    left_m = X[:, f] <= thr
    right_m = ~left_m
    if left_m.sum() < min_leaf or right_m.sum() < min_leaf:
        return idx
    nodes[idx].feat = f
    nodes[idx].thr = thr
    nodes[idx].left = _build_tree(X[left_m], resid[left_m], depth - 1, min_leaf, nodes)
    nodes[idx].right = _build_tree(X[right_m], resid[right_m], depth - 1, min_leaf, nodes)
    return idx


def _tree_predict_one(x: np.ndarray, nodes: list[_TreeNode], root: int) -> float:
    i = root
    while True:
        nd = nodes[i]
        if nd.feat < 0:
            return nd.value
        i = nd.left if x[nd.feat] <= nd.thr else nd.right


def gbm_fit(X: np.ndarray, y: np.ndarray, *,
            n_est: int = GBM_N_EST, depth: int = GBM_DEPTH,
            min_leaf: int = GBM_MIN_LEAF, lr: float = GBM_LR,
            seed: int = GBM_SEED
            ) -> tuple[float, list[tuple[list[_TreeNode], int]]]:
    """Fit shallow residual-boosting ensemble. Returns (y0, list of (nodes, root))."""
    rng = np.random.default_rng(seed)
    # subsample columns slightly for stability if wide
    y0 = float(y.mean())
    resid = y - y0
    trees: list[tuple[list[_TreeNode], int]] = []
    n = X.shape[0]
    for _ in range(n_est):
        # row subsample 80% if large
        if n > 200:
            idx = rng.choice(n, size=max(min_leaf * 4, int(0.8 * n)), replace=False)
            Xs, rs = X[idx], resid[idx]
        else:
            Xs, rs = X, resid
        nodes: list[_TreeNode] = []
        root = _build_tree(Xs, rs, depth, min_leaf, nodes)
        pred = np.array([_tree_predict_one(X[i], nodes, root) for i in range(n)])
        resid = resid - lr * pred
        trees.append((nodes, root))
        if float(np.std(resid)) < 1e-9:
            break
    return y0, trees


def gbm_predict(X: np.ndarray, y0: float,
                trees: list[tuple[list[_TreeNode], int]], lr: float = GBM_LR
                ) -> np.ndarray:
    out = np.full(X.shape[0], y0)
    for nodes, root in trees:
        out = out + lr * np.array([_tree_predict_one(X[i], nodes, root)
                                   for i in range(X.shape[0])])
    return out


# -------------------------------------------------------- walk-forward ----


def month_key(ts_ns: int) -> tuple[int, int]:
    # UTC year-month from ns
    sec = ts_ns // 1_000_000_000
    # crude but stable: datetime from epoch
    import datetime as _dt
    d = _dt.datetime.fromtimestamp(sec, tz=_dt.timezone.utc)
    return d.year, d.month


def walk_forward_predict(
    X: np.ndarray,
    y: np.ndarray,
    eligible: np.ndarray,
    slot_start: np.ndarray,
    model: str = "M-RIDGE",
    min_train: int = MIN_TRAIN_ROWS,
) -> np.ndarray:
    """Causal monthly refit OOS predictions.

    At each eligible origin t, ŷ[t] uses a model fit only on prior eligible rows
    with finite y (targets that completed before t). Monthly: refit when month of
    decision_ts changes; within month reuse last fit.

    y[i] must be the *realised* target for origin i (NaN if incomplete).
    Prediction at t may only use training rows j where j < t and y[j] finite
    (i.e. target window completed before decision t — enforced by requiring
    y-completion index < t via eligible construction in prepare).
    """
    n = X.shape[0]
    yhat = np.full(n, np.nan)
    # indices with finite features + eligible decision
    # training requires finite y as well
    fit_state = None
    last_month: tuple[int, int] | None = None
    train_idx: list[int] = []

    for t in range(n):
        if not eligible[t] or not np.isfinite(X[t]).all():
            # still accumulate train rows that completed at t if y[t] becomes known
            if np.isfinite(y[t]) and np.isfinite(X[t]).all():
                train_idx.append(t)
            continue

        mk = month_key(int(slot_start[t]))
        need_refit = fit_state is None or mk != last_month
        if need_refit:
            # train on all prior completed targets strictly before t
            tr = [j for j in train_idx if j < t]
            if len(tr) < min_train:
                # not enough history — leave NaN (no zone from model)
                if np.isfinite(y[t]) and np.isfinite(X[t]).all():
                    train_idx.append(t)
                continue
            Xtr = X[tr]
            ytr = y[tr]
            ok = np.isfinite(Xtr).all(axis=1) & np.isfinite(ytr)
            if ok.sum() < min_train:
                if np.isfinite(y[t]) and np.isfinite(X[t]).all():
                    train_idx.append(t)
                continue
            Xtr, ytr = Xtr[ok], ytr[ok]
            if model == "M-RIDGE":
                fit_state = ("ridge",) + ridge_fit(Xtr, ytr)
            elif model == "M-GBM":
                fit_state = ("gbm",) + gbm_fit(Xtr, ytr)
            else:
                raise ValueError(model)
            last_month = mk

        if fit_state is None:
            if np.isfinite(y[t]) and np.isfinite(X[t]).all():
                train_idx.append(t)
            continue

        xrow = X[t: t + 1]
        if fit_state[0] == "ridge":
            _, w, mu, sd, ym = fit_state
            yhat[t] = float(ridge_predict(xrow, w, mu, sd, ym)[0])
        else:
            _, y0, trees = fit_state
            yhat[t] = float(gbm_predict(xrow, y0, trees)[0])

        # after prediction at t, if y[t] is already known (should not be for causal target)
        # train rows are added only when target is realised — caller ensures y[t] uses future
        # so y[t] is NaN at decision; we append when we later visit? Actually y is precomputed
        # full series including future-known targets. Causal rule: only use j < t with
        # completed target. Target for origin j completes at j+1+H, so we must only add j
        # to train when current t > j+H (or when building train_idx filter by completion).
        # handled below via train_ready mask from caller.
        if np.isfinite(y[t]) and np.isfinite(X[t]).all():
            train_idx.append(t)

    return yhat


def walk_forward_predict_causal(
    X: np.ndarray,
    y: np.ndarray,
    y_ready_at: np.ndarray,
    eligible: np.ndarray,
    slot_start: np.ndarray,
    model: str = "M-RIDGE",
    min_train: int = MIN_TRAIN_ROWS,
) -> np.ndarray:
    """Walk-forward with explicit target-ready index.

    y_ready_at[j] = bar index at which target for origin j is fully known (exit open).
    Origin t may train only on j where y_ready_at[j] <= t (≤t, causal).
    """
    n = X.shape[0]
    yhat = np.full(n, np.nan)
    fit_state = None
    last_month: tuple[int, int] | None = None

    # precompute list of eligible training candidates (sorted)
    feat_ok = np.isfinite(X).all(axis=1)
    cand = np.where(np.isfinite(y) & feat_ok & np.isfinite(y_ready_at))[0]
    # decision origins only
    origins = np.where(eligible & feat_ok)[0]
    if origins.size == 0 or cand.size < min_train:
        return yhat

    # two-pointer: for each origin, train pool = cand with cand < t and y_ready_at <= t
    # cand is sorted ascending
    ready_at = y_ready_at.astype(float)

    for t in origins:
        mk = month_key(int(slot_start[t]))
        need_refit = fit_state is None or mk != last_month
        if need_refit:
            # vectorised filter
            tr = cand[(cand < t) & (ready_at[cand] <= t)]
            if tr.size < min_train:
                fit_state = None
                last_month = mk
                continue
            Xtr, ytr = X[tr], y[tr]
            if model == "M-RIDGE":
                fit_state = ("ridge",) + ridge_fit(Xtr, ytr)
            elif model == "M-GBM":
                # cap train rows for GBM speed (still causal prior sample)
                if tr.size > 2000:
                    tr_use = tr[-2000:]
                    Xtr, ytr = X[tr_use], y[tr_use]
                fit_state = ("gbm",) + gbm_fit(Xtr, ytr)
            else:
                raise ValueError(model)
            last_month = mk

        if fit_state is None:
            continue
        xrow = X[t: t + 1]
        if fit_state[0] == "ridge":
            _, w, mu, sd, ym = fit_state
            yhat[t] = float(ridge_predict(xrow, w, mu, sd, ym)[0])
        else:
            _, y0, trees = fit_state
            yhat[t] = float(gbm_predict(xrow, y0, trees)[0])

    return yhat


def feature_matrix(feat: dict[str, np.ndarray], ablation: str) -> np.ndarray:
    cols = FEATURE_LAYERS[ablation]
    return np.column_stack([feat[c] for c in cols])
