"""EXP-024 — CF-CSRR-001 HYP-002b US-bloc session-anchor availability primary.

Data-analyst's OWN interrogation code (no experiment-local imports). Canonical xen only:
`xen.bar_aggregator.aggregate_ohlc` (1m->4h) and `xen.evaluation` (hardened CI/MDE, L-20).

Execution-agnostic availability screen: NO fills, NO P&L, NO cTrader, NO xen.adjudication
(nothing to reconcile). Integrity = causal <=t-1 provenance + leak tripwire + TRAIN-only
holdout fence (first 49%). See python/experiments/EXP-024/design.md.

Controlled follow-up to EXP-022 (USTEC lead). ONE frozen construction (no sweep):
  members   = US bloc {USTEC, US500, US2000, US30}; sigma_i = +1 (single US-equity factor)
  anchor    = session-open reset S (SESSION_HOUR=12; reused verbatim from EXP-022 screen.py)
  A=median, B=raw, C=all>k (PRIMARY, powered), D=hedged (idio=g_i-G) — each a single value.
  h_i = clamp(round(2*HL_i),[1,12]); HL_i = AR(1) half-life of s_i under session anchor.
  k   = trailing-median of per-bar max_i|s_i| (causal, <t).

  u_i(t)=ln(Close_i(t)/anchor_i(t)); m=median({u_j present}); s_i=u_i-m;
  g_i(t,h)=ln(Open_i(t+1+h)/Open_i(t+1)); G=median({g_j}); idio=g_i-G;
  rho_i = -sign(s_i)*idio  [+ => residual reverts in fade dir].  Open-to-open (L-01).

Multiplicity family = the 4 US-bloc members. Significance = permuted-axis identity null per
member + HOLM over members with a valid p_perm (an UNPOWERED member does not consume Holm
alpha — QA issue 2). Robustness (disclosed): single-worst hedged continuity; 1/2/3*HL horizon
sign-stability; both-temporal-halves sign-stability.

R1 FIX (QA blocking carry-forward): the FULL hardened CI battery (n_boot>=10k, 5-seed
ci_low_seed_range, block_sensitivity 1/2x/1x/2x, trimmed_mean) is applied to the binding
R_US/anchor-S/all>k/hedged cell BY CONSTRUCTION — NOT gated to N*P as EXP-022 screen.py:422
did (which routed R_US/S to the 2k light path and omitted hardened disclosures on the
binding cell). Per design 6 the binding CI uses a circular block >= h_i; block_sensitivity
sweeps [max(1,h_i//2), h_i, 2*h_i].
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import polars as pl
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "python" / "src"))
from xen.bar_aggregator import aggregate_ohlc  # noqa: E402
from xen import evaluation as ev               # noqa: E402

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
EXP_DIR = ROOT / "python" / "experiments" / "EXP-024"
RESULTS = EXP_DIR / "results"
PLOTS = EXP_DIR / "plots"
DATA = ROOT / "data" / "timebars"

# 4 US-bloc members; sigma_i = +1 (single common US-equity factor).
MEMBERS = ["ustec", "us500", "us2000", "us30"]
DISPLAY = {"ustec": "USTEC", "us500": "US500", "us2000": "US2000", "us30": "US30"}
# session-open UTC hour snapped to the 4h grid (anchor S). All US bloc: NY cash open ~13:30.
SESSION_HOUR = {"ustec": 12, "us500": 12, "us2000": 12, "us30": 12}

# CLI: [min_coverage] [suffix] [period_minutes] — defaults reproduce the primary run.
MIN_COVERAGE = float(sys.argv[1]) if len(sys.argv) > 1 else 0.90
SUFFIX = sys.argv[2] if len(sys.argv) > 2 else ""
PERIOD_MIN = int(sys.argv[3]) if len(sys.argv) > 3 else 240
TRAIN_FRAC = 0.49             # first 70% analysis * first 70% train = first 49% of the file
K_TRAIL_W = 120               # trailing window (4h bars) for threshold k (also warmup)
MIN_MEMBERS = 3               # >=3 of 4 present required for a valid consensus bar
N_SEEDS = 25                  # L-19 twin battery
N_PERM = 1000                 # permuted-axis null
N_TRIP = 300                  # tripwire block-permute reps
BLOCK_TRIP = 12               # temporal block for tripwire (>= max h clamp 12)
N_BOOT_FULL = 10_000          # BINDING construction (L-20 hardened) — R1: always full here
N_BOOT_ROBUST = 2_000         # single-worst continuity (lighter; disclosed)
ALPHA = 0.05
RNG_GLOBAL = 20260706
BPS = 1e4


def reset_anchor(times: np.ndarray, close: np.ndarray, offset_h: int) -> np.ndarray:
    """anchor[k] = close of the prior reset-period's last bar (causal). NaN before first reset.

    Reset rolls when the bar's (UTC hour) crosses `offset_h`: bucket = floor((t-offset_h)/day).
    offset_h=0 -> common 00:00-UTC daily reset. offset_h=session hour -> anchor S.
    """
    shifted = times.astype("datetime64[ns]") - np.timedelta64(offset_h, "h")
    bucket = shifted.astype("datetime64[D]")
    anchor = np.full(close.shape, np.nan)
    prev_last = -1
    for k in range(len(bucket)):
        if k > 0 and bucket[k] != bucket[k - 1]:
            prev_last = k - 1
        if prev_last >= 0:
            anchor[k] = close[prev_last]
    return anchor


def ar1_halflife(x: np.ndarray) -> float:
    """AR(1) half-life of a residual series. NaN if not mean-reverting (b<=0 or b>=1)."""
    x = x[np.isfinite(x)]
    if len(x) < 50:
        return np.nan
    x0, x1 = x[:-1], x[1:]
    x0c = x0 - x0.mean()
    denom = np.sum(x0c ** 2)
    if denom <= 0:
        return np.nan
    b = np.sum(x0c * (x1 - x1.mean())) / denom
    if b <= 0 or b >= 1:
        return np.nan
    return float(-np.log(2) / np.log(b))


def variance_ratio(x: np.ndarray, q: int) -> float:
    """VR(q) = var(q-step diff)/(q*var(1-step diff)); <1 => mean-reverting."""
    x = x[np.isfinite(x)]
    d = np.diff(x)
    if len(d) < q + 5:
        return np.nan
    v1 = np.var(d, ddof=1)
    dq = x[q:] - x[:-q]
    vq = np.var(dq, ddof=1)
    if v1 <= 0:
        return np.nan
    return float(vq / (q * v1))


def consensus_resid(U: np.ndarray, present: np.ndarray, a_est: str, b_norm: str):
    """m(t), s_i(t) over present members only. Non-present entries -> NaN in s."""
    Um = np.where(present, U, np.nan)
    m = np.nanmedian(Um, axis=1) if a_est == "median" else np.nanmean(Um, axis=1)
    s = np.where(present, U - m[:, None], np.nan)
    if b_norm == "z":
        sig = np.nanstd(Um, axis=1, ddof=1)
        sig = np.where(sig > 0, sig, np.nan)
        s = s / sig[:, None]
    return m, s


def trailing_threshold(maxabs: np.ndarray, w: int) -> np.ndarray:
    """Causal trailing-median of the per-bar max|s| series (window strictly < t)."""
    n = len(maxabs)
    k = np.full(n, np.nan)
    for t in range(1, n):
        win = maxabs[max(0, t - w):t]
        win = win[np.isfinite(win)]
        if len(win) >= 10:
            k[t] = np.median(win)
    return k


def build_rows(O: np.ndarray, present: np.ndarray, s: np.ndarray, k_thr: np.ndarray,
               valid: np.ndarray, sel: str, hvec: np.ndarray, a_est: str, hedged: bool,
               cols: np.ndarray):
    """Return per-event records over the present-member subset (reused verbatim from EXP-022).

    Each record: (t, i_global, s_i, h, rho, fade, present_owner_idxs(local), idio_local, i_local).
    `cols` maps local column index -> global member index.
    """
    n, nI = s.shape
    absr = np.abs(s)
    rows = []
    for t in range(n - 2):
        if not valid[t] or not np.isfinite(k_thr[t]):
            continue
        cand = []
        if sel == "single":
            with np.errstate(invalid="ignore"):
                i = int(np.nanargmax(absr[t])) if np.any(np.isfinite(absr[t])) else -1
            if i >= 0 and absr[t, i] >= k_thr[t]:
                cand = [i]
        else:                                   # all>k
            cand = [i for i in range(nI) if present[t, i] and absr[t, i] >= k_thr[t]]
        if not cand:
            continue
        for i in cand:
            hi = int(hvec[i])
            k1 = t + 1
            if k1 + hi >= n:
                continue
            with np.errstate(invalid="ignore", divide="ignore"):
                g = np.log(O[k1 + hi] / O[k1])          # (nI,) local columns
            fpres = present[t] & np.isfinite(g)
            if not fpres[i]:
                continue
            gp = g[fpres]
            if gp.size < 1:
                continue
            G = (np.median(gp) if a_est == "median" else np.mean(gp)) if hedged else 0.0
            idio = np.where(fpres, g - G, np.nan) if hedged else np.where(fpres, g, np.nan)
            if not np.isfinite(idio[i]):
                continue
            fade = -np.sign(s[t, i])
            rho = fade * idio[i]
            pres_idx = np.where(fpres)[0]
            rows.append((t, int(cols[i]), float(s[t, i]), hi, float(rho), float(fade),
                         pres_idx, idio, i))
    return rows


def _pack(rows):
    """Pack rows into padded arrays for vectorized permutation / twin resampling."""
    E = len(rows)
    fade = np.array([r[5] for r in rows])
    owner_local = np.array([r[8] for r in rows])
    idio_own = np.array([r[7][r[8]] for r in rows])
    maxK = max(len(r[6]) for r in rows)
    pad = np.full((E, maxK), -1, dtype=int)      # present local idxs
    idio = np.zeros((E, len(rows[0][7])))
    for e, r in enumerate(rows):
        pi = r[6]
        pad[e, :len(pi)] = pi
        idio[e, :] = np.nan_to_num(r[7], nan=0.0)
    counts = np.array([len(r[6]) for r in rows])
    return fade, owner_local, idio_own, pad, counts, idio


def permuted_axis_null(rows, n_perm, rng):
    """Within-bar identity permutation: reassign the idio owner among present members."""
    if not rows:
        return np.array([])
    fade, _, _, pad, counts, idio = _pack(rows)
    E = len(rows)
    ar = np.arange(E)
    null = np.empty(n_perm)
    for p in range(n_perm):
        sel = rng.integers(0, counts)
        owner = pad[ar, sel]
        null[p] = np.mean(fade * idio[ar, owner])
    return null


def random_index_twin(rows, n_seeds, rng):
    """Assign the fade to a random present member OTHER than the true owner (its own idio)."""
    if not rows:
        return np.array([])
    fade, owner_local, _, pad, counts, idio = _pack(rows)
    E = len(rows)
    means = np.empty(n_seeds)
    for si in range(n_seeds):
        vals = np.empty(E)
        for e in range(E):
            others = pad[e, :counts[e]]
            others = others[others != owner_local[e]]
            if others.size == 0:
                vals[e] = np.nan
                continue
            j = others[rng.integers(0, others.size)]
            vals[e] = fade[e] * idio[e, j]
        means[si] = np.nanmean(vals)
    return means


def tripwire_block_permute(rows, block, rng, n_perm):
    """Temporal block-permute the owner's idio series (block>=h). MUST collapse rho->0."""
    if not rows:
        return np.array([])
    fade = np.array([r[5] for r in rows])
    idio_own = np.array([r[7][r[8]] for r in rows])
    E = len(idio_own)
    nb = int(np.ceil(E / block))
    out = np.empty(n_perm)
    for p in range(n_perm):
        starts = rng.integers(0, E, size=nb)
        idx = (starts[:, None] + np.arange(block)[None, :]).ravel()[:E] % E
        out[p] = np.mean(fade * idio_own[idx])
    return out


def random_timing_twin(O, present, s, hvec, i_local, a_est, hedged, valid, n_events,
                       n_seeds, rng):
    """Enter at random valid bars on the same instrument; fade = -sign(residual at that bar)."""
    n = O.shape[0]
    h = int(np.median(hvec))
    cand = np.where(valid[: n - h - 2] & present[: n - h - 2, i_local]
                    & np.isfinite(s[: n - h - 2, i_local]))[0]
    cand = cand[cand + 1 + h < n]
    if cand.size == 0 or n_events == 0:
        return np.array([])
    means = np.empty(n_seeds)
    for seed in range(n_seeds):
        picks = rng.choice(cand, size=min(n_events, cand.size), replace=False)
        vals = []
        for t in picks:
            k1 = t + 1
            with np.errstate(invalid="ignore", divide="ignore"):
                g = np.log(O[k1 + h] / O[k1])
            fpres = present[t] & np.isfinite(g)
            if not fpres[i_local]:
                continue
            if hedged:
                gp = g[fpres]
                G = np.median(gp) if a_est == "median" else np.mean(gp)
                idio = g[i_local] - G
            else:
                idio = g[i_local]
            vals.append(-np.sign(s[t, i_local]) * idio)
        means[seed] = np.mean(vals) if vals else np.nan
    return means


def load_member(symbol: str) -> pl.DataFrame:
    """Load 1m 5-year file, slice first TRAIN_FRAC (holdout-safe), 1m->4h, emit session-anchor u."""
    f = sorted(DATA.glob(f"timebars_{symbol}_20210602_*.parquet"))[-1]
    df = pl.scan_parquet(f).sort("CloseTime").collect()
    cut = int(df.height * TRAIN_FRAC)              # only ever touch the first 49%
    df = df.head(cut)
    bars = aggregate_ohlc(df, period_minutes=PERIOD_MIN, min_coverage=MIN_COVERAGE)
    bars = bars.head(bars.height - 1)              # drop trailing partial window at train boundary
    t = bars["CloseTime"].to_numpy()
    c = bars["Close"].to_numpy().astype(float)
    aS = reset_anchor(t, c, SESSION_HOUR[symbol])
    with np.errstate(divide="ignore", invalid="ignore"):
        uS = np.log(c / aS)
    return pl.DataFrame({
        "CloseTime": bars["CloseTime"],
        f"O_{symbol}": bars["Open"].cast(float),
        f"uS_{symbol}": uS,
    })


def build_panel() -> pl.DataFrame:
    """Outer (union) join all 4 members on shared 4h CloseTime; NaN where absent."""
    panel = None
    for s in tqdm(MEMBERS, desc="load members"):
        b = load_member(s)
        panel = b if panel is None else panel.join(b, on="CloseTime", how="full", coalesce=True)
    return panel.sort("CloseTime")


def holm_adjust(pvals: list[float]) -> list[float]:
    """Holm-Bonferroni adjusted p-values (step-down). NaN pvals are excluded (UNPOWERED; do not
    consume alpha) and returned as NaN. Denominator = count of valid (non-NaN) pvals."""
    idx = list(range(len(pvals)))
    valid = [(i, p) for i, p in zip(idx, pvals) if np.isfinite(p)]
    m = len(valid)
    adj = [np.nan] * len(pvals)
    if m == 0:
        return adj
    valid.sort(key=lambda ip: ip[1])
    running = 0.0
    for rank, (i, p) in enumerate(valid):
        running = max(running, min(1.0, (m - rank) * p))
        adj[i] = running
    return adj


def main():
    RESULTS.mkdir(parents=True, exist_ok=True)
    PLOTS.mkdir(parents=True, exist_ok=True)
    print("[1/5] building panel ...")
    panel = build_panel()
    times = panel["CloseTime"].to_numpy()
    n = len(times)
    O = np.column_stack([panel[f"O_{s}"].to_numpy().astype(float) for s in MEMBERS])
    U = np.column_stack([panel[f"uS_{s}"].to_numpy().astype(float) for s in MEMBERS])
    present = np.isfinite(U) & np.isfinite(O)
    valid = present.sum(axis=1) >= MIN_MEMBERS
    print(f"      union 4h bars={n}  span={times[0]}..{times[-1]}  "
          f"median present/bar={int(np.median(present.sum(axis=1)))}")

    # Frozen construction: median / raw / session-anchor S
    m, s = consensus_resid(U, present, "median", "raw")
    cols = np.array(list(range(len(MEMBERS))))
    hl = np.empty(len(MEMBERS))
    hvec = np.empty(len(MEMBERS), dtype=int)        # primary = 2*HL
    sub_rows = []
    for li, gi in enumerate(cols):
        si = s[valid, li]
        si = si[np.isfinite(si)]
        h_ = ar1_halflife(si)
        hl[li] = h_
        hvec[li] = int(np.clip(round(2 * h_), 1, 12)) if np.isfinite(h_) else 6
        sub_rows.append({
            "instrument": DISPLAY[MEMBERS[gi]], "n": int(len(si)),
            "VR2": variance_ratio(si, 2), "VR6": variance_ratio(si, 6),
            "autocorr1": (float(np.corrcoef(si[:-1], si[1:])[0, 1]) if len(si) > 2 else np.nan),
            "HL": h_, "h": int(hvec[li])})
    # horizon-robustness h vectors (1/2/3 * HL; fac=2 == primary)
    hvec_by_fac = {fac: np.array([int(np.clip(round(fac * hl[li]), 1, 12))
                                  if np.isfinite(hl[li]) else 6 for li in range(len(MEMBERS))])
                   for fac in (1, 2, 3)}
    maxabs = np.where(valid, np.nanmax(np.where(present, np.abs(s), np.nan), axis=1), np.nan)
    k_thr = trailing_threshold(maxabs, K_TRAIL_W)

    # PRIMARY binding cell: all>k / hedged — FULL hardened battery (R1 fix)
    print("[2/5] binding cell (all>k / hedged, hardened CI) ...")
    rows_allk = build_rows(O, present, s, k_thr, valid, "allk", hvec, "median", True, cols)
    cell_rows, pvals, rho_by_member = [], [np.nan] * len(MEMBERS), {}
    for li, gi in enumerate(cols):
        r_i = [r for r in rows_allk if r[1] == int(gi)]
        rho_by_member[int(gi)] = r_i
        rho = np.array([r[4] for r in r_i])
        ne = len(rho)
        base = {"instrument": DISPLAY[MEMBERS[gi]], "selection": "allk", "hedge": "hedged",
                "n_events": ne, "h": int(hvec[li])}
        if ne < 1:
            cell_rows.append({**base, "mean_rho_bps": np.nan})
            continue
        rc = np.random.default_rng(RNG_GLOBAL + hash(("EXP-024", "allk", "hedged", int(gi))) % 100_000)
        blk = max(1, int(hvec[li]))                       # block >= h_i (design 6)
        ci = ev.block_bootstrap_ci(rho, np.mean, block=blk, n_boot=N_BOOT_FULL, n_seeds=5)
        obs = float(np.mean(rho))
        bs = ev.block_sensitivity(rho, [max(1, blk // 2), blk, blk * 2], n_boot=N_BOOT_FULL, n_seeds=5)
        tm = ev.block_bootstrap_ci(rho, ev.trimmed_mean, block=blk, n_boot=N_BOOT_FULL, n_seeds=5)
        perm_null = permuted_axis_null(r_i, N_PERM, rc)
        p_perm = float(np.mean(perm_null >= obs)) if perm_null.size else np.nan
        if perm_null.size:
            pvals[li] = p_perm
        ri = random_index_twin(r_i, N_SEEDS, rc)
        rt = random_timing_twin(O, present, s, hvec, li, "median", True, valid, ne, N_SEEDS, rc)
        trip = tripwire_block_permute(r_i, BLOCK_TRIP, rc, N_TRIP)
        ri_mean = float(np.nanmean(ri)) if ri.size else np.nan
        rt_mean = float(np.nanmean(rt)) if rt.size else np.nan
        rt_pct = float(np.mean(rt <= obs)) if rt.size else np.nan
        trip_mean = float(np.mean(trip)) if trip.size else np.nan
        cell_rows.append({**base, "mean_rho_bps": obs * BPS,
               "ci_low_bps": ci["ci"][0] * BPS, "ci_high_bps": ci["ci"][1] * BPS,
               "ci_low_seed_range_bps": [v * BPS for v in ci["ci_low_seed_range"]],
               "ci_high_seed_range_bps": [v * BPS for v in ci["ci_high_seed_range"]],
               "trimmed_mean_bps": tm["stat"] * BPS, "tmean_ci_low_bps": tm["ci"][0] * BPS,
               "block_sens_ci_low_bps": [r["ci"][0] * BPS for r in bs],
               "mde_bps": ev.mde(rho, block=blk, n_boot=N_BOOT_FULL) * BPS,
               "p_perm": p_perm,
               "ri_twin_bps": ri_mean * BPS, "ri_collapse": ev.collapse_fraction(obs, ri_mean),
               "rt_twin_bps": rt_mean * BPS, "rt_percentile": rt_pct,
               "rt_collapse": ev.collapse_fraction(obs, rt_mean),
               "tripwire_bps": trip_mean * BPS,
               "tripwire_collapse": ev.collapse_fraction(obs, trip_mean)})

    # Holm over members with a valid p_perm (UNPOWERED excluded from denominator)
    holm_p = holm_adjust(pvals)
    n_valid_holm = int(sum(np.isfinite(p) for p in pvals))
    holm_rows = [{"instrument": DISPLAY[MEMBERS[gi]], "p_perm": pvals[li],
                  "holm_p": holm_p[li], "n_valid_holm": n_valid_holm}
                 for li, gi in enumerate(cols)]

    # Robustness: both temporal halves + horizon 1/2/3*HL
    print("[3/5] robustness (both-halves, horizon, single-worst) ...")
    rob_rows = []
    for li, gi in enumerate(cols):
        r_i = rho_by_member.get(int(gi), [])
        rho = np.array([r[4] for r in r_i])
        ne = len(rho)
        if ne >= 2:                                      # both temporal halves
            mid = ne // 2
            for half, lab in [(rho[:mid], "first"), (rho[mid:], "second")]:
                if half.size:
                    ci_h = ev.block_bootstrap_ci(half, np.mean, block=max(1, int(hvec[li])),
                                                 n_boot=N_BOOT_ROBUST, n_seeds=5)
                    rob_rows.append({"instrument": DISPLAY[MEMBERS[gi]], "type": "both_halves",
                                     "half": lab, "n": int(half.size),
                                     "mean_rho_bps": float(np.mean(half)) * BPS,
                                     "ci_low_bps": ci_h["ci"][0] * BPS,
                                     "sign": int(np.sign(np.mean(half)))})
    rows_h1 = build_rows(O, present, s, k_thr, valid, "allk", hvec_by_fac[1], "median", True, cols)
    rows_h3 = build_rows(O, present, s, k_thr, valid, "allk", hvec_by_fac[3], "median", True, cols)
    for li, gi in enumerate(cols):
        for fac, rs in [(1, rows_h1), (2, rows_allk), (3, rows_h3)]:
            rho_f = np.array([r[4] for r in rs if r[1] == int(gi)])
            rob_rows.append({"instrument": DISPLAY[MEMBERS[gi]], "type": "horizon",
                             "h_factor": fac, "h": int(hvec_by_fac[fac][li]), "n": int(len(rho_f)),
                             "mean_rho_bps": (float(np.mean(rho_f)) * BPS if rho_f.size else np.nan),
                             "sign": (int(np.sign(np.mean(rho_f))) if rho_f.size else 0)})

    # single-worst hedged continuity (the exact EXP-022 lead form; lighter CI)
    rows_sw = build_rows(O, present, s, k_thr, valid, "single", hvec, "median", True, cols)
    for li, gi in enumerate(cols):
        r_i = [r for r in rows_sw if r[1] == int(gi)]
        rho = np.array([r[4] for r in r_i])
        ne = len(rho)
        base = {"instrument": DISPLAY[MEMBERS[gi]], "selection": "single", "hedge": "hedged",
                "n_events": ne, "h": int(hvec[li])}
        if ne < 1:
            cell_rows.append({**base, "mean_rho_bps": np.nan})
            continue
        rc = np.random.default_rng(RNG_GLOBAL + hash(("EXP-024", "single", "hedged", int(gi))) % 100_000)
        blk = max(1, int(hvec[li]))
        ci = ev.block_bootstrap_ci(rho, np.mean, block=blk, n_boot=N_BOOT_ROBUST, n_seeds=5)
        obs = float(np.mean(rho))
        perm_null = permuted_axis_null(r_i, N_PERM, rc)
        p_perm = float(np.mean(perm_null >= obs)) if perm_null.size else np.nan
        trip = tripwire_block_permute(r_i, BLOCK_TRIP, rc, N_TRIP)
        trip_mean = float(np.mean(trip)) if trip.size else np.nan
        cell_rows.append({**base, "mean_rho_bps": obs * BPS,
               "ci_low_bps": ci["ci"][0] * BPS, "ci_high_bps": ci["ci"][1] * BPS,
               "p_perm": p_perm,
               "tripwire_bps": trip_mean * BPS,
               "tripwire_collapse": ev.collapse_fraction(obs, trip_mean)})

    # Golden trace: first 3 all>k fade events after warmup (K_TRAIL_W bars)
    print("[4/5] golden trace ...")
    golden = []
    for r in rows_allk:
        if r[0] < K_TRAIL_W:
            continue
        t, gi, li_local, hi = r[0], r[1], r[8], r[3]
        k1 = t + 1
        with np.errstate(invalid="ignore", divide="ignore"):
            g = np.log(O[k1 + hi] / O[k1])
        fpres = present[t] & np.isfinite(g)
        gp = g[fpres]
        G_t = float(np.median(gp))
        u_row = U[t]
        present_idx = np.where(present[t])[0]
        golden.append({
            "CloseTime": str(times[t]), "instrument": DISPLAY[MEMBERS[gi]], "t_index": int(t),
            "present": ",".join(DISPLAY[MEMBERS[j]] for j in present_idx),
            "u_j": ";".join(f"{DISPLAY[MEMBERS[j]]}={float(u_row[j]):.6f}" for j in present_idx),
            "m_median": float(np.nanmedian(np.where(present[t], u_row, np.nan))),
            "s_i": r[2], "k_thr": float(k_thr[t]),
            "abs_s_gt_k": bool(abs(r[2]) >= k_thr[t]),
            "fade": r[5], "h": hi, "g_i": float(g[li_local]), "G": G_t,
            "idio": float(r[7][li_local]), "rho": r[4], "rho_bps": r[4] * BPS})
        if len(golden) >= 3:
            break

    # Write results
    print("[5/5] writing results ...")
    sx = SUFFIX
    pl.DataFrame(sub_rows).write_parquet(RESULTS / f"substrate{sx}.parquet")
    pl.DataFrame(sub_rows).write_csv(RESULTS / f"substrate{sx}.csv")
    dfc = pl.DataFrame(cell_rows, strict=False)
    dfc.write_parquet(RESULTS / f"cell_reads{sx}.parquet")
    scalar = [c for c, dt in zip(dfc.columns, dfc.dtypes) if not isinstance(dt, pl.List)]
    dfc.select(scalar).write_csv(RESULTS / f"cell_reads{sx}.csv")
    pl.DataFrame(rob_rows).write_parquet(RESULTS / f"robustness{sx}.parquet")
    pl.DataFrame(rob_rows).write_csv(RESULTS / f"robustness{sx}.csv")
    pl.DataFrame(holm_rows).write_parquet(RESULTS / f"holm{sx}.parquet")
    pl.DataFrame(holm_rows).write_csv(RESULTS / f"holm{sx}.csv")
    pl.DataFrame(golden).write_parquet(RESULTS / f"golden_trace{sx}.parquet")
    summary = {
        "experiment": "EXP-024", "family": "CF-CSRR-001", "branch": "HYP-002b",
        "construction": "R_US / anchor-S / median / raw / all>k / hedged",
        "union_bars": int(n), "train_frac": TRAIN_FRAC, "min_coverage": MIN_COVERAGE,
        "members": [DISPLAY[m] for m in MEMBERS], "min_members": MIN_MEMBERS,
        "n_seeds": N_SEEDS, "n_perm": N_PERM, "n_trip": N_TRIP, "block_trip": BLOCK_TRIP,
        "n_boot_full": N_BOOT_FULL, "n_boot_robust": N_BOOT_ROBUST,
        "k_trailing_window": K_TRAIL_W, "alpha": ALPHA,
        "span": [str(times[0]), str(times[-1])],
        "median_present_per_bar": int(np.median(present.sum(axis=1))),
        "n_valid_holm": n_valid_holm, "n_allk_events": len(rows_allk),
        "n_single_worst_events": len(rows_sw), "block_ge_h": True, "suffix": sx}
    (RESULTS / f"summary{sx}.json").write_text(json.dumps(summary, indent=2, default=str))
    print("      done. results in", RESULTS)


if __name__ == "__main__":
    main()
