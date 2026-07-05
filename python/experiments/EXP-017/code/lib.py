"""
EXP-017 — CF-MR-005/HYP-002 episode-native mechanism probe (ANALYSIS-ONLY, L-16/L-17).

The P&L-bearing object is the EPISODE: a maximal contiguous span of bars with Position != 0 in
one (cell, exit, arm, z*) emission. Episode net = sum of engine-realized per-bar NET bps over
the span (audited EXP-014c `assemble_realized_bps`: MTM L-09, cost once per entry L-02).

Causal provenance contract: every episode statistic reads only emitted engine values at bars
inside the episode's span (all ≤ the EXP-013 49% TRAIN fence by construction of the source
runs); START features read the FIRST leg's entry-time conditioners, which the engine computed
from ≤ t-1 confirmed bars. The passive comparator is a labelled NON-TRADABLE price-path
diagnostic: 1 unit, the episode's initial direction, marked open-to-open on the same emission's
RealOpen column over the same span, charged 1x the frozen per-instrument cost.

No frozen-referee calls anywhere in this experiment (L-17).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "python" / "src"))

# EXP-014c's audited loaders/series — loaded by explicit path (both files are named lib.py)
import importlib.util as _ilu                            # noqa: E402

_spec = _ilu.spec_from_file_location(
    "lib14c", ROOT / "python" / "experiments" / "EXP-014c" / "code" / "lib.py")
lib14c = _ilu.module_from_spec(_spec)
sys.modules["lib14c"] = lib14c          # dataclass decorator resolves module by name
_spec.loader.exec_module(lib14c)

# --------------------------------------------------------------------------- #
# Constants (frozen)
# --------------------------------------------------------------------------- #
SEED_BOOT = 20260703
SEED_PERM = 20260705
N_BOOT = 10_000
N_PERM = 5_000
BLOCK_EPISODES = 5
MIN_EPISODES = 30
ALPHA = 0.05
PRIMARY_CELLS = ("US2000", "AUDUSD", "NZDUSD")
ALL_CELLS = lib14c.S8_CELLS
FEATURES = ("abs_entry_z", "entry_sigma", "trend_aligned_z", "vol_regime", "horizon_bars")

# stratum -> (etag, run source note). e0 lives in the EXP-014b dirs via lib14c.run_root.
STRATA_EXITS = ("e3", "e2", "e0")


@dataclass
class Episode:
    start_i: int                 # index into the per-bar series (bars[:-1] frame)
    end_i: int                   # inclusive
    net_bps: float               # sum of per-bar net over span
    passive_bps: float           # non-tradable diagnostic comparator
    direction: int               # initial position sign
    n_bars: int
    n_legs: int
    max_level: int
    mae_bps: float               # min cumulative net within span (<=0)
    underwater_bars: int         # bars until cumulative net first > 0 (span length if never)
    year: int
    censored: bool               # touches the last bar of the series (open at fence)
    # START-known features (first leg's entry-time conditioners, engine-computed <= t-1)
    abs_entry_z: float
    entry_sigma: float
    trend_aligned_z: float
    vol_regime: float
    horizon_bars: float
    add_bars: tuple = ()         # bar indices of ladder adds (for the A1 destroy)


# --------------------------------------------------------------------------- #
# Episode reconstruction (sequential/stateful — deliberately not vectorized)
# --------------------------------------------------------------------------- #
def build_episodes(cell: "lib14c.Cell", cost: float) -> list[Episode]:
    """Split one emission into episodes and attach net/passive/features per episode."""
    df = cell.positions.sort("SourceCloseTime")
    _, pos, net = lib14c.assemble_realized_bps(df, cost_bps=cost)
    open_ = df.get_column("RealOpen").to_numpy().astype(float)
    sct = df.get_column("SourceCloseTime").to_numpy()[:-1]
    log_open = np.log(open_)
    cis = cell.cis_trades.sort("EntryTime") if cell.cis_trades.height else cell.cis_trades

    episodes: list[Episode] = []
    n = len(pos)
    i = 0
    while i < n:
        if pos[i] == 0.0:
            i += 1
            continue
        j = i
        while j + 1 < n and pos[j + 1] != 0.0:
            j += 1
        span = net[i:j + 1]
        cum = np.cumsum(span)
        direction = int(np.sign(pos[i]))
        uw = int(np.argmax(cum > 0.0)) if np.any(cum > 0.0) else len(cum)
        t_lo, t_hi = sct[i], sct[j]
        legs = (cis.filter((pl.col("EntryTime") >= t_lo) & (pl.col("EntryTime") <= t_hi))
                if cis.height else pl.DataFrame())
        # A1-M2 comparator: size-and-time-matched passive — one unit per ladder leg, entered
        # at the RealOpen of the leg's entry bar (market, same bar as the fill), held to the
        # episode end mark (next open after bar j), 1x cost per unit. Same exposure bars and
        # unit count as the ladder; NON-TRADABLE diagnostic.
        if legs.height:
            ent_np = legs.get_column("EntryTime").to_numpy()
            add_bars = np.clip(np.searchsorted(sct[i:j + 1], ent_np, side="left") + i, i, j)
            passive = float(np.sum(direction * (log_open[j + 1] - log_open[add_bars])
                                   * 10_000.0 - cost))
        else:
            add_bars = np.array([i])
            passive = direction * (log_open[j + 1] - log_open[i]) * 10_000.0 - cost
        first = legs.row(0, named=True) if legs.height else None
        episodes.append(Episode(
            start_i=i, end_i=j, net_bps=float(span.sum()), passive_bps=float(passive),
            direction=direction, n_bars=int(j - i + 1), n_legs=int(legs.height),
            max_level=int(legs.get_column("LadderLevel").max()) if legs.height else 0,
            mae_bps=float(min(cum.min(), 0.0)), underwater_bars=uw,
            year=int(str(t_lo)[:4]), censored=bool(j == n - 1),
            add_bars=tuple(int(b) for b in add_bars),
            abs_entry_z=abs(float(first["EntryZ"])) if first else float("nan"),
            entry_sigma=float(first["EntrySigma"]) if first else float("nan"),
            trend_aligned_z=(float(first["EntryTrendZ"]) * direction) if first else float("nan"),
            vol_regime=float(first["EntryVolRegime"]) if first else float("nan"),
            horizon_bars=float(first.get("HorizonBars", float("nan")) or float("nan"))
            if first else float("nan")))
        i = j + 1
    return episodes


def completed(eps: list[Episode]) -> list[Episode]:
    return [e for e in eps if not e.censored]


# --------------------------------------------------------------------------- #
# M2 — structure increment (paired, moving-block bootstrap over episodes)
# --------------------------------------------------------------------------- #
def block_boot_ci(x: np.ndarray, stat, n_boot: int = N_BOOT, block: int = BLOCK_EPISODES,
                  seed: int = SEED_BOOT) -> tuple[float, float, float]:
    """(stat, lo, hi) moving-block bootstrap over episode order (episodes are time-ordered)."""
    n = len(x)
    if n == 0:
        return (float("nan"),) * 3
    rng = np.random.default_rng(seed)
    n_blocks = int(np.ceil(n / block))
    starts = rng.integers(0, max(n - block, 1), size=(n_boot, n_blocks))
    stats = np.empty(n_boot)
    for b in range(n_boot):
        idx = (starts[b][:, None] + np.arange(block)[None, :]).ravel()[:n] % n
        stats[b] = stat(x[idx])
    return (float(stat(x)), float(np.quantile(stats, ALPHA / 2)),
            float(np.quantile(stats, 1 - ALPHA / 2)))


def m2_increment(eps: list[Episode]) -> dict:
    d = np.array([e.net_bps - e.passive_bps for e in eps])
    med = block_boot_ci(d, np.median)
    mean = block_boot_ci(d, np.mean)
    return {"n": len(d), "median": med[0], "median_ci": [med[1], med[2]],
            "mean": mean[0], "mean_ci": [mean[1], mean[2]],
            "frac_positive": float(np.mean(d > 0)) if len(d) else float("nan")}


def m2_addbar_null(eps: list[Episode], series_open: np.ndarray, cost: float,
                   n_draws: int = 200, seed: int = 20260706) -> dict:
    """A1 destroy: matched passive recomputed with each add at a uniformly random bar in the
    episode span (same unit count). Null band of the stratum-median Delta under 'add timing is
    irrelevant'; collapse fraction disclosed (L-15)."""
    log_open = np.log(series_open)
    rng = np.random.default_rng(seed)
    d_obs = np.array([e.net_bps - e.passive_bps for e in eps])
    obs = float(np.median(d_obs)) if len(d_obs) else float("nan")
    null_meds = []
    for _ in range(n_draws):
        d = []
        for e in eps:
            k = max(len(e.add_bars), 1)
            bars = rng.integers(e.start_i, e.end_i + 1, size=k)
            passive = float(np.sum(e.direction * (log_open[e.end_i + 1] - log_open[bars])
                                   * 10_000.0 - cost))
            d.append(e.net_bps - passive)
        null_meds.append(np.median(d))
    null_arr = np.asarray(null_meds)
    band = [float(np.quantile(null_arr, ALPHA / 2)),
            float(np.quantile(null_arr, 1 - ALPHA / 2))]
    inside = bool(band[0] <= obs <= band[1])
    collapse = float(np.median(null_arr) / obs) if abs(obs) > 1e-9 else float("nan")
    return {"n_draws": n_draws, "obs_median": obs, "null_band": band,
            "obs_inside_null_band": inside, "collapse_fraction": collapse}


# --------------------------------------------------------------------------- #
# M3 — start-feature predictability (Spearman + feature-label permutation null)
# --------------------------------------------------------------------------- #
def _rank(a: np.ndarray) -> np.ndarray:
    order = np.argsort(a, kind="mergesort")
    r = np.empty(len(a))
    r[order] = np.arange(len(a), dtype=float)
    # average ties
    vals, inv, cnt = np.unique(a, return_inverse=True, return_counts=True)
    sums = np.zeros(len(vals))
    np.add.at(sums, inv, r)
    return sums[inv] / cnt[inv]


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    rx, ry = _rank(x), _rank(y)
    sx, sy = rx.std(), ry.std()
    if sx == 0 or sy == 0:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


def m3_predictability(eps: list[Episode]) -> dict:
    y = np.array([e.net_bps for e in eps])
    rng = np.random.default_rng(SEED_PERM)
    out: dict = {}
    pvals: dict[str, float] = {}
    for f in FEATURES:
        x = np.array([getattr(e, f) for e in eps])
        ok = np.isfinite(x) & np.isfinite(y)
        if ok.sum() < MIN_EPISODES or np.nanstd(x[ok]) == 0:
            out[f] = {"n": int(ok.sum()), "rho": float("nan"), "status": "UNPOWERED"}
            continue
        xo, yo = x[ok], y[ok]
        rho = spearman(xo, yo)
        null = np.array([spearman(rng.permutation(xo), yo) for _ in range(N_PERM)])
        p = float(np.mean(np.abs(null) >= abs(rho)))
        band = [float(np.quantile(null, ALPHA / 2)), float(np.quantile(null, 1 - ALPHA / 2))]
        collapse = float(np.median(np.abs(null)) / abs(rho)) if abs(rho) > 1e-12 else float("nan")
        out[f] = {"n": int(ok.sum()), "rho": float(rho), "perm_p": p, "null_band": band,
                  "collapse_fraction": collapse}
        pvals[f] = p
    holm = lib14c.holm(pvals) if pvals else {}
    for f, adm in holm.items():
        out[f]["holm_significant"] = bool(adm)
    return out


# --------------------------------------------------------------------------- #
# M1 / M4 — descriptive anatomy + tail census
# --------------------------------------------------------------------------- #
def m1_anatomy(eps: list[Episode]) -> dict:
    net = np.array([e.net_bps for e in eps])
    lvl = np.array([e.max_level for e in eps])
    legs = np.array([e.n_legs for e in eps])
    dur = np.array([e.n_bars for e in eps])
    by_level = {int(v): {"n": int((lvl == v).sum()), "mean": float(net[lvl == v].mean()),
                         "sum": float(net[lvl == v].sum())} for v in sorted(set(lvl))}
    terc = np.quantile(dur, [1 / 3, 2 / 3]) if len(dur) else [0, 0]
    dbin = np.digitize(dur, terc)
    by_dur = {int(b): {"n": int((dbin == b).sum()), "mean": float(net[dbin == b].mean())}
              for b in sorted(set(dbin))}
    return {"by_max_level": by_level, "by_duration_tercile": by_dur,
            "multi_leg_share_of_net": float(net[legs >= 2].sum() / net.sum())
            if abs(net.sum()) > 1e-9 else float("nan"),
            "mean_legs": float(legs.mean()) if len(legs) else float("nan")}


def m4_tail(eps: list[Episode]) -> dict:
    net = np.sort(np.array([e.net_bps for e in eps]))
    mae = np.array([e.mae_bps for e in eps])
    total = float(net.sum())
    topk = {}
    for k in (1, 3, 5):
        topk[k] = float(net[:-k].sum()) if len(net) > k else float("nan")
    lvl = np.array([e.max_level for e in eps])
    yr = np.array([e.year for e in eps])
    per_year = {int(y): float(np.array([e.net_bps for e in eps if e.year == y]).sum())
                for y in sorted(set(yr))}
    return {"n": len(net), "total_bps": total,
            "q01": float(np.quantile(net, 0.01)) if len(net) else float("nan"),
            "q05": float(np.quantile(net, 0.05)) if len(net) else float("nan"),
            "mae_q05": float(np.quantile(mae, 0.05)) if len(mae) else float("nan"),
            "mae_worst": float(mae.min()) if len(mae) else float("nan"),
            "underwater_med": float(np.median([e.underwater_bars for e in eps])),
            "net_without_top_k_winners": topk,
            "share_from_L2plus": float(net[np.argsort(net)].sum() and
                                       np.array([e.net_bps for e in eps if e.max_level >= 2]
                                                ).sum() / total) if abs(total) > 1e-9
            else float("nan"),
            "per_year_bps": per_year}
