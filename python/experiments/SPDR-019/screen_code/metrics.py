"""log R metrics, day-block bootstrap envelope, sensitivity ladder (design §5, §8).

Bootstrap speed path is bit-identical to xen.evaluation.block_bootstrap_ci — asserted.
"""
from __future__ import annotations

import numpy as np

from xen.evaluation import block_bootstrap_ci

from config import (
    BOOT_BLOCKS_DAYS,
    BOOT_CI_ALPHA,
    BOOT_RESAMPLES,
    BOOT_SEEDS,
    COST_FLOOR_BPS,
    DAY_NS,
    EFFECTIVE_COVERAGE_START_NS,
    IDENTITY_RECONSTRUCTION_TOL_BPS,
    IID_MDE_CONST,
    LADDER_RUNGS,
    NS,
)

# --------------------------------------------------------------------------- day keys
def day_index(ts_ns: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    days = np.asarray(ts_ns, dtype=np.int64) // DAY_NS
    uniq, inv = np.unique(days, return_inverse=True)
    return inv.astype(np.int64), uniq * DAY_NS


_SUFF_COLS = ("n", "sum", "n_pos", "sum_pos", "n_neg", "sum_neg", "n_zero", "sumsq")


def day_sufficient(r: np.ndarray, day_idx: np.ndarray, n_days: int) -> np.ndarray:
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


def log_R_from_pWL(p: float, W: float, L: float) -> float:
    """Primary read: log(W/L) − log((1−p)/p). Slope 1. Exact mirror identity."""
    if not all(np.isfinite([p, W, L])) or p <= 0 or p >= 1 or L <= 0 or W <= 0:
        return float("nan")
    return float(np.log(W / L) - np.log((1.0 - p) / p))


def _resample_day_blocks(n_days: int, block: int, n_boot: int, seed: int) -> np.ndarray:
    """Byte-identical construction to xen.evaluation.block_bootstrap_ci."""
    eff = max(1, min(int(block), n_days - 1))
    n_blocks = int(np.ceil(n_days / eff))
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, n_days, size=(n_boot, n_blocks))
    idx = (starts[:, :, None] + np.arange(eff)[None, None, :]).reshape(n_boot, -1)[:, :n_days]
    return idx % n_days


_BOOT_CHUNK = 250  # replicates per aggregation chunk; caps peak memory on wide day panels


def _boot_totals(suff: np.ndarray, block: int, n_boot: int, seed: int) -> np.ndarray:
    """Per-replicate column totals, chunked over replicates to bound peak memory.

    ``suff[idx]`` materialises ``(n_boot, n_days, 8)`` float64 — ~115 MB for a 900-day pooled
    cell at n_boot=2000, once per bootstrap call. Chunking keeps the draws bit-identical (the
    index matrix is generated in one shot, exactly as the canonical path does) while holding
    the working set to one chunk (QA run 8, R8-28).
    """
    n_days = suff.shape[0]
    idx = _resample_day_blocks(n_days, block, n_boot, seed)
    out = np.empty((n_boot, suff.shape[1]), dtype=float)
    for lo in range(0, n_boot, _BOOT_CHUNK):
        hi = min(lo + _BOOT_CHUNK, n_boot)
        out[lo:hi] = suff[idx[lo:hi]].sum(axis=1)
    return out


def log_R_is_defined(p, W, L) -> bool:
    """Is `log R = log(W/L) - log((1-p)/p)` defined from THESE primitives? (AMENDMENT-20)

    Derived from `p`, `W`, `L` and nothing else — deliberately NOT from an emitted `log_R`
    field, because the exemption path blanks that field, and a check that reads the value its
    own remedy just deleted can only ever agree with itself (QA run 11, R11-02).
    """
    vals = (p, W, L)
    ok_types = (int, float, np.floating, np.integer)  # np.integer per QA run 12, R12-04
    if not all(isinstance(v, ok_types) and np.isfinite(v) for v in vals):
        return False
    return bool(0.0 < float(p) < 1.0 and float(W) > 0.0 and float(L) > 0.0)


def _logR_from_totals(tot: np.ndarray) -> np.ndarray:
    n_pos, sum_pos = tot[:, 2], tot[:, 3]
    n_neg, sum_neg = tot[:, 4], tot[:, 5]
    signed = n_pos + n_neg
    with np.errstate(divide="ignore", invalid="ignore"):
        p = np.where(signed > 0, n_pos / signed, np.nan)
        W = np.where(n_pos > 0, sum_pos / n_pos, np.nan)
        L = np.where(n_neg > 0, -sum_neg / n_neg, np.nan)
        return np.where(
            (p > 0) & (p < 1) & (W > 0) & (L > 0),
            np.log(W / L) - np.log((1.0 - p) / p),
            np.nan,
        )


def _logR_boot_stats(suff: np.ndarray, block: int, n_boot: int, seed: int) -> np.ndarray:
    """Vectorised log-R bootstrap; same index draws as xen.evaluation.block_bootstrap_ci."""
    return _logR_from_totals(_boot_totals(suff, block, n_boot, seed))


def envelope_ci_logR(suff: np.ndarray, *, n_boot: int = BOOT_RESAMPLES) -> dict:
    """Min/max envelope over blocks {1,3,7} × 5 seeds on log R."""
    n_days = suff.shape[0]
    point_a = _agg(suff)
    point = log_R_from_pWL(point_a["p"], point_a["W"], point_a["L"])
    if n_days < 2:
        return {
            "stat": float(point), "ci_low": float("nan"), "ci_high": float("nan"),
            "n_days": int(n_days), "per_block": [], "per_seed": [], "degenerate": True,
        }
    lows, highs = [], []
    per_block, per_seed = [], []
    for bl in BOOT_BLOCKS_DAYS:
        eff = max(1, min(int(bl), n_days - 1))
        seed_lo, seed_hi = [], []
        for seed in BOOT_SEEDS:
            stats = _logR_boot_stats(suff, bl, n_boot, seed)
            v = stats[np.isfinite(stats)]
            if v.size == 0:
                continue
            lo = float(np.quantile(v, BOOT_CI_ALPHA / 2))
            hi = float(np.quantile(v, 1 - BOOT_CI_ALPHA / 2))
            seed_lo.append(lo)
            seed_hi.append(hi)
            per_seed.append({
                "block_days": int(bl), "seed": int(seed),
                "ci_low": lo, "ci_high": hi,
            })
        if seed_lo:
            lows += seed_lo
            highs += seed_hi
            per_block.append({
                "block_days": int(bl), "effective_block": eff,
                "ci": [float(np.median(seed_lo)), float(np.median(seed_hi))],
                "ci_low_seed_range": [min(seed_lo), max(seed_lo)],
                "ci_high_seed_range": [min(seed_hi), max(seed_hi)],
            })
    return {
        "stat": float(point),
        "ci_low": float(min(lows)) if lows else float("nan"),
        "ci_high": float(max(highs)) if highs else float("nan"),
        "n_days": int(n_days),
        "per_block": per_block,
        "per_seed": per_seed,
        "degenerate": False,
        "envelope_rule": "min/max over blocks {1,3,7} days x 5 seeds",
    }


def assert_canonical_equivalence(
    suff: np.ndarray, *, block: int = 3, n_boot: int = 500, tol: float = 1e-9
) -> dict:
    """Prove vectorised logR path == xen.evaluation.block_bootstrap_ci on same seed."""

    def stat(s: np.ndarray) -> float:
        a = _agg(np.atleast_2d(s))
        return log_R_from_pWL(a["p"], a["W"], a["L"])

    canon = block_bootstrap_ci(
        suff, stat, block=block, n_boot=n_boot, alpha=BOOT_CI_ALPHA,
        seed=BOOT_SEEDS[0], n_seeds=1,
    )
    fast = _logR_boot_stats(suff, block, n_boot, BOOT_SEEDS[0])
    v = fast[np.isfinite(fast)]
    lo = float(np.quantile(v, BOOT_CI_ALPHA / 2))
    hi = float(np.quantile(v, 1 - BOOT_CI_ALPHA / 2))
    d_lo = abs(lo - canon["ci"][0])
    d_hi = abs(hi - canon["ci"][1])
    return {
        "statistic": "log_R", "block": block, "n_boot": n_boot,
        "canonical_ci": [float(canon["ci"][0]), float(canon["ci"][1])],
        "vectorised_ci": [lo, hi], "abs_diff": [d_lo, d_hi], "tol": tol,
        "equivalent": bool(d_lo <= tol and d_hi <= tol),
    }


def block_mde(ci: dict) -> float:
    if not np.isfinite(ci.get("stat", np.nan)) or not np.isfinite(ci.get("ci_low", np.nan)):
        return float("nan")
    return float(ci["stat"] - ci["ci_low"])


def iid_mde_companion(r: np.ndarray) -> float:
    r = np.asarray(r, dtype=float)
    n = r.size
    if n < 2:
        return float("nan")
    return float(IID_MDE_CONST * np.std(r, ddof=1) / np.sqrt(n))


LADDER_BLOCK_DAYS = 3   # declared, descriptive: the ladder is a resolution curve, not a CI
LADDER_SEED = BOOT_SEEDS[0]


def resolution_ladder(suff: np.ndarray, *, n_boot: int = BOOT_RESAMPLES) -> dict:
    """§8 sensitivity ladder: detection RATE per rung, under BOTH plant operators.

    Both operators are applied to the resampled data, not to the point estimate — on the point
    estimate they are algebraically the same number and the pair carries no information
    (QA run 8, R8-08).

      via W/L (PRIMARY): scale every positive return by ``exp(delta)`` at fixed ``p``. In every
        replicate this shifts ``log(W/L)`` by exactly ``delta``, so the planted replicate
        distribution is the unplanted one shifted by ``delta``.
      via p (CO-REPORT): move a fraction ``f`` of losing episodes to winners at fixed ``W`` and
        ``L``, with ``f`` solving the pooled ``p'``. Each replicate's planted value depends on
        its OWN realised counts, so this distribution is not a shift — which is precisely why
        the two detection rates differ.

    Detection rate at a rung = the fraction of replicates whose planted value clears the
    critical value of the centred unplanted distribution at ``BOOT_CI_ALPHA`` — a genuine rate
    in [0,1], not a 0/1 indicator (QA run 8, R8-09).
    """
    n_days = suff.shape[0]
    base = _agg(suff)
    p0, W0, L0, n = base["p"], base["W"], base["L"], base["n"]
    out = {
        "ladder_rungs": list(LADDER_RUNGS),
        "detect_rate_via_WL": {},
        "detect_rate_via_p": {},
        "required_n_via_WL": {},
        "mde50": float("nan"), "mde80": float("nan"), "mde95": float("nan"),
        "ladder_block_days": LADDER_BLOCK_DAYS,
        "ladder_seed": LADDER_SEED,
        "n_replicates": 0,
    }
    if n_days < 2 or not all(np.isfinite([p0, W0, L0])) or L0 <= 0 or p0 <= 0 or p0 >= 1:
        return out

    tot = _boot_totals(suff, LADDER_BLOCK_DAYS, n_boot, LADDER_SEED)
    base_stats = _logR_from_totals(tot)
    ok = np.isfinite(base_stats)
    if not ok.any():
        return out
    v0 = base_stats[ok]
    point = log_R_from_pWL(p0, W0, L0)
    # critical value of the CENTRED unplanted distribution: an effect is detected when the
    # planted value clears the noise the same bootstrap measures
    crit = float(np.quantile(v0 - point, 1 - BOOT_CI_ALPHA / 2))
    out["n_replicates"] = int(v0.size)
    out["detection_critical_value"] = crit

    n_pos, sum_pos = tot[:, 2], tot[:, 3]
    n_neg, sum_neg = tot[:, 4], tot[:, 5]
    signed = n_pos + n_neg
    with np.errstate(divide="ignore", invalid="ignore"):
        W_b = np.where(n_pos > 0, sum_pos / n_pos, np.nan)
        L_b = np.where(n_neg > 0, -sum_neg / n_neg, np.nan)

    rates_wl, rates_p, req_n = {}, {}, {}
    for delta in LADDER_RUNGS:
        # --- PRIMARY: scale W/L by exp(delta) at fixed p -> exact +delta per replicate
        planted_wl = base_stats + delta
        w = planted_wl[np.isfinite(planted_wl)]
        rates_wl[str(delta)] = float(np.mean(w > crit)) if w.size else float("nan")

        # --- CO-REPORT: move losers to winners at fixed W and L
        target_odds = ((1 - p0) / p0) * np.exp(-delta)
        p_prime = 1.0 / (1.0 + target_odds)
        f = (p_prime * (base["n_pos"] + base["n_neg"]) - base["n_pos"]) / base["n_neg"]
        f = float(np.clip(f, 0.0, 1.0))
        with np.errstate(divide="ignore", invalid="ignore"):
            n_pos_p = n_pos + f * n_neg
            n_neg_p = (1.0 - f) * n_neg
            p_b = np.where(signed > 0, n_pos_p / signed, np.nan)
            planted_p = np.where(
                (p_b > 0) & (p_b < 1) & (W_b > 0) & (L_b > 0) & (n_neg_p > 0),
                np.log(W_b / L_b) - np.log((1.0 - p_b) / p_b),
                np.nan,
            )
        vp = planted_p[np.isfinite(planted_p)]
        rates_p[str(delta)] = float(np.mean(vp > crit)) if vp.size else float("nan")

    # mde50/80/95 = the ladder curve of the PRIMARY operator, inverted exactly. Under that
    # operator rate(d) = P(theta* + d > crit), so the effect detectable at rate q is
    # crit - quantile(theta*, 1-q). This is the same curve the rungs sample, read continuously
    # rather than interpolated between six points.
    for key, q in (("mde50", 0.50), ("mde80", 0.80), ("mde95", 0.95)):
        out[key] = float(crit - np.quantile(v0, 1.0 - q))

    for delta in LADDER_RUNGS:
        m = out["mde50"]
        req_n[str(delta)] = (
            float(np.ceil(n * (m / delta) ** 2))
            if np.isfinite(m) and delta > 0 and n > 0 else float("nan")
        )

    out["detect_rate_via_WL"] = rates_wl
    out["detect_rate_via_p"] = rates_p
    out["required_n_via_WL"] = req_n
    return out


def cell_metrics(
    r: np.ndarray,
    ts_ns: np.ndarray,
    *,
    n_boot: int = BOOT_RESAMPLES,
    cost_bps: float = COST_FLOOR_BPS,
    mfe: np.ndarray | None = None,
) -> dict:
    """Full (p,W,L,log R) cell with block CI, MDE, ladder. No powered flag."""
    r = np.asarray(r, dtype=float)
    ok = np.isfinite(r)
    mfe_arr = np.asarray(mfe, dtype=float)[ok] if mfe is not None else None
    r = r[ok]
    ts = np.asarray(ts_ns, dtype=np.int64)[ok]
    out: dict = {"n": int(r.size), "cost_bps_DISCLOSURE_ONLY": float(cost_bps)}
    if r.size == 0:
        out["empty"] = True
        out["log_R"] = float("nan")
        out["ci_low"] = float("nan")
        out["ci_high"] = float("nan")
        out["ci_width"] = float("nan")
        out["block_mde"] = float("nan")
        return out

    day_idx, day_starts = day_index(ts)
    n_days = int(day_starts.size)
    suff = day_sufficient(r, day_idx, n_days)
    base = _agg(suff)
    out.update(base)
    out["n_dates"] = n_days

    p, W, L = base["p"], base["W"], base["L"]
    denom = W + L if np.isfinite(W) and np.isfinite(L) else float("nan")
    out["W_L"] = float(W / L) if (np.isfinite(L) and L > 0) else float("nan")
    out["p_be"] = float(L / denom) if (np.isfinite(denom) and denom > 0) else float("nan")
    out["p_be_net"] = (
        float((L + cost_bps) / denom) if (np.isfinite(denom) and denom > 0) else float("nan")
    )
    out["p_be_net_flag"] = "DISCLOSURE_ONLY"
    out["log_R"] = log_R_from_pWL(p, W, L)

    # identity: mean_signed = p*W - (1-p)*L
    signed = r != 0
    signed_mean = float(r[signed].mean()) if signed.any() else float("nan")
    recon = (p * W - (1.0 - p) * L) if all(np.isfinite([p, W, L])) else float("nan")
    out["identity_residual_bps"] = (
        abs(recon - signed_mean) if np.isfinite(recon) and np.isfinite(signed_mean) else float("nan")
    )
    out["identity_tol_bps"] = IDENTITY_RECONSTRUCTION_TOL_BPS
    out["mean_signed_rows"] = signed_mean

    ci = envelope_ci_logR(suff, n_boot=n_boot)
    out["ci_low"] = ci["ci_low"]
    out["ci_high"] = ci["ci_high"]
    out["ci_width"] = (
        float(ci["ci_high"] - ci["ci_low"])
        if np.isfinite(ci["ci_low"]) and np.isfinite(ci["ci_high"]) else float("nan")
    )
    out["block_mde"] = block_mde(ci)
    out["iid_mde_log__COMPANION_ONLY"] = (
        iid_mde_companion(r) / max((1 - p) * L, 1e-12)
        if all(np.isfinite([p, L])) else float("nan")
    )
    out["mde_source_for_bands"] = "block"
    out["n_days"] = n_days
    out["effective_block_cap"] = True
    out["per_block_ci"] = ci.get("per_block", [])
    out["per_seed_ci"] = ci.get("per_seed", [])

    # AMENDMENT-20: a cell that cannot carry a block-bootstrap CI must NAME which condition
    # applies, and may not ship a log R (§12 "log R never unaccompanied" — log R was assigned
    # from (p, W, L) above, before the CI was attempted, so a cell that early-returns at
    # n_days < 2 would otherwise keep a number and lose its interval).
    # Order is fixed so the token is deterministic; integrity re-derives BOTH conditions and
    # validates whichever is claimed.
    if np.isfinite(out["ci_low"]) and np.isfinite(out["ci_high"]):
        out["ci_absent_reason"] = None
    else:
        if not log_R_is_defined(p, W, L):
            out["ci_absent_reason"] = "LOG_R_UNDEFINED"
        elif n_days < 2:
            out["ci_absent_reason"] = "N_DATES_LT_2_NO_DAY_BLOCK"
        else:
            # no admissible condition → integrity classes it unclassified → HARD failure
            out["ci_absent_reason"] = None
        out["log_R"] = float("nan")

    # realised c = mde_log * sqrt(n)
    mde = out["block_mde"]
    out["realised_c"] = float(mde * np.sqrt(r.size)) if np.isfinite(mde) and r.size else float("nan")
    # §8.1 realised EFFECTIVE sample size: the iid n that would reach this cell's realised
    # block precision. Emitting the nominal n under this name asserted a dependence
    # adjustment that had not been made, and it is the one number that says what the M15
    # "~4x" lever actually bought (QA run 8, R8-19).
    #
    # Both half-widths must be taken at the SAME alpha or the ratio measures the constant, not
    # the dependence: the companion column is the 2.8σ MDE form (M-1), so the iid reference
    # here is rebuilt at BOOT_CI_ALPHA via the delta method on log R.
    z = 1.959963984540054
    sd_r = float(np.std(r, ddof=1)) if r.size > 1 else float("nan")
    scale = (1.0 - p) * L if all(np.isfinite([p, L])) else float("nan")
    iid_half = (
        z * sd_r / (np.sqrt(r.size) * scale)
        if np.isfinite(sd_r) and np.isfinite(scale) and scale > 0 else float("nan")
    )
    # companion-only, like every other iid form (M-1): it drives no band and no threshold —
    # its sole consumer is the effective-n ratio below
    out["iid_ci_half_width_log_same_alpha__COMPANION_ONLY"] = iid_half
    out["effective_n"] = (
        float(r.size * (iid_half / mde) ** 2)
        if np.isfinite(mde) and mde > 0 and np.isfinite(iid_half) else float("nan")
    )
    out["n_nominal"] = float(r.size)

    # CI-relative band (§9). NEVER named `band` — the reporting band (TRAIN/DESIGN/CONFIRM)
    # owns that key on the same row and silently overwrote this one (QA run 8, R8-11).
    if np.isfinite(out["ci_low"]) and out["ci_low"] > 0:
        out["mirror_band"] = "ABOVE_THE_MIRROR"
    elif np.isfinite(out["ci_high"]) and out["ci_high"] < 0:
        out["mirror_band"] = "BELOW_THE_MIRROR"
    else:
        out["mirror_band"] = "COVERS_THE_MIRROR"

    lad = resolution_ladder(suff, n_boot=n_boot)
    out["ladder"] = lad
    out["mde50"], out["mde80"], out["mde95"] = lad["mde50"], lad["mde80"], lad["mde95"]
    for k, v in lad["detect_rate_via_WL"].items():
        out[f"detect_wl_{k}"] = v
    for k, v in lad["detect_rate_via_p"].items():
        out[f"detect_p_{k}"] = v

    # κ = median(r / mfe) (§5) — non-tradable ceiling-relative diagnostic, multiplies nothing
    if mfe_arr is not None:
        good = np.isfinite(mfe_arr) & (mfe_arr > 0) & np.isfinite(r)
        out["kappa"] = float(np.median(r[good] / mfe_arr[good])) if good.any() else float("nan")
        out["kappa_n"] = int(good.sum())
    else:
        out["kappa"] = float("nan")
        out["kappa_n"] = 0
    out["kappa_status"] = "DISCLOSURE_ONLY"

    # span / coverage placeholders filled by caller when ts available
    out["span_exact_frac"] = float("nan")
    out["span_p50"] = float("nan")
    out["span_p90"] = float("nan")
    return out


def homogeneity(values: np.ndarray, ses: np.ndarray) -> dict:
    """Cochran Q and I² across the per-symbol cells behind a pooled cell (§9).

    §9 grants the pooled read PRIMARY status only conditionally, and the condition is an
    EMITTED homogeneity statistic. With none emitted the condition could not be evaluated and
    the lane default (pooled = disclosure-only, L-03) applied by omission (QA run 8, R8-23).
    The operator judges the emitted value; nothing here drops or re-labels a cell.
    """
    v = np.asarray(values, dtype=float)
    s = np.asarray(ses, dtype=float)
    ok = np.isfinite(v) & np.isfinite(s) & (s > 0)
    v, s = v[ok], s[ok]
    k = v.size
    out = {"i_squared": float("nan"), "q_stat": float("nan"), "q_df": max(k - 1, 0),
           "k_symbols": int(k), "per_symbol_spread": float("nan")}
    if k < 2:
        return out
    w = 1.0 / (s ** 2)
    mu = float(np.sum(w * v) / np.sum(w))
    q = float(np.sum(w * (v - mu) ** 2))
    df = k - 1
    out["q_stat"] = q
    out["i_squared"] = float(max(0.0, (q - df) / q)) if q > 0 else 0.0
    out["fixed_effect_mean"] = mu
    out["per_symbol_spread"] = float(np.max(v) - np.min(v))
    return out


def span_stats(entry_ts: np.ndarray, exit_ts: np.ndarray, h_hours: float) -> dict:
    e = np.asarray(entry_ts, dtype=np.int64)
    x = np.asarray(exit_ts, dtype=np.int64)
    if e.size == 0:
        return {"span_exact_frac": float("nan"), "span_p50": float("nan"), "span_p90": float("nan")}
    span_h = (x - e) / (3600 * NS)
    exact = np.isclose(span_h, h_hours, rtol=0, atol=1e-6)
    return {
        "span_exact_frac": float(exact.mean()),
        "span_p50": float(np.median(span_h)),
        "span_p90": float(np.percentile(span_h, 90)),
    }


def effective_coverage(ts_ns: np.ndarray, symbols: np.ndarray) -> dict:
    ts = np.asarray(ts_ns, dtype=np.int64)
    syms = np.asarray(symbols)
    if ts.size == 0:
        return {"n": 0, "n_symbols": 0, "effective_frac_of_nominal": float("nan")}
    nominal_days = float((ts.max() - ts.min()) / DAY_NS)
    multi = ts >= EFFECTIVE_COVERAGE_START_NS
    eff_days = float((ts[multi].max() - ts[multi].min()) / DAY_NS) if multi.any() else 0.0
    return {
        "n": int(ts.size),
        "n_symbols": int(len(np.unique(syms))),
        "nominal_days": nominal_days,
        "effective_multi_symbol_days": eff_days,
        "effective_frac_of_nominal": (eff_days / nominal_days) if nominal_days > 0 else float("nan"),
    }


def paired_combo_ci(
    arms: dict[str, tuple[np.ndarray, np.ndarray]],
    combo,
    *,
    n_boot: int = BOOT_RESAMPLES,
) -> dict:
    """Block-bootstrap CI for a COMBINATION of arms, resampled JOINTLY on a common day index.

    ``arms`` maps name -> (r, ts). ``combo`` maps {name: logR} -> scalar.

    Δ`log R` is the M15 primary read (§8.1) and the §4.3 phase-(b) trigger reads its `ci_low`,
    so it must come from the §8.1 block rule like any other read. Summing the two arms' CI
    widths treated strict-subset arms that share their fills and exits as independent, which
    both mis-scales the interval and discards the positive correlation that makes a paired
    difference precise (QA run 8, R8-10). One block index set per replicate, drawn on the
    union day index, gives the difference its own dependence-matched distribution.
    """
    names = list(arms)
    all_ts = np.concatenate([np.asarray(arms[k][1], dtype=np.int64) for k in names])
    if all_ts.size == 0:
        return {"delta_log_R": float("nan"), "ci_low": float("nan"),
                "ci_high": float("nan"), "ci_width": float("nan"),
                "block_mde": float("nan"), "n_days": 0, "per_seed": []}
    days = np.unique(all_ts // DAY_NS)
    n_days = int(days.size)
    suffs = {}
    for k in names:
        rk = np.asarray(arms[k][0], dtype=float)
        tk = np.asarray(arms[k][1], dtype=np.int64)
        ok = np.isfinite(rk)
        di = np.searchsorted(days, tk[ok] // DAY_NS)
        suffs[k] = day_sufficient(rk[ok], di, n_days)

    points = {}
    for k in names:
        a = _agg(suffs[k])
        points[k] = log_R_from_pWL(a["p"], a["W"], a["L"])
    point = combo(points)
    if n_days < 2:
        return {"delta_log_R": float(point), "ci_low": float("nan"),
                "ci_high": float("nan"), "ci_width": float("nan"),
                "block_mde": float("nan"), "n_days": n_days, "per_seed": [],
                "degenerate": True}

    lows, highs, per_seed = [], [], []
    for bl in BOOT_BLOCKS_DAYS:
        for seed in BOOT_SEEDS:
            idx = _resample_day_blocks(n_days, bl, n_boot, seed)
            vals = {}
            for k in names:
                s = suffs[k]
                tot = np.empty((n_boot, s.shape[1]), dtype=float)
                for lo in range(0, n_boot, _BOOT_CHUNK):
                    hi = min(lo + _BOOT_CHUNK, n_boot)
                    tot[lo:hi] = s[idx[lo:hi]].sum(axis=1)
                vals[k] = _logR_from_totals(tot)
            stat = combo(vals)
            v = stat[np.isfinite(stat)]
            if v.size == 0:
                continue
            lo_q = float(np.quantile(v, BOOT_CI_ALPHA / 2))
            hi_q = float(np.quantile(v, 1 - BOOT_CI_ALPHA / 2))
            lows.append(lo_q)
            highs.append(hi_q)
            per_seed.append({"block_days": int(bl), "seed": int(seed),
                             "ci_low": lo_q, "ci_high": hi_q})
    ci_low = float(min(lows)) if lows else float("nan")
    ci_high = float(max(highs)) if highs else float("nan")
    return {
        "delta_log_R": float(point),
        "ci_low": ci_low,
        "ci_high": ci_high,
        "ci_width": (ci_high - ci_low) if np.isfinite(ci_low) and np.isfinite(ci_high)
        else float("nan"),
        "block_mde": (float(point) - ci_low) if np.isfinite(ci_low) else float("nan"),
        "n_days": n_days,
        "per_seed": per_seed,
        "envelope_rule": "min/max over blocks {1,3,7} days x 5 seeds, paired on a common day index",
    }


def delta_logR_paired(
    r_a: np.ndarray, ts_a: np.ndarray,
    r_b: np.ndarray, ts_b: np.ndarray,
    *,
    n_boot: int = BOOT_RESAMPLES,
) -> dict:
    """Δ log R = logR(layer) − logR(L0), paired block bootstrap (§8.1)."""
    return paired_combo_ci(
        {"a": (r_a, ts_a), "b": (r_b, ts_b)},
        lambda v: v["a"] - v["b"],
        n_boot=n_boot,
    )
