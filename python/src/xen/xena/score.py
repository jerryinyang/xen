"""XENA intensive turnover-edge score (INFR-009 / consolidated-03 §3; INFR-022 gross-only).

Binding search / rank / fold statistic:

    g_gross(S, W) = 1e4 · Σ_{ℓ∈A(S,W)} PnL_gross_ℓ  /  Σ_{ℓ∈A(S,W)} |notional_entry_ℓ|

where A(S,W) is the set of trades **admitted by the full oracle** for subset S on
window W, and notional_entry = Units · EntryPrice · money_per_unit.

This is an *intensive* ratio: adding more equal-quality trades does not raise the
score by itself (unlike log-wealth F, which scales with trade count × leverage ×
compounding — audit A1/A2/B1). Used identically in search, folds, and (post-CAL)
TEST.

INFR-022 (zero-cost model): the NET score path (``NetMoney`` numerator) is **removed** —
no cost enters any calculation programme-wide. ``g_gross`` is the only score; legacy CAL
``g_net`` reads are retired (bannered CAL apparatus must run gross).

Bootstrap: common-block resampling of the universe bar grid, summing per-bar
gross P&L and |notional| then forming the ratio — same common-index machinery as the
retired extensive bootstrap, different scalar.
"""
from __future__ import annotations

from typing import Mapping

import numpy as np
import polars as pl

from xen.xena.oracle import CandidateStream, OracleResult

# Denominator floor: empty / near-zero notional → score undefined (treated as -inf
# for ranking, never a silent zero that looks like "flat edge").
_NOTIONAL_EPS = 1e-12


def money_per_unit_map(streams: list[CandidateStream]) -> dict[str, float]:
    """candidate_id → money_per_unit from the live stream list."""
    return {s.candidate_id: float(s.money_per_unit) for s in streams}


def entry_notional(units: np.ndarray, entry_price: np.ndarray,
                   money_per_unit: np.ndarray) -> np.ndarray:
    """|notional_entry| = |Units · EntryPrice · money_per_unit|."""
    return np.abs(units * entry_price * money_per_unit)


def g_gross_from_ledger(ledger: pl.DataFrame,
                        mpu_by_cid: Mapping[str, float]) -> float:
    """Point intensive edge (bps of entry notional) from an oracle ledger.

    Parameters
    ----------
    ledger : polars DataFrame with GrossMoney, Units, EntryPrice, CandidateId.
    mpu_by_cid : per-candidate money_per_unit.

    Returns
    -------
    float
        Intensive bps; ``-inf`` when no admitted notional. Gross only (INFR-022).
    """
    if ledger is None or ledger.height == 0:
        return float("-inf")
    units = ledger.get_column("Units").to_numpy().astype(float)
    ep = ledger.get_column("EntryPrice").to_numpy().astype(float)
    cids = ledger.get_column("CandidateId").to_list()
    mpu = np.array([float(mpu_by_cid.get(c, 1.0)) for c in cids], dtype=float)
    notional = entry_notional(units, ep, mpu)
    denom = float(notional.sum())
    if denom <= _NOTIONAL_EPS:
        return float("-inf")
    numer = float(ledger.get_column("GrossMoney").sum())
    return 1e4 * numer / denom


def g_gross_point(result: OracleResult, streams: list[CandidateStream]) -> float:
    """Point g_gross from an ``OracleResult`` (gross only, INFR-022)."""
    return g_gross_from_ledger(result.ledger, money_per_unit_map(streams))


def mean_per_leg_bps(result: OracleResult, streams: list[CandidateStream]) -> float:
    """Mean per-admitted-leg intensive bps (INFR-009 P-BF frozen TEST functional).

    For each admitted leg ℓ: ``bps_ℓ = 1e4 · PnL_ℓ / |notional_entry_ℓ|``.
    Returns the unweighted mean over legs (light form (a)). Undefined (-inf) if no
    finite-notional legs. Ratio g_gross remains a companion disclosure only under P-BF.
    """
    pnl, notional, _et = ledger_leg_arrays(result, streams)
    if len(pnl) == 0:
        return float("-inf")
    ok = notional > _NOTIONAL_EPS
    if not np.any(ok):
        return float("-inf")
    return float(np.mean(1e4 * pnl[ok] / notional[ok]))


def grid_gross_notional(result: OracleResult, streams: list[CandidateStream],
                        grid: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Bin admitted-trade GrossMoney and |notional| onto the bar grid.

    Returns
    -------
    pnl_per_bar, notional_per_bar : ndarray shape (len(grid),)
        Zero-filled; used by the common-block bootstrap of g_gross.
    """
    n = len(grid)
    pnl = np.zeros(n, dtype=float)
    notional = np.zeros(n, dtype=float)
    led = result.ledger
    if led is None or led.height == 0:
        return pnl, notional
    mpu_map = money_per_unit_map(streams)
    et = led.get_column("EntryTime").to_numpy().astype(np.int64)
    g = led.get_column("GrossMoney").to_numpy().astype(float)
    units = led.get_column("Units").to_numpy().astype(float)
    ep = led.get_column("EntryPrice").to_numpy().astype(float)
    cids = led.get_column("CandidateId").to_list()
    mpu = np.array([float(mpu_map.get(c, 1.0)) for c in cids], dtype=float)
    abs_n = entry_notional(units, ep, mpu)
    # same binning contract as search.grid_increments: first grid bar with CloseTime >= t
    idx = np.searchsorted(grid, et, side="left")
    valid = (idx >= 0) & (idx < n)
    np.add.at(pnl, idx[valid], g[valid])
    np.add.at(notional, idx[valid], abs_n[valid])
    return pnl, notional


def bootstrap_g_gross(gross_per_bar: np.ndarray, notional_per_bar: np.ndarray,
                      starts: np.ndarray, *, block: int) -> np.ndarray:
    """Block-bootstrap the intensive ratio on the common bar grid.

    Parameters
    ----------
    gross_per_bar, notional_per_bar : per-bar series (same length, common grid).
    starts : (n_boot, n_blocks) common block-start matrix from ``bootstrap_block_starts``.
    block : nominal block length in bars.

    Returns
    -------
    ndarray shape (n_boot,)
        g_gross per resample (bps). Empty-denominator resamples → -inf.
    """
    n = len(gross_per_bar)
    if n != len(notional_per_bar):
        raise ValueError("gross/notional series length mismatch")
    if n < 2:
        return np.full(starts.shape[0], float("-inf"))
    eff_block = max(1, min(int(block), n - 1))
    n_boot, n_blocks = starts.shape
    g_dbl = np.concatenate([gross_per_bar, gross_per_bar])
    n_dbl = np.concatenate([notional_per_bar, notional_per_bar])
    g_csum = np.concatenate([[0.0], np.cumsum(g_dbl)])
    n_csum = np.concatenate([[0.0], np.cumsum(n_dbl)])
    g_blocks = g_csum[starts + eff_block] - g_csum[starts]
    n_blocks_sum = n_csum[starts + eff_block] - n_csum[starts]
    tail = n - eff_block * (n_blocks - 1)
    if tail != eff_block:
        last = starts[:, -1]
        g_blocks[:, -1] = g_csum[last + tail] - g_csum[last]
        n_blocks_sum[:, -1] = n_csum[last + tail] - n_csum[last]
    g_tot = g_blocks.sum(axis=1)
    n_tot = n_blocks_sum.sum(axis=1)
    out = np.full(n_boot, float("-inf"))
    ok = n_tot > _NOTIONAL_EPS
    out[ok] = 1e4 * g_tot[ok] / n_tot[ok]
    return out


def robust_g_hat(result: OracleResult, streams: list[CandidateStream], grid: np.ndarray,
                 starts: np.ndarray, *, block: int, quantile: float = 0.25
                 ) -> tuple[float, float, np.ndarray]:
    """Quantile of block-bootstrapped g_gross + point intensive edge.

    Returns
    -------
    g_hat, g_point, boot
        Robust score, point intensive edge, full bootstrap vector.
    """
    g_bar, n_bar = grid_gross_notional(result, streams, grid)
    boot = bootstrap_g_gross(g_bar, n_bar, starts, block=block)
    finite = boot[np.isfinite(boot)]
    if len(finite) == 0:
        g_hat = float("-inf")
    else:
        g_hat = float(np.quantile(finite, quantile))
    g_point = g_gross_point(result, streams)
    return g_hat, g_point, boot


def effective_n_diagnostics(result: OracleResult, streams: list[CandidateStream],
                            grid: np.ndarray, *, block: int) -> dict:
    """n_legs, nonempty-block count, empty-bar fraction (P3b A1 diagnostics)."""
    led = result.ledger
    n_legs = int(led.height) if led is not None else 0
    pnl, notional = grid_gross_notional(result, streams, grid)
    n_bars = len(notional)
    nonempty_bars = int(np.sum(notional > _NOTIONAL_EPS))
    empty_bar_fraction = (1.0 - nonempty_bars / n_bars) if n_bars else 1.0
    eff_block = max(1, min(int(block), max(n_bars - 1, 1)))
    # Non-overlapping block windows with any notional mass
    n_nonempty_blocks = 0
    for i0 in range(0, n_bars, eff_block):
        if float(notional[i0:i0 + eff_block].sum()) > _NOTIONAL_EPS:
            n_nonempty_blocks += 1
    return {
        "n_legs": n_legs,
        "n_bars": n_bars,
        "n_nonempty_bars": nonempty_bars,
        "n_nonempty_blocks": int(n_nonempty_blocks),
        "empty_bar_fraction": float(empty_bar_fraction),
        "block": int(block),
        "eff_block": int(eff_block),
    }


def lcb_g(result: OracleResult, streams: list[CandidateStream], grid: np.ndarray,
          starts: np.ndarray, *, block: int, confidence: float = 0.95) -> dict:
    """One-sided LCB via **raw Efron percentile** (P3 baseline — undercovers at low n).

    Prefer :func:`lcb_g_studentized` for P3b+ binders. Gross only (INFR-022).
    """
    if not (0.0 < confidence < 1.0):
        raise ValueError("confidence must be in (0, 1)")
    q = 1.0 - confidence
    g_hat, g_point, boot = robust_g_hat(
        result, streams, grid, starts, block=block, quantile=q)
    finite = boot[np.isfinite(boot)]
    diag = effective_n_diagnostics(result, streams, grid, block=block)
    return {
        "lcb": g_hat,
        "point": g_point,
        "boot_median": float(np.median(finite)) if len(finite) else float("nan"),
        "n_boot_finite": int(len(finite)),
        "pass_positive": bool(np.isfinite(g_hat) and g_hat > 0.0),
        "confidence": float(confidence),
        "block": int(block),
        "score_kind": "g_gross",
        "method": "percentile",
        "binder_form": "LCB>0 percentile (P3 baseline); prefer studentized for P3b",
        **diag,
    }


def ledger_leg_arrays(result: OracleResult, streams: list[CandidateStream]
                      ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per-leg (pnl, |notional|, entry_time) for leg/event bootstrap (P3d). Gross only.

    Returns
    -------
    pnl, notional, entry_times
        Sorted by entry time. Empty arrays if no ledger.
    """
    led = result.ledger
    if led is None or led.height == 0:
        return (np.zeros(0), np.zeros(0), np.zeros(0, dtype=np.int64))
    mpu_map = money_per_unit_map(streams)
    et = led.get_column("EntryTime").to_numpy().astype(np.int64)
    pnl = led.get_column("GrossMoney").to_numpy().astype(float)
    units = led.get_column("Units").to_numpy().astype(float)
    ep = led.get_column("EntryPrice").to_numpy().astype(float)
    cids = led.get_column("CandidateId").to_list()
    mpu = np.array([float(mpu_map.get(c, 1.0)) for c in cids], dtype=float)
    notional = entry_notional(units, ep, mpu)
    order = np.argsort(et, kind="mergesort")
    return pnl[order], notional[order], et[order]


def bootstrap_g_legs(pnl: np.ndarray, notional: np.ndarray, *, n_boot: int,
                     seed: int, block_legs: int = 1) -> np.ndarray:
    """Bootstrap intensive ratio by resampling **legs** (not calendar bars).

    ``block_legs=1``: IID with-replacement over legs.
    ``block_legs>1``: circular block bootstrap over time-ordered legs.
    """
    n = len(pnl)
    if n == 0:
        return np.full(n_boot, float("-inf"))
    rng = np.random.default_rng(seed)
    out = np.full(n_boot, float("-inf"))
    bl = max(1, min(int(block_legs), n))
    if bl == 1:
        idx = rng.integers(0, n, size=(n_boot, n))
    else:
        n_blocks = int(np.ceil(n / bl))
        starts = rng.integers(0, n, size=(n_boot, n_blocks))
        # build (n_boot, n) index matrix of circular blocks
        idx = np.empty((n_boot, n_blocks * bl), dtype=np.int64)
        for b in range(n_blocks):
            for j in range(bl):
                idx[:, b * bl + j] = (starts[:, b] + j) % n
        idx = idx[:, :n]
    g = pnl[idx].sum(axis=1)
    d = notional[idx].sum(axis=1)
    ok = d > _NOTIONAL_EPS
    out[ok] = 1e4 * g[ok] / d[ok]
    return out


def lcb_g_leg_studentized(result: OracleResult, streams: list[CandidateStream], *,
                          n_boot: int = 400, seed: int = 0, block_legs: int = 1,
                          confidence: float = 0.95) -> dict:
    """Studentized LCB on g_gross via **leg** bootstrap (P3d mechanistic fix). Gross only.

    Resamples admitted legs (IID or leg-blocks), not sparse calendar bars — addresses
    ~94% empty-bar geometry at high cadence.
    """
    if not (0.0 < confidence < 1.0):
        raise ValueError("confidence must be in (0, 1)")
    pnl, notional, _et = ledger_leg_arrays(result, streams)
    n_legs = int(len(pnl))
    g_point = g_gross_point(result, streams)
    boot = bootstrap_g_legs(pnl, notional, n_boot=n_boot, seed=seed, block_legs=block_legs)
    finite = boot[np.isfinite(boot)]

    if len(finite) < 8 or not np.isfinite(g_point):
        lcb, se, t_crit = float("-inf"), float("nan"), float("nan")
    else:
        se = float(np.std(finite, ddof=1))
        if se < 1e-15:
            lcb, t_crit = float(g_point), 0.0
        else:
            t_star = (finite - g_point) / se
            t_crit = float(np.quantile(t_star, confidence))
            lcb = float(g_point - t_crit * se)

    return {
        "lcb": lcb,
        "point": g_point,
        "se": se if len(finite) >= 8 else float("nan"),
        "t_crit": t_crit if len(finite) >= 8 else float("nan"),
        "boot_median": float(np.median(finite)) if len(finite) else float("nan"),
        "n_boot_finite": int(len(finite)),
        "pass_positive": bool(np.isfinite(lcb) and lcb > 0.0),
        "confidence": float(confidence),
        "n_legs": n_legs,
        "n_nonempty_blocks": n_legs,  # each leg is a unit
        "empty_bar_fraction": float("nan"),  # N/A for leg bootstrap
        "block_legs": int(block_legs),
        "n_boot": int(n_boot),
        "score_kind": "g_gross",
        "method": "leg_studentized_bootstrap_t",
        "resample_unit": "legs",
        "binder_form": "LCB>0 leg-bootstrap studentized (INFR-009 P3d)",
    }


def lcb_g_studentized(result: OracleResult, streams: list[CandidateStream],
                      grid: np.ndarray, starts: np.ndarray, *, block: int,
                      confidence: float = 0.95) -> dict:
    """One-sided **bootstrap-t (studentized)** LCB on intensive g_gross (P3b A1). Gross only.

    ``LCB = ĝ − t*_{1-α} · sê`` with ``t*_b = (g*_b − ĝ) / sê`` and
    ``sê = sample sd of finite bootstrap replicates``. Same common-bar bootstrap path
    as search; interval math only changes. Sample size is reported as context (n_legs,
    nonempty blocks, empty-bar fraction); it never vetoes a read (INFR-022 L-63).
    """
    if not (0.0 < confidence < 1.0):
        raise ValueError("confidence must be in (0, 1)")
    g_bar, n_bar = grid_gross_notional(result, streams, grid)
    boot = bootstrap_g_gross(g_bar, n_bar, starts, block=block)
    finite = boot[np.isfinite(boot)]
    g_point = g_gross_point(result, streams)
    diag = effective_n_diagnostics(result, streams, grid, block=block)

    if len(finite) < 8 or not np.isfinite(g_point):
        lcb = float("-inf")
        se = float("nan")
        t_crit = float("nan")
    else:
        se = float(np.std(finite, ddof=1))
        if se < 1e-15:
            # degenerate: all replicates identical — LCB = point (no evidence of >0 unless point>0)
            lcb = float(g_point)
            t_crit = 0.0
        else:
            t_star = (finite - g_point) / se
            t_crit = float(np.quantile(t_star, confidence))  # 1-α quantile for lower LCB
            lcb = float(g_point - t_crit * se)

    out = {
        "lcb": lcb,
        "point": g_point,
        "se": se if len(finite) >= 8 else float("nan"),
        "t_crit": t_crit if len(finite) >= 8 else float("nan"),
        "boot_median": float(np.median(finite)) if len(finite) else float("nan"),
        "n_boot_finite": int(len(finite)),
        "pass_positive": bool(np.isfinite(lcb) and lcb > 0.0),
        "confidence": float(confidence),
        "block": int(block),
        "score_kind": "g_gross",
        "method": "studentized_bootstrap_t",
        "binder_form": "LCB>0 studentized (INFR-009 P3b A1); not extensive-F",
        **diag,
    }
    return out
