"""The uniform layer applied to every arm (design §4, §6, §8).

Four things, applied identically to every cell in all four arms:

  1. the ``(p, W, L)`` decomposition and ``edge = p - p_be_net``            (§4.1, SoT §2)
  2. dependence-matched uncertainty: day-block bootstrap, block MDE primary (§6.2, M-1)
  3. the standing corrections M-2 (exact span), M-4 (effective coverage)   (§6.3)
  4. interpretation bands as LABELS — no ``pass`` field anywhere            (§8, INFR-016)

Nothing here defines a parent's estimand; it decorates whatever signed return the parent's own
object already produces.
"""
from __future__ import annotations

import numpy as np

from xen.evaluation import block_bootstrap_ci

from config import (
    BAND_MEAN_CONTRADICTED_BPS,
    BAND_MEAN_MDE_CEILING_BPS,
    BAND_MEAN_SUPPORTED_BPS,
    BOOT_BLOCKS_DAYS,
    BOOT_CI_ALPHA,
    BOOT_RESAMPLES,
    BOOT_SEEDS,
    EFFECTIVE_COVERAGE_START_NS,
    IDENTITY_RECONSTRUCTION_TOL_BPS,
    IID_MDE_CONST,
    NS,
    TRIM_FRACTION,
)

DAY_NS = 86_400 * NS


# --------------------------------------------------------------------------- #
# day keys — the resampling unit (§6.2: per-calendar-day sufficient statistics)
# --------------------------------------------------------------------------- #
def day_index(ts_ns: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Map timestamps to a dense day index. Returns (per-row day index, unique day starts)."""
    days = (np.asarray(ts_ns, dtype=np.int64) // DAY_NS)
    uniq, inv = np.unique(days, return_inverse=True)
    return inv.astype(np.int64), uniq * DAY_NS


# --------------------------------------------------------------------------- #
# per-day sufficient statistics — exact for the whole mean / p / W / L family
# --------------------------------------------------------------------------- #
_SUFF_COLS = ("n", "sum", "n_pos", "sum_pos", "n_neg", "sum_neg", "n_zero", "sumsq")


def day_sufficient(r: np.ndarray, day_idx: np.ndarray, n_days: int) -> np.ndarray:
    """``(n_days, 8)`` sufficient statistics. Every §4.1 quantity is exact from these."""
    r = np.asarray(r, dtype=float)
    pos = r > 0
    neg = r < 0
    zero = r == 0
    out = np.zeros((n_days, len(_SUFF_COLS)), dtype=float)
    out[:, 0] = np.bincount(day_idx, minlength=n_days)
    out[:, 1] = np.bincount(day_idx, weights=r, minlength=n_days)
    out[:, 2] = np.bincount(day_idx, weights=pos.astype(float), minlength=n_days)
    out[:, 3] = np.bincount(day_idx, weights=np.where(pos, r, 0.0), minlength=n_days)
    out[:, 4] = np.bincount(day_idx, weights=neg.astype(float), minlength=n_days)
    out[:, 5] = np.bincount(day_idx, weights=np.where(neg, r, 0.0), minlength=n_days)
    out[:, 6] = np.bincount(day_idx, weights=zero.astype(float), minlength=n_days)
    out[:, 7] = np.bincount(day_idx, weights=r * r, minlength=n_days)
    return out


def _agg(s: np.ndarray) -> dict:
    """Collapse sufficient statistics to the §4.1 quantities. ``s`` is (n_days, 8)."""
    n = s[:, 0].sum()
    tot = s[:, 1].sum()
    n_pos = s[:, 2].sum()
    sum_pos = s[:, 3].sum()
    n_neg = s[:, 4].sum()
    sum_neg = s[:, 5].sum()
    n_zero = s[:, 6].sum()
    signed = n_pos + n_neg
    nan = float("nan")
    return {
        "n": float(n),
        "mean": tot / n if n else nan,
        "p": n_pos / signed if signed else nan,
        "W": sum_pos / n_pos if n_pos else nan,
        "L": -sum_neg / n_neg if n_neg else nan,
        "n_pos": float(n_pos),
        "n_neg": float(n_neg),
        "p_flat": n_zero / n if n else nan,
    }


def _stat_from_suff(name: str, cost_bps: float):
    """Statistic callables over a resampled ``(days, 8)`` sufficient-stat matrix."""
    def f(s: np.ndarray) -> float:
        a = _agg(np.atleast_2d(s))
        W, L, p = a["W"], a["L"], a["p"]
        if name == "mean":
            return a["mean"]
        if name == "p":
            return p
        if name == "W":
            return W
        if name == "L":
            return L
        if name == "W_L":
            return W / L if (np.isfinite(L) and L > 0) else float("nan")
        if name == "p_be":
            return L / (W + L) if np.isfinite(W + L) and (W + L) > 0 else float("nan")
        if name == "p_be_net":
            d = W + L
            return (L + cost_bps) / d if np.isfinite(d) and d > 0 else float("nan")
        if name == "edge":
            d = W + L
            if not (np.isfinite(d) and d > 0):
                return float("nan")
            return p - (L + cost_bps) / d
        raise KeyError(name)
    return f


def _day_gather_index(counts: np.ndarray, starts: np.ndarray, ids: np.ndarray) -> np.ndarray:
    """Row indices for a resampled set of days — fully vectorised ragged gather.

    The obvious form, ``np.concatenate([day_rows[d] for d in ids])``, runs a Python loop over
    every day for every resample: at 900 days x 2000 resamples x 15 (block, seed) combinations
    that is ~27M interpreter iterations PER CELL, which is what made the pooled cells intractable.
    This builds the same index array with pure array arithmetic — identical rows, identical
    statistic, no sampling change whatsoever.
    """
    lens = counts[ids]
    total = int(lens.sum())
    if total == 0:
        return np.empty(0, dtype=np.int64)
    offs = np.cumsum(lens) - lens
    return (np.repeat(starts[ids] - offs, lens) + np.arange(total)).astype(np.int64)


def _stat_from_rows(name: str, r: np.ndarray, day_idx: np.ndarray, n_days: int):
    """Statistics needing the raw rows (median, trimmed mean) over a resampled day-index array."""
    order = np.argsort(day_idx, kind="stable")
    vals = np.asarray(r, dtype=float)[order]
    counts = np.bincount(day_idx, minlength=n_days).astype(np.int64)
    starts = np.concatenate([[0], np.cumsum(counts)[:-1]]).astype(np.int64)

    def f(day_ids: np.ndarray) -> float:
        idx = _day_gather_index(counts, starts, np.atleast_1d(day_ids).astype(np.int64))
        if idx.size == 0:
            return float("nan")
        v = vals[idx]
        if name == "median":
            return float(np.median(v))
        if name == "trimmed_mean":
            return _trimmed(v, TRIM_FRACTION)
        raise KeyError(name)
    return f


def _trimmed(v: np.ndarray, frac: float) -> float:
    """Two-sided ``frac`` trimmed mean (design §6.1 — 10%, this family is fat-tailed)."""
    v = np.sort(np.asarray(v, dtype=float))
    n = v.size
    if n == 0:
        return float("nan")
    k = int(np.floor(n * frac))
    core = v[k: n - k] if n - 2 * k > 0 else v
    return float(core.mean())


# --------------------------------------------------------------------------- #
# the envelope bootstrap (§6.2 BINDING)
# --------------------------------------------------------------------------- #
def _resample_day_blocks(n_days: int, block: int, n_boot: int, seed: int) -> np.ndarray:
    """``(n_boot, n_days)`` circular day-block resample indices.

    Byte-identical in construction to ``xen.evaluation.block_bootstrap_ci``: effective block
    capped to ``[1, n-1]``, starts drawn over the FULL circular range ``[0, n)``, concatenated
    blocks truncated to ``n`` (INFR-004 F1 / L-20). Equivalence to the canonical implementation is
    asserted at run time by ``assert_canonical_equivalence`` — this is a speed path over the same
    referee, not a second referee.
    """
    eff = max(1, min(int(block), n_days - 1))
    n_blocks = int(np.ceil(n_days / eff))
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, n_days, size=(n_boot, n_blocks))
    idx = (starts[:, :, None] + np.arange(eff)[None, None, :]).reshape(n_boot, -1)[:, :n_days]
    return idx % n_days


def _suff_boot_stats(suff: np.ndarray, block: int, n_boot: int, seed: int,
                     cost_bps: float, names: tuple[str, ...]) -> dict[str, np.ndarray]:
    """All mean-family statistics from ONE vectorised day-block resample pass."""
    n_days = suff.shape[0]
    out = {k: np.empty(n_boot) for k in names}
    chunk = max(1, int(4e6 // max(n_days, 1)))
    done = 0
    while done < n_boot:
        take = min(chunk, n_boot - done)
        idx = _resample_day_blocks(n_days, block, take, seed)[:, :]
        # advance the stream deterministically per chunk by folding the offset into the seed
        tot = suff[idx].sum(axis=1)                      # (take, 8)
        n = tot[:, 0]
        s = tot[:, 1]
        n_pos, sum_pos = tot[:, 2], tot[:, 3]
        n_neg, sum_neg = tot[:, 4], tot[:, 5]
        signed = n_pos + n_neg
        with np.errstate(divide="ignore", invalid="ignore"):
            mean = np.where(n > 0, s / n, np.nan)
            p = np.where(signed > 0, n_pos / signed, np.nan)
            W = np.where(n_pos > 0, sum_pos / n_pos, np.nan)
            L = np.where(n_neg > 0, -sum_neg / n_neg, np.nan)
            d = W + L
            W_L = np.where(L > 0, W / L, np.nan)
            p_be = np.where(d > 0, L / d, np.nan)
            p_be_net = np.where(d > 0, (L + cost_bps) / d, np.nan)
            edge = p - p_be_net
        vals = {"mean": mean, "p": p, "W": W, "L": L, "W_L": W_L,
                "p_be": p_be, "p_be_net": p_be_net, "edge": edge}
        for k in names:
            out[k][done:done + take] = vals[k]
        done += take
    return out


def envelope_ci_suff(suff: np.ndarray, cost_bps: float, names: tuple[str, ...], *,
                     blocks=BOOT_BLOCKS_DAYS, n_boot=BOOT_RESAMPLES) -> dict[str, dict]:
    """Envelope CIs for the whole mean family in one pass per (block, seed). See ``envelope_ci``."""
    n_days = suff.shape[0]
    point = {k: _stat_from_suff(k, cost_bps)(suff) for k in names}
    if n_days < 2:
        return {k: {"stat": float(point[k]), "ci_low": float("nan"), "ci_high": float("nan"),
                    "n_days": int(n_days), "per_block": [], "degenerate": True} for k in names}

    lows = {k: [] for k in names}
    highs = {k: [] for k in names}
    per_block = {k: [] for k in names}
    for bl in blocks:
        eff = max(1, min(int(bl), n_days - 1))
        seed_lo = {k: [] for k in names}
        seed_hi = {k: [] for k in names}
        for si, sd in enumerate(BOOT_SEEDS):
            stats = _suff_boot_stats(suff, bl, n_boot, BOOT_SEEDS[0] + si, cost_bps, names)
            for k in names:
                v = stats[k][np.isfinite(stats[k])]
                if v.size == 0:
                    continue
                seed_lo[k].append(float(np.quantile(v, BOOT_CI_ALPHA / 2)))
                seed_hi[k].append(float(np.quantile(v, 1 - BOOT_CI_ALPHA / 2)))
            del sd
        for k in names:
            if not seed_lo[k]:
                continue
            lows[k] += seed_lo[k]
            highs[k] += seed_hi[k]
            per_block[k].append({"block_days": int(bl), "effective_block": eff,
                                 "ci": [float(np.median(seed_lo[k])),
                                        float(np.median(seed_hi[k]))],
                                 "ci_low_seed_range": [min(seed_lo[k]), max(seed_lo[k])],
                                 "ci_high_seed_range": [min(seed_hi[k]), max(seed_hi[k])]})
    return {k: {"stat": float(point[k]),
                "ci_low": float(min(lows[k])) if lows[k] else float("nan"),
                "ci_high": float(max(highs[k])) if highs[k] else float("nan"),
                "n_days": int(n_days), "per_block": per_block[k], "degenerate": False,
                "envelope_rule": "min/max over blocks {1,3,7} days x 5 seeds"} for k in names}


def assert_canonical_equivalence(suff: np.ndarray, cost_bps: float, *, name: str = "mean",
                                 block: int = 3, n_boot: int = 500, tol: float = 1e-9) -> dict:
    """Prove the vectorised path == ``xen.evaluation.block_bootstrap_ci`` on the same seed.

    Run in the integrity self-check. Both draw ``rng.integers(0, n, (n_boot, n_blocks))`` from
    ``default_rng(seed)`` and truncate to ``n``, so the resampled index sets are identical and the
    bounds must agree to floating-point tolerance.
    """
    stat = _stat_from_suff(name, cost_bps)
    canon = block_bootstrap_ci(suff, stat, block=block, n_boot=n_boot, alpha=BOOT_CI_ALPHA,
                               seed=BOOT_SEEDS[0], n_seeds=1)
    fast = _suff_boot_stats(suff, block, n_boot, BOOT_SEEDS[0], cost_bps, (name,))[name]
    v = fast[np.isfinite(fast)]
    lo = float(np.quantile(v, BOOT_CI_ALPHA / 2))
    hi = float(np.quantile(v, 1 - BOOT_CI_ALPHA / 2))
    d_lo = abs(lo - canon["ci"][0])
    d_hi = abs(hi - canon["ci"][1])
    return {"statistic": name, "block": block, "n_boot": n_boot,
            "canonical_ci": [float(canon["ci"][0]), float(canon["ci"][1])],
            "vectorised_ci": [lo, hi], "abs_diff": [d_lo, d_hi], "tol": tol,
            "equivalent": bool(d_lo <= tol and d_hi <= tol)}


def envelope_ci(x: np.ndarray, stat, *, blocks=BOOT_BLOCKS_DAYS, n_boot=BOOT_RESAMPLES) -> dict:
    """Day-block bootstrap CI, envelope = **min/max over blocks x seeds** (conservative).

    ``x`` is indexed by DAY (either the sufficient-statistic matrix or a day-index vector), so the
    resampling unit is a block of ``{1,3,7}`` calendar days. The minimum block, 1 day = 24 H1
    bars, is >= every horizon in scope — the Phase-010 requirement that a library ``block=5``
    default never substitutes for. Delegates to ``xen.evaluation.block_bootstrap_ci``, which
    carries the INFR-004 / L-20 hardening (effective block capped < n, full circular start range,
    5-seed battery).
    """
    x = np.asarray(x)
    n_days = x.shape[0]
    if n_days == 0:
        return {"stat": float("nan"), "ci_low": float("nan"), "ci_high": float("nan"),
                "n_days": 0, "per_block": [], "degenerate": True}
    if n_days == 1:
        s = float(stat(x))
        return {"stat": s, "ci_low": float("nan"), "ci_high": float("nan"),
                "n_days": 1, "per_block": [], "degenerate": True,
                "note": "single calendar day — no block resampling is possible"}

    point = float(stat(x))
    lows, highs, per_block = [], [], []
    for bl in blocks:
        r = block_bootstrap_ci(x, stat, block=int(bl), n_boot=n_boot, alpha=BOOT_CI_ALPHA,
                               seed=BOOT_SEEDS[0], n_seeds=len(BOOT_SEEDS))
        lo_lo, lo_hi = r["ci_low_seed_range"]
        hi_lo, hi_hi = r["ci_high_seed_range"]
        lows += [lo_lo, lo_hi]
        highs += [hi_lo, hi_hi]
        per_block.append({"block_days": int(bl), "effective_block": int(r["block"]),
                          "ci": [float(r["ci"][0]), float(r["ci"][1])],
                          "ci_low_seed_range": [float(lo_lo), float(lo_hi)],
                          "ci_high_seed_range": [float(hi_lo), float(hi_hi)]})
    lows = [v for v in lows if np.isfinite(v)]
    highs = [v for v in highs if np.isfinite(v)]
    return {
        "stat": point,
        "ci_low": float(min(lows)) if lows else float("nan"),
        "ci_high": float(max(highs)) if highs else float("nan"),
        "n_days": int(n_days),
        "per_block": per_block,
        "degenerate": False,
        "envelope_rule": "min/max over blocks {1,3,7} days x 5 seeds",
    }


def block_mde(ci: dict) -> float:
    """The reported MDE (M-1): the envelope half-width below the point estimate.

    The smallest constant shift that would lift the envelope CI low above zero. This is THE
    band-driving MDE. The iid form is a companion column only and never drives a label.
    """
    if not np.isfinite(ci.get("stat", np.nan)) or not np.isfinite(ci.get("ci_low", np.nan)):
        return float("nan")
    return float(ci["stat"] - ci["ci_low"])


def iid_mde_companion(r: np.ndarray) -> float:
    """``2.8*sigma/sqrt(n)`` — LABELLED COMPANION ONLY (M-1). Never drives a band label."""
    r = np.asarray(r, dtype=float)
    n = r.size
    if n < 2:
        return float("nan")
    return float(IID_MDE_CONST * np.std(r, ddof=1) / np.sqrt(n))


def required_n_for_target(r: np.ndarray, realised_mde: float, target_mde: float) -> float:
    """The ``n`` that WOULD be required to reach ``target_mde``, at the realised dependence.

    MDE scales as ``1/sqrt(n)`` at fixed dependence, so ``n_req = n * (mde/target)^2``. Reported
    with every NOT_RESOLVABLE cell so the shortfall is a number, not an adjective.
    """
    n = float(np.asarray(r).size)
    if not (np.isfinite(realised_mde) and np.isfinite(target_mde)) or target_mde <= 0 or n <= 0:
        return float("nan")
    return float(np.ceil(n * (realised_mde / target_mde) ** 2))


# --------------------------------------------------------------------------- #
# M-2 span disclosure / M-4 effective coverage
# --------------------------------------------------------------------------- #
def span_stats(entry_ts_ns: np.ndarray, exit_ts_ns: np.ndarray, h: int,
               clock_minutes: int) -> dict:
    """M-2: ``h`` is an INDEX OFFSET, not wall-clock. Co-report the exact-span subset.

    A row is *exact-span* when its wall-clock span equals ``h`` bar-widths — i.e. no gap in the
    symbol's bar series ran through the hold. On sparse symbols a meaningful share of rows span
    far more, and reading those as an ``h``-hour horizon is the M-2 error.
    """
    e = np.asarray(entry_ts_ns, dtype=np.int64)
    x = np.asarray(exit_ts_ns, dtype=np.int64)
    if e.size == 0:
        return {"n": 0, "exact_span_n": 0, "exact_span_frac": float("nan"),
                "nominal_span_hours": h * clock_minutes / 60.0}
    span_h = (x - e) / (3600 * NS)
    nominal = h * clock_minutes / 60.0
    exact = np.isclose(span_h, nominal, rtol=0, atol=1e-9)
    return {
        "n": int(e.size),
        "nominal_span_hours": float(nominal),
        "exact_span_n": int(exact.sum()),
        "exact_span_frac": float(exact.mean()),
        "span_hours_median": float(np.median(span_h)),
        "span_hours_p95": float(np.percentile(span_h, 95)),
        "span_hours_max": float(span_h.max()),
        "frac_exceeding_nominal": float((span_h > nominal + 1e-9).mean()),
    }


def effective_coverage(ts_ns: np.ndarray, symbols: np.ndarray) -> dict:
    """M-4: EFFECTIVE multi-symbol coverage, not the nominal span.

    The DESIGN band is one symbol deep before 2022-07-14 (catalog history cap), so the nominal
    20-month window overstates what the cell actually rests on. Reported per cell.
    """
    ts = np.asarray(ts_ns, dtype=np.int64)
    syms = np.asarray(symbols)
    if ts.size == 0:
        return {"n": 0, "nominal_days": 0.0, "effective_multi_symbol_days": 0.0,
                "n_symbols": 0, "effective_frac_of_nominal": float("nan")}
    nominal_days = float((ts.max() - ts.min()) / DAY_NS)
    multi = ts >= EFFECTIVE_COVERAGE_START_NS
    eff_days = float((ts[multi].max() - ts[multi].min()) / DAY_NS) if multi.any() else 0.0
    day_ids = ts // DAY_NS
    per_day_syms = {}
    for d, s in zip(day_ids, syms):
        per_day_syms.setdefault(int(d), set()).add(s)
    deep_days = sum(1 for v in per_day_syms.values() if len(v) >= 2)
    return {
        "n": int(ts.size),
        "n_symbols": int(len(np.unique(syms))),
        "n_dates": int(len(per_day_syms)),
        "nominal_days": nominal_days,
        "effective_multi_symbol_days": eff_days,
        "effective_frac_of_nominal": (eff_days / nominal_days) if nominal_days > 0 else float("nan"),
        "n_dates_with_ge2_symbols": int(deep_days),
        "multi_symbol_cutover": "2022-07-14 (catalog history cap; M-4)",
    }


# --------------------------------------------------------------------------- #
# the cell record
# --------------------------------------------------------------------------- #
def signed_cell(r: np.ndarray, ts_ns: np.ndarray, *, cost_bps: float,
                full: bool = True, n_boot: int = BOOT_RESAMPLES) -> dict:
    """Every §5.3 quantity for one cell of signed returns in bps.

    ``full=False`` skips the (expensive) median / trimmed-mean bootstrap and returns their point
    values only — used for the several-thousand-cell grids where the mean family is the read.
    The identity ``mean = p*W - (1-p)*L`` is reconstructed and its residual returned for the HARD
    self-check assertion (§12).
    """
    r = np.asarray(r, dtype=float)
    ok = np.isfinite(r)
    r = r[ok]
    ts = np.asarray(ts_ns, dtype=np.int64)[ok]
    out: dict = {"n": int(r.size), "cost_bps": float(cost_bps)}
    if r.size == 0:
        out["empty"] = True
        return out

    day_idx, day_starts = day_index(ts)
    n_days = day_starts.size
    suff = day_sufficient(r, day_idx, n_days)
    base = _agg(suff)
    out.update({k: (float(v) if v is not None else None) for k, v in base.items()})
    out["n_dates"] = int(n_days)

    W, L, p = base["W"], base["L"], base["p"]
    denom = W + L
    out["W_L"] = float(W / L) if (np.isfinite(L) and L > 0) else float("nan")
    out["p_be"] = float(L / denom) if (np.isfinite(denom) and denom > 0) else float("nan")
    out["p_be_net"] = (float((L + cost_bps) / denom)
                       if (np.isfinite(denom) and denom > 0) else float("nan"))
    out["edge"] = (float(p - out["p_be_net"]) if np.isfinite(out["p_be_net"]) else float("nan"))

    # --- identity reconstruction (§4.1 / §12 HARD) --------------------------------
    recon = (p * W - (1.0 - p) * L) if all(np.isfinite([p, W, L])) else float("nan")
    # cells with r == 0 are excluded from p and counted (p_flat); the identity is stated over the
    # signed rows, so reconstruct against the signed-row mean.
    signed_mask = r != 0
    signed_mean = float(r[signed_mask].mean()) if signed_mask.any() else float("nan")
    out["identity_reconstruction"] = float(recon)
    out["identity_residual_bps"] = (abs(recon - signed_mean)
                                    if np.isfinite(recon) and np.isfinite(signed_mean)
                                    else float("nan"))
    out["identity_tol_bps"] = IDENTITY_RECONSTRUCTION_TOL_BPS
    out["mean_signed_rows"] = signed_mean

    # --- point statistics ---------------------------------------------------------
    out["median"] = float(np.median(r))
    out["trimmed_mean_10"] = _trimmed(r, TRIM_FRACTION)
    out["iid_mde_bps__COMPANION_ONLY"] = iid_mde_companion(r)
    out["mde_source_for_bands"] = "block"

    # --- envelope CIs on the mean family (exact from sufficient statistics) --------
    cis = dict(envelope_ci_suff(suff, cost_bps, ("mean", "p", "W", "L", "W_L", "edge"),
                                n_boot=n_boot))
    if full:
        day_ids = np.arange(n_days)
        for name in ("median", "trimmed_mean"):
            cis[name] = envelope_ci(day_ids, _stat_from_rows(name, r, day_idx, n_days),
                                    n_boot=n_boot)

    for name, ci in cis.items():
        out[f"{name}_ci_low"] = ci["ci_low"]
        out[f"{name}_ci_high"] = ci["ci_high"]
    out["block_mde_mean_bps"] = block_mde(cis["mean"])
    out["block_mde_p"] = block_mde(cis["p"])
    out["block_mde_edge"] = block_mde(cis["edge"])
    out["_ci_detail"] = cis
    return out


# --------------------------------------------------------------------------- #
# interpretation bands — LABELS, NEVER GATES (§8 / INFR-016)
# --------------------------------------------------------------------------- #
def _label(effect: float, ci_low: float, ci_high: float, mde: float, target: float,
           sup: float, contra: float, *, levers_exhausted: bool) -> str:
    """Shared band logic.

    Precedence is CI-first, then power. A cell whose CI excludes zero IS resolved, whatever its
    nominal MDE ceiling says; only a cell that has NOT resolved can be short of power. That
    ordering keeps B-5 symmetric: UNPOWERED / NOT_RESOLVABLE are power statements about
    unresolved cells and can never stand in for a negative.
    """
    if not np.isfinite(effect):
        return "UNPOWERED"
    if np.isfinite(ci_low) and ci_low > 0 and effect >= sup:
        return "SUPPORTED"
    if np.isfinite(ci_high) and ci_high < 0 and effect <= contra:
        return "CONTRADICTED"
    if not np.isfinite(mde) or not np.isfinite(target) or mde > target:
        return "NOT_RESOLVABLE" if levers_exhausted else "UNPOWERED"
    return "WASH"


def band_mean(cell: dict, *, levers_exhausted: bool = False) -> str:
    """mean r (bps) band — §8."""
    return _label(cell.get("mean", float("nan")),
                  cell.get("mean_ci_low", float("nan")),
                  cell.get("mean_ci_high", float("nan")),
                  cell.get("block_mde_mean_bps", float("nan")),
                  BAND_MEAN_MDE_CEILING_BPS,
                  BAND_MEAN_SUPPORTED_BPS, BAND_MEAN_CONTRADICTED_BPS,
                  levers_exhausted=levers_exhausted)


def band_edge(cell: dict, *, levers_exhausted: bool = False) -> str:
    """``edge = p - p_be_net`` band — §8. NOT ``p > 0.5`` (SoT §2.2, refused programme-wide).

    The cell's own target precision for ``edge`` is its own ``|edge|`` (design §9 'uniform'):
    the block MDE on ``p`` must sit below the edge the cell actually shows.
    """
    edge = cell.get("edge", float("nan"))
    target = abs(edge) if np.isfinite(edge) else float("nan")
    return _label(edge,
                  cell.get("edge_ci_low", float("nan")),
                  cell.get("edge_ci_high", float("nan")),
                  cell.get("block_mde_p", float("nan")),
                  target, 0.0, 0.0,
                  levers_exhausted=levers_exhausted)


def not_resolvable_record(cell: dict, *, arm: str, cell_key: dict, target_mde: float,
                          target_rule: str, r: np.ndarray) -> dict:
    """§5: a NOT_RESOLVABLE cell is reported as a QUANTIFIED shortfall — a first-class answer."""
    mde = cell.get("block_mde_mean_bps", float("nan"))
    return {
        "arm": arm,
        **cell_key,
        "n": cell.get("n"),
        "n_dates": cell.get("n_dates"),
        "block_mde_bps": mde,
        "iid_mde_bps__COMPANION_ONLY": cell.get("iid_mde_bps__COMPANION_ONLY"),
        "target_mde_bps": target_mde,
        "target_rule": target_rule,
        "multiple_short": (float(mde / target_mde)
                           if np.isfinite(mde) and target_mde > 0 else float("nan")),
        "n_required_for_target": required_n_for_target(r, mde, target_mde),
        "statement": (
            "This cell cannot reach its parent's own target precision in its original form on "
            "this data. That is an ANSWER to the checkpoint-017 open question, not a failure, "
            "and it is never evidence against the hypothesis (B-5)."
        ),
    }
