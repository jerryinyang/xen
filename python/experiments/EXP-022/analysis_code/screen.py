"""EXP-022 — CF-CSRR-001 HYP-002 Indices consensus-residual reversion availability screen.

Data-analyst's OWN interrogation code (no experiment-local imports). Canonical xen only:
`xen.bar_aggregator.aggregate_ohlc` (1m->4h) and `xen.evaluation` (hardened CI/MDE, L-20).

Execution-agnostic availability screen: NO fills, NO P&L, NO cTrader, NO xen.adjudication
(nothing to reconcile). Integrity = causal <=t-1 provenance + leak tripwire + TRAIN-only
holdout fence (first 49%). See python/experiments/EXP-022/design.md.

Indices mirror of EXP-021. Differences:
  * 10-index equity basket, sigma_i = +1 for ALL members (single common factor: global equity
    risk); no USD-strength alignment. Plain median / equal-weight consensus is factor-coherent.
  * session-disjoint members -> PRESENT-MEMBER consensus (union CloseTime join; a bar enters a
    member's consensus only if that member is present; >=4 present required, >=2 in a bloc).
  * 3 basket builds: N naive (all present) | A activity-gated (drop inactive/off-session bars) |
    R regional blocs {US4 / EU3 / Asia3}.
  * 2 anchors: P common 00:00-UTC daily reset [PRIMARY] | S per-index session-open reset.

Construction (frozen):
  u_i(t)   = ln(Close_i(t)/anchor_i(t))                       [signal from confirmed close <= t]
  m(t)     = A_est({u_j : j present}); A in {median, mean}
  s_i(t)   = u_i - m; B in {raw, /sigma_t (cross-sec std)}
  k(t)     = trailing-median of per-bar max_i|s_i| (causal, <= t-1)
  HL_i     = AR(1) half-life of s_i; h_i = clip(round(2*HL_i),1,12)
  g_i(t,h) = ln(Open_i(t+1+h)/Open_i(t+1))                    [TRADED forward, OPEN-to-OPEN, L-01]
  G(t,h)   = A_est({g_j : j present, finite}); idio = g_i - G (hedged) | g_i (unhedged)
  rho      = -sign(s_i) * idio                                [+ => residual reverts in fade dir]
Cells = A(2) x B(2) x C{single-worst, all>k}(2) x D{hedged, unhedged}(2) = 16, per instrument.

PRIMARY significance family = build N x anchor P (full CI battery + max-stat over 16 cells).
Robustness overlays (build A, anchor S) + secondary arm (build R blocs) use a lighter CI.
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
EXP_DIR = ROOT / "python" / "experiments" / "EXP-022"
RESULTS = EXP_DIR / "results"
PLOTS = EXP_DIR / "plots"
DATA = ROOT / "data" / "timebars"

# 10 index members (file-stem symbol); sigma_i = +1 for ALL. Display name for reporting.
MEMBERS = ["ustec", "us500", "us2000", "us30", "jp225",
           "aus200", "stoxx50", "de40", "hk50", "uk100"]
DISPLAY = {"ustec": "USTEC", "us500": "US500", "us2000": "US2000", "us30": "US30",
           "jp225": "JP225", "aus200": "AUS200", "stoxx50": "EU50", "de40": "GER40",
           "hk50": "HK50", "uk100": "UK100"}
REGIONS = {"US": ["ustec", "us500", "us2000", "us30"],
           "EU": ["stoxx50", "de40", "uk100"],
           "ASIA": ["jp225", "aus200", "hk50"]}
# per-index session-open UTC hour, snapped to the 4h grid {0,4,8,12,16,20} (anchor S offset)
SESSION_HOUR = {"ustec": 12, "us500": 12, "us2000": 12, "us30": 12,     # NY cash open ~13:30
                "stoxx50": 8, "de40": 8, "uk100": 8,                    # London/Frankfurt ~07-08
                "jp225": 0, "aus200": 0, "hk50": 0}                     # Tokyo/Sydney/HK ~00-01:30
# liquid-session bar-hours per member (build A off-session gate)
LIQUID_HOURS = {"ustec": {12, 16, 20}, "us500": {12, 16, 20}, "us2000": {12, 16, 20},
                "us30": {12, 16, 20}, "stoxx50": {8, 12}, "de40": {8, 12}, "uk100": {8, 12},
                "jp225": {0, 4}, "aus200": {0, 4}, "hk50": {0, 4}}

# CLI: [min_coverage] [suffix] [period_minutes] — defaults reproduce the primary run.
MIN_COVERAGE = float(sys.argv[1]) if len(sys.argv) > 1 else 0.90
SUFFIX = sys.argv[2] if len(sys.argv) > 2 else ""
PERIOD_MIN = int(sys.argv[3]) if len(sys.argv) > 3 else 240
TRAIN_FRAC = 0.49             # first 70% analysis * first 70% train = first 49% of the file
K_TRAIL_W = 120               # trailing window (4h bars) for adaptive threshold k
ACT_TRAIL_W = 120             # trailing window for activity-gate TR percentile
ACT_PCT = 10.0                # drop bars with TR below this trailing percentile (build A)
N_SEEDS = 25                  # L-19 twin battery
N_PERM = 1000                 # permuted-axis null
N_TRIP = 300                  # tripwire block-permute reps
BLOCK_TRIP = 12               # temporal block for tripwire (>= max h)
N_BOOT_FULL = 10_000          # PRIMARY construction (L-20 hardened)
N_BOOT_ROBUST = 2_000         # robustness overlays (lighter; disclosed)
RNG_GLOBAL = 20260706
BPS = 1e4


# --------------------------------------------------------------------------- #
# I/O + per-member feature construction (natively, before the union join)
# --------------------------------------------------------------------------- #
def reset_anchor(times: np.ndarray, close: np.ndarray, offset_h: int) -> np.ndarray:
    """anchor[k] = close of the prior reset-period's last bar (causal). NaN before first reset.

    Reset rolls when the bar's (UTC hour) crosses `offset_h`: bucket = floor((t - offset_h) / day).
    offset_h=0 -> common 00:00-UTC daily reset (anchor P). offset_h=session hour -> anchor S.
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


def true_range(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
    """Per-bar true range TR = max(H-L, |H-prevC|, |L-prevC|)."""
    prevc = np.concatenate([[np.nan], close[:-1]])
    a = high - low
    b = np.abs(high - prevc)
    c = np.abs(low - prevc)
    return np.nanmax(np.column_stack([a, b, c]), axis=1)


def trailing_pct_active(tr: np.ndarray, hours: np.ndarray, liquid: set, w: int,
                        pct: float) -> np.ndarray:
    """Activity flag (build A): active if TR >= trailing pct-th percentile AND hour in liquid set.

    Trailing window strictly < t (causal). Warmup (insufficient window) -> inactive.
    """
    n = len(tr)
    active = np.zeros(n, dtype=bool)
    for t in range(n):
        if hours[t] not in liquid:
            continue
        lo = max(0, t - w)
        win = tr[lo:t]
        win = win[np.isfinite(win)]
        if len(win) >= 20 and np.isfinite(tr[t]) and tr[t] >= np.percentile(win, pct):
            active[t] = True
    return active


def load_member(symbol: str) -> pl.DataFrame:
    """Load 1m 5-year file, slice first TRAIN_FRAC (holdout-safe), 1m->4h, emit features."""
    f = sorted(DATA.glob(f"timebars_{symbol}_20210602_*.parquet"))[-1]
    df = pl.scan_parquet(f).sort("CloseTime").collect()
    cut = int(df.height * TRAIN_FRAC)              # only ever touch the first 49%
    df = df.head(cut)
    bars = aggregate_ohlc(df, period_minutes=PERIOD_MIN, min_coverage=MIN_COVERAGE)
    bars = bars.head(bars.height - 1)              # drop trailing partial window at train boundary
    t = bars["CloseTime"].to_numpy()
    c = bars["Close"].to_numpy().astype(float)
    h = bars["High"].to_numpy().astype(float)
    lo = bars["Low"].to_numpy().astype(float)
    hours = t.astype("datetime64[h]").astype("datetime64[ns]")
    hours = ((hours - t.astype("datetime64[D]").astype("datetime64[ns]"))
             / np.timedelta64(1, "h")).astype(int)
    aP = reset_anchor(t, c, 0)
    aS = reset_anchor(t, c, SESSION_HOUR[symbol])
    with np.errstate(divide="ignore", invalid="ignore"):
        uP = np.log(c / aP)
        uS = np.log(c / aS)
    tr = true_range(h, lo, c)
    act = trailing_pct_active(tr, hours, LIQUID_HOURS[symbol], ACT_TRAIL_W, ACT_PCT)
    return pl.DataFrame({
        "CloseTime": bars["CloseTime"],
        f"O_{symbol}": bars["Open"].cast(float),
        f"uP_{symbol}": uP, f"uS_{symbol}": uS, f"act_{symbol}": act,
    })


def build_panel() -> pl.DataFrame:
    """Outer (union) join all 10 members on shared 4h CloseTime; NaN where absent."""
    panel = None
    for s in tqdm(MEMBERS, desc="load members"):
        b = load_member(s)
        panel = b if panel is None else panel.join(b, on="CloseTime", how="full", coalesce=True)
    return panel.sort("CloseTime")


# --------------------------------------------------------------------------- #
# Substrate diagnostics
# --------------------------------------------------------------------------- #
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


# --------------------------------------------------------------------------- #
# Core construction over a PRESENT-member subset
# --------------------------------------------------------------------------- #
def consensus_resid(U: np.ndarray, present: np.ndarray, a_est: str, b_norm: str):
    """m(t), s_i(t) over present members only. Non-present entries -> NaN in s."""
    Um = np.where(present, U, np.nan)
    if a_est == "median":
        m = np.nanmedian(Um, axis=1)
    else:
        m = np.nanmean(Um, axis=1)
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


# --------------------------------------------------------------------------- #
# Events + estimand rho (present-aware)
# --------------------------------------------------------------------------- #
def build_rows(O: np.ndarray, present: np.ndarray, s: np.ndarray, k_thr: np.ndarray,
               valid: np.ndarray, sel: str, hvec: np.ndarray, a_est: str, hedged: bool,
               cols: np.ndarray):
    """Return per-event records over the present-member subset.

    Each record: (t, i_global, s_i, h, rho, fade, present_owner_idxs(local), idio_local(local)).
    `cols` maps local column index -> global member index (for build R blocs).
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
        h = int(hvec[cand[0]]) if sel == "single" else 0
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


# --------------------------------------------------------------------------- #
# Controls (present-aware, vectorized over reps)
# --------------------------------------------------------------------------- #
def _pack(rows):
    """Pack rows into padded arrays for vectorized permutation / twin resampling."""
    E = len(rows)
    fade = np.array([r[5] for r in rows])
    owner_local = np.array([r[8] for r in rows])
    idio_own = np.array([r[7][r[8]] for r in rows])
    maxK = max(len(r[6]) for r in rows)
    pad = np.full((E, maxK), -1, dtype=int)      # present local idxs
    idio = np.zeros((E, s_cols(rows)))
    for e, r in enumerate(rows):
        pi = r[6]
        pad[e, :len(pi)] = pi
        idio[e, :] = np.nan_to_num(r[7], nan=0.0)
    counts = np.array([len(r[6]) for r in rows])
    return fade, owner_local, idio_own, pad, counts, idio


def s_cols(rows):
    return len(rows[0][7])


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
    ar = np.arange(E)
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


# --------------------------------------------------------------------------- #
# Per-construction driver
# --------------------------------------------------------------------------- #
def run_construction(times, O_all, UP_all, US_all, ACT_all, members_local, anchor, build,
                     min_members, tag_build, golden_sink):
    """Compute substrate + 16-cell reads + controls for one (member-subset, anchor, build).

    Returns (substrate_rows, cell_rows, maxstat_rows). members_local = global indices in play.
    """
    cols = np.array(members_local)
    O = O_all[:, cols]
    U = (UP_all if anchor == "P" else US_all)[:, cols]
    base_present = np.isfinite(U) & np.isfinite(O)
    if build == "A":
        present = base_present & ACT_all[:, cols]
    else:
        present = base_present
    valid = present.sum(axis=1) >= min_members
    full_ci = (tag_build == "N" and anchor == "P")
    n_boot = N_BOOT_FULL if full_ci else N_BOOT_ROBUST

    A_LEVELS, B_LEVELS = ["median", "mean"], ["raw", "z"]
    C_LEVELS, D_LEVELS = ["single", "allk"], [True, False]
    sub_rows, cell_rows = [], []
    perm_cache = {}                     # (a,b,c,d) -> {global_i: (obs, null)}
    hl_cache = {}
    label = f"{tag_build}/{anchor}"

    # substrate + HL
    for a in A_LEVELS:
        for b in B_LEVELS:
            _, s = consensus_resid(U, present, a, b)
            for li, gi in enumerate(cols):
                si = s[valid, li]
                si = si[np.isfinite(si)]
                hl = ar1_halflife(si)
                hl_cache[(a, b, li)] = hl
                sub_rows.append({
                    "instrument": DISPLAY[MEMBERS[gi]], "build": tag_build, "anchor": anchor,
                    "A": a, "B": b, "n": int(len(si)),
                    "VR2": variance_ratio(si, 2), "VR6": variance_ratio(si, 6),
                    "autocorr1": (float(np.corrcoef(si[:-1], si[1:])[0, 1])
                                  if len(si) > 2 else np.nan),
                    "HL": hl,
                    "h": int(np.clip(round(2 * hl), 1, 12)) if np.isfinite(hl) else 6})

    # cell reads + controls
    rng = np.random.default_rng(RNG_GLOBAL + (0 if anchor == "P" else 7))
    for a in A_LEVELS:
        for b in B_LEVELS:
            m, s = consensus_resid(U, present, a, b)
            maxabs = np.where(valid, np.nanmax(np.where(present, np.abs(s), np.nan), axis=1),
                              np.nan)
            k_thr = trailing_threshold(maxabs, K_TRAIL_W)
            hvec = np.array([int(np.clip(round(2 * hl_cache[(a, b, li)]), 1, 12))
                             if np.isfinite(hl_cache[(a, b, li)]) else 6
                             for li in range(len(cols))])
            for c in C_LEVELS:
                for d in D_LEVELS:
                    rows = build_rows(O, present, s, k_thr, valid, c, hvec, a, d, cols)
                    if full_ci and (a, b, c, d) == ("median", "raw", "single", True):
                        for r in rows[:3]:
                            t, gi, si, h, rho, fade = r[0], r[1], r[2], r[3], r[4], r[5]
                            golden_sink.append({
                                "CloseTime": str(times[t]),
                                "instrument": DISPLAY[MEMBERS[gi]], "sign_i": 1,
                                "n_present": int(r[6].size), "m": float(m[t]),
                                "s_i": float(si), "fade_dir": float(fade), "h": int(h),
                                "entry_open": float(O[t + 1, r[8]]),
                                "exit_open": float(O[t + 1 + h, r[8]]), "rho": float(rho)})
                    by_inst = {}
                    for r in rows:
                        by_inst.setdefault(r[1], []).append(r)
                    for li, gi in enumerate(cols):
                        r_i = by_inst.get(int(gi), [])
                        rho = np.array([rr[4] for rr in r_i], dtype=float)
                        rho = rho[np.isfinite(rho)]
                        ne = len(rho)
                        base = {"instrument": DISPLAY[MEMBERS[gi]], "build": tag_build,
                                "anchor": anchor, "A": a, "B": b, "C": c,
                                "D": "hedged" if d else "unhedged", "n_events": ne}
                        if ne < 2:
                            cell_rows.append({**base, "mean_rho_bps": np.nan})
                            continue
                        rc = np.random.default_rng(RNG_GLOBAL + hash((label, a, b, c, d, int(gi)))
                                                   % 100_000)
                        ci = ev.block_bootstrap_ci(rho, block=ev.DEFAULT_BLOCK, n_boot=n_boot)
                        obs = float(np.mean(rho))
                        perm_null = permuted_axis_null(r_i, N_PERM, rc)
                        p_perm = float(np.mean(perm_null >= obs)) if perm_null.size else np.nan
                        ri = random_index_twin(r_i, N_SEEDS, rc)
                        rt = random_timing_twin(O, present, s, hvec, li, a, d, valid, ne,
                                                N_SEEDS, rc)
                        trip = tripwire_block_permute(r_i, BLOCK_TRIP, rc, N_TRIP)
                        ri_mean = float(np.nanmean(ri)) if ri.size else np.nan
                        rt_mean = float(np.nanmean(rt)) if rt.size else np.nan
                        rt_pct = float(np.mean(rt <= obs)) if rt.size else np.nan
                        trip_mean = float(np.mean(trip)) if trip.size else np.nan
                        perm_cache.setdefault((a, b, c, d), {})[int(gi)] = (obs, perm_null)
                        row = {**base, "mean_rho_bps": obs * BPS,
                               "ci_low_bps": ci["ci"][0] * BPS, "ci_high_bps": ci["ci"][1] * BPS,
                               "p_perm": p_perm,
                               "ri_twin_bps": ri_mean * BPS,
                               "ri_collapse": ev.collapse_fraction(obs, ri_mean),
                               "rt_twin_bps": rt_mean * BPS, "rt_percentile": rt_pct,
                               "rt_collapse": ev.collapse_fraction(obs, rt_mean),
                               "tripwire_bps": trip_mean * BPS,
                               "tripwire_collapse": ev.collapse_fraction(obs, trip_mean)}
                        if full_ci:
                            bs = ev.block_sensitivity(rho, [max(2, ev.DEFAULT_BLOCK // 2),
                                                            ev.DEFAULT_BLOCK, ev.DEFAULT_BLOCK * 2])
                            tm = ev.block_bootstrap_ci(rho, ev.trimmed_mean, n_boot=n_boot)
                            row["ci_low_seed_range_bps"] = [v * BPS for v in ci["ci_low_seed_range"]]
                            row["trimmed_mean_bps"] = tm["stat"] * BPS
                            row["tmean_ci_low_bps"] = tm["ci"][0] * BPS
                            row["block_sens_ci_low_bps"] = [r["ci"][0] * BPS for r in bs]
                            row["mde_bps"] = ev.mde(rho) * BPS
                        cell_rows.append(row)

    # max-stat family-wise p over the 16 cells, per instrument
    maxstat_rows = []
    for li, gi in enumerate(cols):
        obs_cells, nulls = [], []
        for cellkey, dd in perm_cache.items():
            if int(gi) in dd:
                o, nl = dd[int(gi)]
                obs_cells.append((cellkey, o))
                nulls.append(nl)
        if not nulls:
            continue
        L = min(len(x) for x in nulls)
        max_null = np.column_stack([x[:L] for x in nulls]).max(axis=1)
        for cellkey, o in obs_cells:
            maxstat_rows.append({"instrument": DISPLAY[MEMBERS[gi]], "build": tag_build,
                                 "anchor": anchor, "cell": "|".join(map(str, cellkey)),
                                 "obs_bps": o * BPS,
                                 "fw_p_maxstat": float(np.mean(max_null >= o))})
    return sub_rows, cell_rows, maxstat_rows


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main():
    RESULTS.mkdir(parents=True, exist_ok=True)
    PLOTS.mkdir(parents=True, exist_ok=True)
    print("[1/4] building panel ...")
    panel = build_panel()
    times = panel["CloseTime"].to_numpy()
    n = len(times)
    O_all = np.column_stack([panel[f"O_{s}"].to_numpy().astype(float) for s in MEMBERS])
    UP_all = np.column_stack([panel[f"uP_{s}"].to_numpy().astype(float) for s in MEMBERS])
    US_all = np.column_stack([panel[f"uS_{s}"].to_numpy().astype(float) for s in MEMBERS])
    ACT_all = np.column_stack([panel[f"act_{s}"].to_numpy().astype(bool) for s in MEMBERS])
    present_N = np.isfinite(UP_all) & np.isfinite(O_all)
    print(f"      union 4h bars={n}  span={times[0]}..{times[-1]}  "
          f"median present/bar={int(np.median(present_N.sum(axis=1)))}")

    all_idx = list(range(len(MEMBERS)))
    golden = []
    sub_all, cell_all, ms_all = [], [], []

    # builds N, A (all 10, min 4) x anchors P, S ; build R per bloc (min 2)
    plan = []
    for anchor in ["P", "S"]:
        plan.append((all_idx, anchor, "N", 4, "N"))
        plan.append((all_idx, anchor, "A", 4, "A"))
        for bloc, syms in REGIONS.items():
            plan.append(([MEMBERS.index(s) for s in syms], anchor, "N", 2, f"R_{bloc}"))

    for members_local, anchor, build, minm, tag in tqdm(plan, desc="constructions"):
        sr, cr, mr = run_construction(times, O_all, UP_all, US_all, ACT_all, members_local,
                                      anchor, build, minm, tag, golden)
        sub_all += sr
        cell_all += cr
        ms_all += mr

    sx = SUFFIX
    pl.DataFrame(sub_all).write_parquet(RESULTS / f"substrate{sx}.parquet")
    pl.DataFrame(sub_all).write_csv(RESULTS / f"substrate{sx}.csv")
    dfc = pl.DataFrame(cell_all, strict=False)
    dfc.write_parquet(RESULTS / f"cell_reads{sx}.parquet")
    scalar = [c for c, dt in zip(dfc.columns, dfc.dtypes) if not isinstance(dt, pl.List)]
    dfc.select(scalar).write_csv(RESULTS / f"cell_reads{sx}.csv")
    pl.DataFrame(ms_all).write_parquet(RESULTS / f"maxstat{sx}.parquet")
    pl.DataFrame(ms_all).write_csv(RESULTS / f"maxstat{sx}.csv")
    pl.DataFrame(golden).write_parquet(RESULTS / f"golden_trace{sx}.parquet")
    print(f"[2/4] substrate rows={len(sub_all)}  cell rows={len(cell_all)}  "
          f"maxstat rows={len(ms_all)}")

    summary = {
        "union_bars": int(n), "train_frac": TRAIN_FRAC,
        "members": [DISPLAY[m] for m in MEMBERS], "regions": REGIONS,
        "n_seeds": N_SEEDS, "n_perm": N_PERM, "n_boot_primary": N_BOOT_FULL,
        "n_boot_robust": N_BOOT_ROBUST, "k_trailing_window": K_TRAIL_W,
        "span": [str(times[0]), str(times[-1])],
        "median_present_per_bar": int(np.median(present_N.sum(axis=1))),
        "constructions": [f"{t[4]}/{t[1]}" for t in plan],
        "min_coverage": MIN_COVERAGE, "period_minutes": PERIOD_MIN, "suffix": sx,
    }
    (RESULTS / f"summary{sx}.json").write_text(json.dumps(summary, indent=2, default=str))
    print("[3/4] summary written")
    print("[4/4] done. results in", RESULTS)


if __name__ == "__main__":
    main()
