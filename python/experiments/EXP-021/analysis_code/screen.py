"""EXP-021 — CF-CSRR-001 HYP-001 Currencies consensus-residual reversion availability screen.

Data-analyst's OWN interrogation code (no experiment-local imports). Canonical xen only:
`xen.bar_aggregator.aggregate_ohlc` (1m->4h) and `xen.evaluation` (hardened CI/MDE, L-20).

Execution-agnostic availability screen: NO fills, NO P&L, NO cTrader, NO xen.adjudication
(nothing to reconcile). Integrity here = causal <=t-1 provenance + leak tripwire + TRAIN-only
holdout fence. See python/experiments/EXP-021/design.md.

Construction (operator-frozen 2026-07-06):
  members  = 7 USD pairs, signed to USD strength (quote sigma=-1, base sigma=+1); JPY crosses disclosure-only
  anchor   = session/daily-reset causal anchor (prior UTC day's last 4h close); residual accumulates intraday
  u_i(t)   = sigma_i * ln(Close_i(t)/anchor_i(t))                            [signal from confirmed close <= t]
  m(t)     = A_est({u_i});  A in {median, mean}
  s_i(t)   = u_i - m;       B in {raw, /sigma_t (cross-sec std z)}
  k(t)     = trailing-median of per-bar max_i|s_i| (causal, shifted)          [axis-G, one primary value]
  HL_i     = AR(1) half-life of s_i;  h_i = clip(round(2*HL_i),1,12)          [horizon from mechanism scale]
  g_i(t,h) = sigma_i * ln(Open_i(t+1+h)/Open_i(t+1))                          [TRADED forward, OPEN-to-OPEN, L-01]
  G(t,h)   = A_est({g_j});  idio = g_i - G (D=hedged) | g_i (D=unhedged)
  rho      = -sign(s_i(t)) * idio                                            [+ => residual reverts in fade dir]
Cells = A(2) x B(2) x C{single-worst, all>k}(2) x D{hedged, unhedged}(2) = 16, per 7 instrument strata.

Controls: random-index twin (>=25 seeds), random-timing battery (>=25 seeds, L-19 percentile),
permuted-axis within-bar identity null (PRIMARY, >=1000 perms, max-stat multiplicity),
tripwire = temporal block-permute of (s->forward-return) pairing (must collapse rho->0).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "python" / "src"))
from xen.bar_aggregator import aggregate_ohlc  # noqa: E402
from xen import evaluation as ev               # noqa: E402

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
EXP_DIR = ROOT / "python" / "experiments" / "EXP-021"
RESULTS = EXP_DIR / "results"
PLOTS = EXP_DIR / "plots"
DATA = ROOT / "data" / "timebars"

# USD-strength sign: +1 for USD-base pairs, -1 for USD-quote pairs
MEMBERS = {
    "eurusd": -1, "gbpusd": -1, "audusd": -1, "nzdusd": -1,   # USD-quote
    "usdjpy": +1, "usdchf": +1, "usdcad": +1,                 # USD-base
}
CROSSES = ["eurjpy", "gbpjpy", "audjpy"]      # disclosure-only

# Domain config: name -> (period_minutes, anchor reset unit, trailing-k window in domain bars)
# 4h = registered primary (daily-reset accumulation). 1d = DISCLOSURE-ONLY exploratory branch
# (NON-REGISTERED; family card fixes 4h-only) with WEEKLY reset to preserve accumulation semantics.
DOMAINS = {"4h": (240, "D", 120), "1d": (1440, "W", 20)}
DOMAIN = sys.argv[1] if len(sys.argv) > 1 else "4h"
PERIOD_MIN, RESET_UNIT, K_TRAIL_W = DOMAINS[DOMAIN]
SUFFIX = "" if DOMAIN == "4h" else f"_{DOMAIN}"
MIN_COVERAGE = 0.90
TRAIN_FRAC = 0.49             # first 70% analysis * first 70% train
N_SEEDS = 25                  # L-19 twin battery
N_PERM = 1000                 # permuted-axis null
BLOCK_TRIP = 12              # temporal block for tripwire (>= max h)
RNG_GLOBAL = 20260706


# --------------------------------------------------------------------------- #
# I/O + panel construction
# --------------------------------------------------------------------------- #
def load_4h_train(symbol: str) -> pl.DataFrame:
    """Load 1m 5-year file, slice to first TRAIN_FRAC (chronological, holdout-safe), 1m->domain."""
    f = sorted(DATA.glob(f"timebars_{symbol}_20210602_*.parquet"))[-1]
    df = pl.scan_parquet(f).sort("CloseTime").collect()
    cut = int(df.height * TRAIN_FRAC)          # only ever touch the first 49%
    df = df.head(cut)
    bars = aggregate_ohlc(df, period_minutes=PERIOD_MIN, min_coverage=MIN_COVERAGE)
    # drop final (possibly partial) window at the train boundary
    bars = bars.head(bars.height - 1)
    return bars.select("CloseTime", "Open", "Close").rename(
        {"Open": f"O_{symbol}", "Close": f"C_{symbol}"})


def build_panel() -> pl.DataFrame:
    """Inner-join all 7 members on shared 4h CloseTime; keep bars where all present."""
    panel = None
    for s in MEMBERS:
        b = load_4h_train(s)
        panel = b if panel is None else panel.join(b, on="CloseTime", how="inner")
    return panel.sort("CloseTime")


def daily_reset_anchor(times: np.ndarray, close: np.ndarray, unit: str = "D") -> np.ndarray:
    """anchor[k] = close of the prior reset-period's last bar (causal). NaN before the first reset.

    unit='D' -> daily reset (4h domain, accumulate intraday); 'W' -> weekly reset (1d domain,
    accumulate intra-week, = V1 Monday-open variant) to preserve the accumulated-dislocation
    semantics the operator chose (a daily reset on daily bars would degenerate to a 1-bar return).
    """
    bucket = times.astype(f"datetime64[{unit}]")
    anchor = np.full(close.shape, np.nan)
    prev_bucket_last = -1
    for k in range(len(bucket)):
        if k > 0 and bucket[k] != bucket[k - 1]:
            prev_bucket_last = k - 1        # last bar of the period that just ended
        if prev_bucket_last >= 0:
            anchor[k] = close[prev_bucket_last]
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
    """VR(q): var(q-step)/ (q*var(1-step)); <1 => mean-reverting."""
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
# Core construction: u, m, s, threshold
# --------------------------------------------------------------------------- #
def compute_state(panel: pl.DataFrame):
    """Return dict of arrays: times, close[inst], open[inst], u[inst] (signed accumulated move)."""
    times = panel["CloseTime"].to_numpy()
    syms = list(MEMBERS)
    close = {s: panel[f"C_{s}"].to_numpy().astype(float) for s in syms}
    openp = {s: panel[f"O_{s}"].to_numpy().astype(float) for s in syms}
    u = {}
    for s in syms:
        anchor = daily_reset_anchor(times, close[s], RESET_UNIT)
        with np.errstate(divide="ignore", invalid="ignore"):
            u[s] = MEMBERS[s] * np.log(close[s] / anchor)
    U = np.column_stack([u[s] for s in syms])       # (n, 7)
    valid = np.all(np.isfinite(U), axis=1)           # bars with anchor + all present
    return {"times": times, "syms": syms, "close": close, "open": openp,
            "U": U, "valid": valid}


def consensus_resid(U: np.ndarray, a_est: str, b_norm: str):
    """m(t), s_i(t) for a given A estimator and B normalization."""
    if a_est == "median":
        m = np.nanmedian(U, axis=1)
    else:
        m = np.nanmean(U, axis=1)
    s = U - m[:, None]
    if b_norm == "z":
        sig = np.nanstd(U, axis=1, ddof=1)
        sig[sig <= 0] = np.nan
        s = s / sig[:, None]
    return m, s


def trailing_threshold(maxabs: np.ndarray, w: int) -> np.ndarray:
    """Causal trailing-median of the per-bar max|s| series (shifted by 1, uses <= t-1)."""
    n = len(maxabs)
    k = np.full(n, np.nan)
    for t in range(1, n):
        lo = max(0, t - w)
        window = maxabs[lo:t]                       # strictly < t
        window = window[np.isfinite(window)]
        if len(window) >= 10:
            k[t] = np.median(window)
    return k


# --------------------------------------------------------------------------- #
# Estimand: events + forward reversion rho
# --------------------------------------------------------------------------- #
def forward_signed_return(openp, syms, sign, i, k1, h):
    """g on ONE instrument i over [k1, k1+h] open-to-open (USD-signed)."""
    o = openp[syms[i]]
    return sign[i] * np.log(o[k1 + h] / o[k1])


def build_events(state, s, k_thr, sel, h_by_inst):
    """Yield event tuples (bar k, inst_idx i, resid s_i, h). C=single-worst | all>k."""
    U, valid = state["U"], state["valid"]
    n, nI = U.shape
    absr = np.abs(s)
    events = []
    for t in range(n - 1):                          # need t+1 open at least
        if not valid[t] or not np.isfinite(k_thr[t]):
            continue
        if sel == "single":
            i = int(np.nanargmax(absr[t]))
            if absr[t, i] >= k_thr[t]:
                events.append((t, i, s[t, i]))
        else:                                       # all>k
            for i in range(nI):
                if absr[t, i] >= k_thr[t]:
                    events.append((t, i, s[t, i]))
    return events


def rho_for_events(state, events, h_by_inst, a_est, hedged):
    """Compute rho per event + keep owner-idio matrix pieces for permutation null."""
    openp, syms = state["open"], state["syms"]
    sign = np.array([MEMBERS[s] for s in syms])
    n = state["U"].shape[0]
    nI = len(syms)
    O = np.column_stack([openp[s] for s in syms])   # (n,7)
    rows = []
    for (t, i, si) in events:
        h = int(h_by_inst[i])
        k1 = t + 1
        if k1 + h >= n:
            continue
        # signed forward returns for ALL instruments over this event's horizon
        with np.errstate(invalid="ignore", divide="ignore"):
            g = sign * np.log(O[k1 + h] / O[k1])     # (7,)
        if not np.all(np.isfinite(g)):
            continue
        G = np.median(g) if a_est == "median" else np.mean(g)
        idio_all = g - G if hedged else g            # (7,) idio per possible owner
        rho = -np.sign(si) * idio_all[i]
        rows.append((t, i, si, h, rho, -np.sign(si), idio_all))
    return rows


# --------------------------------------------------------------------------- #
# Controls
# --------------------------------------------------------------------------- #
def permuted_axis_null(rows, n_perm, rng):
    """Within-bar identity permutation: reassign idio owner among present instruments.

    rows carry idio_all (7,) so a permutation is a relabel of which instrument's forward idio
    pairs with the event's residual/sign. Returns null distribution of the cell mean rho.
    """
    if not rows:
        return np.array([])
    fade = np.array([r[5] for r in rows])            # -sign(s_i)
    owners = np.array([r[1] for r in rows])
    idio_mat = np.array([r[6] for r in rows])        # (E,7)
    E, nI = idio_mat.shape
    null = np.empty(n_perm)
    for p in range(n_perm):
        perm_owner = rng.integers(0, nI, size=E)     # random owner per event (within-bar identity swap)
        idio_sel = idio_mat[np.arange(E), perm_owner]
        null[p] = np.mean(fade * idio_sel)
    return null


def random_index_twin(rows, n_seeds, rng):
    """Assign the fade to a random OTHER member (its own idio), excluding the true argmax owner."""
    if not rows:
        return np.array([])
    fade = np.array([r[5] for r in rows])
    owners = np.array([r[1] for r in rows])
    idio_mat = np.array([r[6] for r in rows])
    E, nI = idio_mat.shape
    means = np.empty(n_seeds)
    for s in range(n_seeds):
        j = rng.integers(0, nI - 1, size=E)
        j = j + (j >= owners)                        # skip the true owner -> uniform over the other 6
        means[s] = np.mean(fade * idio_mat[np.arange(E), j])
    return means


def random_timing_twin(state, inst_idx, s_col, n_events, h, a_est, hedged, n_seeds, rng):
    """Enter at random valid bars on the SAME instrument; fade dir = -sign(residual) at that bar.

    Uses the raw signed residual sign at the random bar (NOT thresholded) -> mostly near-consensus
    bars, so it isolates the dislocation-CONDITIONING vs random timing (L-13 caveat: reads
    spuriously negative near consensus; secondary to the permuted-axis null).
    """
    openp, syms = state["open"], state["syms"]
    sign = np.array([MEMBERS[s] for s in syms])
    n = state["U"].shape[0]
    O = np.column_stack([openp[s] for s in syms])
    valid = state["valid"]
    cand = np.where(valid[: n - h - 1] & np.isfinite(s_col[: n - h - 1]))[0]
    cand = cand[cand + 1 + h < n]
    if len(cand) == 0 or n_events == 0:
        return np.array([])
    means = np.empty(n_seeds)
    for seed in range(n_seeds):
        picks = rng.choice(cand, size=min(n_events, len(cand)), replace=False)
        vals = []
        for t in picks:
            k1 = t + 1
            with np.errstate(invalid="ignore", divide="ignore"):
                g = sign * np.log(O[k1 + h] / O[k1])
            if not np.all(np.isfinite(g)):
                continue
            G = np.median(g) if a_est == "median" else np.mean(g)
            idio = (g - G) if hedged else g
            vals.append(-np.sign(s_col[t]) * idio[inst_idx])   # own residual sign at the random bar
        means[seed] = np.mean(vals) if vals else np.nan
    return means


def tripwire_block_permute(rows, block, rng, n_perm=200):
    """Temporal block-permute the forward-idio (owner) series so residual pairs with unrelated time.

    Must collapse rho->0. Returns the null distribution of the cell mean under the destroy.
    """
    if not rows:
        return np.array([])
    fade = np.array([r[5] for r in rows])
    owners = np.array([r[1] for r in rows])
    idio_mat = np.array([r[6] for r in rows])
    idio_own = idio_mat[np.arange(len(rows)), owners]   # the real owner's idio, time-ordered
    E = len(idio_own)
    nb = int(np.ceil(E / block))
    out = np.empty(n_perm)
    for p in range(n_perm):
        starts = rng.integers(0, E, size=nb)
        idx = (starts[:, None] + np.arange(block)[None, :]).ravel()[:E] % E
        out[p] = np.mean(fade * idio_own[idx])
    return out


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main():
    RESULTS.mkdir(parents=True, exist_ok=True)
    PLOTS.mkdir(parents=True, exist_ok=True)
    print("[1/5] building panel ...")
    panel = build_panel()
    state = compute_state(panel)
    n_valid = int(state["valid"].sum())
    print(f"      aligned 4h bars={state['U'].shape[0]}  valid(all-present+anchor)={n_valid}"
          f"  span={state['times'][0]}..{state['times'][-1]}")

    syms = state["syms"]
    A_LEVELS = ["median", "mean"]
    B_LEVELS = ["raw", "z"]
    C_LEVELS = ["single", "allk"]
    D_LEVELS = [True, False]         # hedged, unhedged

    # ---- substrate (per instrument x A x B): VR + lag1 autocorr + HL ----
    substrate = []
    hl_cache = {}
    for a in A_LEVELS:
        for b in B_LEVELS:
            _, s = consensus_resid(state["U"], a, b)
            for i, sym in enumerate(syms):
                si = s[state["valid"], i]
                vr2 = variance_ratio(si, 2)
                vr6 = variance_ratio(si, 6)
                if len(si) > 2:
                    ac1 = float(np.corrcoef(si[:-1], si[1:])[0, 1])
                else:
                    ac1 = np.nan
                hl = ar1_halflife(si)
                hl_cache[(a, b, i)] = hl
                substrate.append({"instrument": sym, "A": a, "B": b, "VR2": vr2, "VR6": vr6,
                                  "autocorr1": ac1, "HL": hl,
                                  "h": int(np.clip(round(2 * hl), 1, 12)) if np.isfinite(hl) else 6})
    pl.DataFrame(substrate).write_parquet(RESULTS / f"substrate{SUFFIX}.parquet")
    print(f"[2/5] substrate done ({len(substrate)} instr x A x B rows)")

    # ---- estimand rho per cell x stratum, + controls ----
    cell_rows = []
    perm_cache = {}                  # (A,B,C,D) -> {inst: observed mean} for max-stat
    rng = np.random.default_rng(RNG_GLOBAL)
    golden = []
    for a in A_LEVELS:
        for b in B_LEVELS:
            m, s = consensus_resid(state["U"], a, b)
            maxabs = np.nanmax(np.abs(s), axis=1)
            maxabs[~state["valid"]] = np.nan
            k_thr = trailing_threshold(maxabs, K_TRAIL_W)
            h_by_inst = {i: (int(np.clip(round(2 * hl_cache[(a, b, i)]), 1, 12))
                             if np.isfinite(hl_cache[(a, b, i)]) else 6) for i in range(len(syms))}
            for c in C_LEVELS:
                events = build_events(state, s, k_thr, c, h_by_inst)
                for d in D_LEVELS:
                    rows_all = rho_for_events(state, events, h_by_inst, a, d)
                    # golden trace: first 3 single-worst events, primary cell
                    if (a, b, c, d) == ("median", "raw", "single", True):
                        for r in rows_all[:3]:
                            t, i, si, h, rho, fade, idio_all = r
                            golden.append({"CloseTime": str(state["times"][t]),
                                           "instrument": syms[i], "sign_i": int(MEMBERS[syms[i]]),
                                           "u_i": float(state["U"][t, i]), "m": float(m[t]),
                                           "s_i": float(si), "fade_dir": float(fade), "h": int(h),
                                           "entry_open": float(state["open"][syms[i]][t + 1]),
                                           "exit_open": float(state["open"][syms[i]][t + 1 + h]),
                                           "rho": float(rho)})
                    # per-instrument stratum reads
                    by_inst = {}
                    for r in rows_all:
                        by_inst.setdefault(r[1], []).append(r)
                    for i, sym in enumerate(syms):
                        r_i = by_inst.get(i, [])
                        rho = np.array([rr[4] for rr in r_i])
                        rho = rho[np.isfinite(rho)]
                        ne = len(rho)
                        if ne < 2:
                            cell_rows.append({"instrument": sym, "A": a, "B": b, "C": c,
                                              "D": "hedged" if d else "unhedged", "n_events": ne,
                                              "mean_rho_bps": np.nan})
                            continue
                        rng_c = np.random.default_rng(RNG_GLOBAL + hash((a, b, c, d, i)) % 10_000)
                        ci = ev.block_bootstrap_ci(rho, block=ev.DEFAULT_BLOCK)
                        bs = ev.block_sensitivity(rho, [max(2, ev.DEFAULT_BLOCK // 2),
                                                        ev.DEFAULT_BLOCK, ev.DEFAULT_BLOCK * 2])
                        tmean_ci = ev.block_bootstrap_ci(rho, ev.trimmed_mean)
                        mde = ev.mde(rho)
                        # controls (per instrument stratum)
                        perm_null = permuted_axis_null(r_i, N_PERM, rng_c)
                        ri_twin = random_index_twin(r_i, N_SEEDS, rng_c)
                        rt_twin = random_timing_twin(state, i, s[:, i], ne,
                                                     int(np.median([rr[3] for rr in r_i])),
                                                     a, d, N_SEEDS, rng_c)
                        trip = tripwire_block_permute(r_i, BLOCK_TRIP, rng_c)
                        obs = float(np.mean(rho))
                        p_perm = float(np.mean(perm_null >= obs)) if len(perm_null) else np.nan
                        ri_mean = float(np.nanmean(ri_twin)) if len(ri_twin) else np.nan
                        rt_mean = float(np.nanmean(rt_twin)) if len(rt_twin) else np.nan
                        rt_pct = (float(np.mean(rt_twin <= obs)) if len(rt_twin) else np.nan)
                        trip_mean = float(np.mean(trip)) if len(trip) else np.nan
                        BPS = 1e4
                        perm_cache.setdefault((a, b, c, d), {})[i] = (obs, perm_null)
                        cell_rows.append({
                            "instrument": sym, "A": a, "B": b, "C": c,
                            "D": "hedged" if d else "unhedged", "n_events": ne,
                            "mean_rho_bps": obs * BPS,
                            "ci_low_bps": ci["ci"][0] * BPS, "ci_high_bps": ci["ci"][1] * BPS,
                            "ci_low_seed_range_bps": [v * BPS for v in ci["ci_low_seed_range"]],
                            "trimmed_mean_bps": tmean_ci["stat"] * BPS,
                            "tmean_ci_low_bps": tmean_ci["ci"][0] * BPS,
                            "block_sens_ci_low_bps": [r["ci"][0] * BPS for r in bs],
                            "mde_bps": mde * BPS,
                            "p_perm": p_perm,
                            "ri_twin_bps": ri_mean * BPS, "ri_collapse": ev.collapse_fraction(obs, ri_mean),
                            "rt_twin_bps": rt_mean * BPS, "rt_percentile": rt_pct,
                            "rt_collapse": ev.collapse_fraction(obs, rt_mean),
                            "tripwire_bps": trip_mean * BPS,
                            "tripwire_collapse": ev.collapse_fraction(obs, trip_mean),
                        })
    df = pl.DataFrame(cell_rows, strict=False)
    df.write_parquet(RESULTS / f"cell_reads{SUFFIX}.parquet")
    scalar_cols = [c for c, dt in zip(df.columns, df.dtypes) if not isinstance(dt, pl.List)]
    df.select(scalar_cols).write_csv(RESULTS / f"cell_reads{SUFFIX}.csv")   # nested list cols parquet-only
    pl.DataFrame(golden).write_parquet(RESULTS / f"golden_trace{SUFFIX}.parquet")
    print(f"[3/5] cell reads done ({df.height} instrument x cell rows)")

    # ---- max-stat multiplicity: family-wise p over the 16 cells, per instrument ----
    maxstat = []
    for i, sym in enumerate(syms):
        obs_by_cell, null_by_cell = [], []
        for cellkey, d in perm_cache.items():
            if i in d:
                obs, null = d[i]
                obs_by_cell.append((cellkey, obs))
                null_by_cell.append(null)
        if not null_by_cell:
            continue
        L = min(len(x) for x in null_by_cell)
        null_mat = np.column_stack([x[:L] for x in null_by_cell])   # (L,16)
        max_null = null_mat.max(axis=1)
        for (cellkey, obs) in obs_by_cell:
            fw_p = float(np.mean(max_null >= obs))
            maxstat.append({"instrument": sym, "cell": "|".join(map(str, cellkey)),
                            "obs_bps": obs * 1e4, "fw_p_maxstat": fw_p})
    pl.DataFrame(maxstat).write_parquet(RESULTS / f"maxstat{SUFFIX}.parquet")
    print(f"[4/5] max-stat multiplicity done ({len(maxstat)} rows)")

    # ---- disclosure: naive quote-median (no USD alignment) substrate contrast ----
    summary = {
        "aligned_bars": int(state["U"].shape[0]), "valid_bars": n_valid,
        "train_frac": TRAIN_FRAC, "members": list(MEMBERS), "crosses_excluded": CROSSES,
        "n_seeds": N_SEEDS, "n_perm": N_PERM, "k_trailing_window": K_TRAIL_W,
        "span": [str(state["times"][0]), str(state["times"][-1])],
    }
    (RESULTS / f"summary{SUFFIX}.json").write_text(json.dumps(summary, indent=2))
    print("[5/5] done. results in", RESULTS)


if __name__ == "__main__":
    main()
