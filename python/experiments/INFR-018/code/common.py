"""Shared runner scaffolding for INFR-018 (universe, day-clustered inference, IO).

Kept out of ``xen.sigbar`` because it is orchestration, not apparatus: the
package holds reusable measurement primitives, this file holds this item's
wiring. Nothing here computes an accounting primitive (L-18 / critical-017) —
there is no P&L in this item at all.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from xen.evaluation import block_bootstrap_ci, block_sensitivity, trimmed_mean  # noqa: E402
from xen.sigbar.fences import (  # noqa: E402
    assert_frozen_inputs,
    build_universe,
    daily_turnover,
    load_admitted,
    load_bars,
    repo_root,
)

RESULTS = "python/experiments/INFR-018/results"

#: Frozen seeds. Every random draw in this item is regenerable from these plus
#: the declared construction, so QA can byte-diff a regeneration (EXP-019 D1).
SEED_PSEUDO_DAILY = 20180101
SEED_PSEUDO_FUND = 20180103
SEED_DERANGE = 20180105
SEED_CONTROL_MATCH = 20180107

#: Block length for the day-clustered bootstrap, in days. Multi-day momentum and
#: volatility clustering in crypto run at roughly this scale; the block
#: SENSITIVITY sweep (1/2x, 1x, 2x) is reported because no block length is
#: correct and a sign that flips across the sweep is not evidence (L-20).
DAY_BLOCK = 5


def out_dir() -> Path:
    d = repo_root() / RESULTS
    d.mkdir(parents=True, exist_ok=True)
    return d


def write_json(name: str, obj: Any) -> Path:
    """Emit an artifact with a UTC stamp; numbers go to disk, never only to prose."""
    p = out_dir() / name
    payload = {"item": "INFR-018", "generated_utc": datetime.now(timezone.utc).isoformat(), **obj}
    p.write_text(json.dumps(payload, indent=2, default=str))
    return p


# ---------------------------------------------------------------------------
# Universe
# ---------------------------------------------------------------------------


def membership_sha256(membership: pl.DataFrame) -> str:
    """Content hash of the realised panel (design §6.1 / §9 require it in the pin).

    Hashes the CSV rendering of the sorted table, NOT the parquet bytes: parquet
    carries writer metadata and is not byte-stable across runs, so a parquet hash
    would change while the membership did not, and the pin would be unfalsifiable.
    """
    if membership.height == 0:
        return hashlib.sha256(b"").hexdigest()
    body = (
        membership.sort(["day", "rank"]).select("day", "symbol", "rank").write_csv().encode()
    )
    return hashlib.sha256(body).hexdigest()


def panel_churn(membership: pl.DataFrame) -> dict:
    """Day-over-day turnover of the top-n panel (design §6.1: "plus the churn rate").

    ``churn_rate`` = mean over consecutive PANEL days of
    ``|members(d) \\ members(d-1)| / |members(d)|`` — the fraction of that day's
    panel that was not in the previous panel. The divisor is named because a
    reader would otherwise have to guess it (L-21). Pairs are consecutive days
    *in the panel*; the count of pairs that are also calendar-adjacent is reported
    so a gap in the bank cannot masquerade as stability.
    """
    if membership.height == 0:
        return {"churn_rate": None, "n_day_pairs": 0, "definition": "no panel days"}
    by_day = (
        membership.group_by("day").agg(pl.col("symbol")).sort("day")
    )
    days = by_day["day"].to_list()
    sets = [set(s) for s in by_day["symbol"].to_list()]
    n_full = max(len(s) for s in sets)
    fracs, full_fracs, adjacent = [], [], 0
    for i in range(1, len(days)):
        prev, cur = sets[i - 1], sets[i]
        if not cur:
            continue
        frac = len(cur - prev) / len(cur)
        fracs.append(frac)
        if len(cur) == n_full and len(prev) == n_full:
            full_fracs.append(frac)
        if (days[i] - days[i - 1]).days == 1:
            adjacent += 1
    sizes = [len(s) for s in sets]
    return {
        "churn_rate": float(np.mean(fracs)) if fracs else None,
        "n_day_pairs": len(fracs),
        "n_pairs_calendar_adjacent": adjacent,
        "definition": "mean over consecutive panel days of |members(d) \\ members(d-1)| / "
                      "|members(d)|; divisor is that day's panel size",
        # The headline rate averages panels of very different width — early in the
        # bank the panel is a handful of symbols, where one substitution is a huge
        # fraction. The population is disclosed beside the rate (QA run 6, I-51).
        "panel_size": {
            "max": n_full,
            "min": int(min(sizes)),
            "n_days_at_full_panel": int(sum(1 for s in sizes if s == n_full)),
            "n_days_below_full": int(sum(1 for s in sizes if s < n_full)),
            "n_days_below_half_full": int(sum(1 for s in sizes if s < n_full / 2)),
        },
        "churn_rate_full_panel_pairs_only": (
            float(np.mean(full_fracs)) if full_fracs else None
        ),
        "n_full_panel_pairs": len(full_fracs),
    }


def realise_universe(band: str = "DESIGN", *, limit: int | None = None) -> tuple[pl.DataFrame, dict]:
    """Build the online top-20 membership panel and its reconciliation record.

    Returns
    -------
    (membership, reconciliation)
        ``membership`` has one row per selected symbol-day. The reconciliation
        records the staged-vs-admitted delta with per-symbol reasons — the
        checkpoint pins 197 DESIGN-bank-covered admitted instruments while 200
        staging files carry DESIGN-bank bars, and an unexplained delta is a
        defect, not a rounding note.
    """
    root = repo_root()
    admitted = load_admitted(root)
    staged = sorted(p.stem for p in (root / "python/experiments/INFR-011/data/staging/bars").glob("*.parquet"))
    if limit:
        staged = staged[:limit]

    per_symbol: dict[str, pl.DataFrame] = {}
    staged_with_bars: list[str] = []
    unreadable: list[dict] = []
    for sym in staged:
        try:
            bars = load_bars(sym, band, root=root)
        except RuntimeError:
            # A BAND or HOLDOUT violation is a governance failure, not a corrupt
            # file, and must stop the run. Swallowing it here would reproduce the
            # INFR-017 7b(i) shape — a full-directory scan whose fence does not
            # stop the run — with the breach recorded as a data-quality note
            # (QA run 1, I-7).
            raise
        except Exception as exc:  # corrupt staging parquet — INFR-011 owns these
            unreadable.append({"symbol": sym, "reason": f"{type(exc).__name__}: {exc}"})
            continue
        if bars.height == 0:
            continue
        staged_with_bars.append(sym)
        if sym in admitted:
            per_symbol[sym] = daily_turnover(bars)

    membership = build_universe(per_symbol)
    recon = {
        "band": band,
        "n_staged_files_scanned": len(staged),
        "n_staged_with_band_bars": len(staged_with_bars),
        "n_admitted_with_band_bars": len(per_symbol),
        "staged_with_bars_not_admitted": sorted(set(staged_with_bars) - set(per_symbol)),
        "unreadable_staging_files": unreadable,
        "n_days": membership.select(pl.col("day").n_unique()).item() if membership.height else 0,
        "n_distinct_symbols_selected": (
            membership.select(pl.col("symbol").n_unique()).item() if membership.height else 0
        ),
        # Required by §6.1 and by the §9 registry block; neither existed before
        # (QA run 5, I-38b). The hash pins WHICH panel was realised, the churn
        # rate says how much of it turned over.
        "membership_sha256": membership_sha256(membership),
        "churn": panel_churn(membership),
        "rule": {
            "n": 20,
            "reeval": "daily 00:00 UTC",
            "statistic": "trailing-24h QUOTE turnover = sum(Volume * (H+L+C)/3), USDT",
            "causality": "turnover measured over day D ranks membership for day D+1 (<= t-1)",
            "eligibility": ">=1200 of 1440 trailing bars AND ADMITTED",
            "tie_break": "lexicographic by symbol",
            "delisting": "fails eligibility from that day forward; no backfill, no exclusion of prior days",
        },
    }
    return membership, recon


# ---------------------------------------------------------------------------
# A5 residualisation
# ---------------------------------------------------------------------------


def bar_metrics(bars: pl.DataFrame) -> pl.DataFrame:
    """Attach the four A5 metric columns the baselines were fitted on.

    ``delta_abs`` and ``delta_ratio`` are separate metrics by A5's explicit
    instruction — ``|delta|`` scales with volume, so a single baseline would
    conflate "a lot of aggression" with "a lot of trading".
    """
    return bars.with_columns(
        pl.col("Volume").alias("volume"),
        (pl.col("High") - pl.col("Low")).alias("range"),
        pl.col("Delta").abs().alias("delta_abs"),
        pl.when(pl.col("Volume") > 0)
        .then(pl.col("Delta") / pl.col("Volume"))
        .otherwise(None)
        .alias("delta_ratio"),
    )


def residualise_symbol(
    bars: pl.DataFrame, symbol: str, metrics: tuple[str, ...] = ("volume", "range", "delta_abs", "delta_ratio")
) -> pl.DataFrame:
    """Residualise a symbol's bars against the FROZEN A5 baselines.

    Loads only this symbol's rows from the pinned parquet. The hash of that file
    is verified at every entry point (``assert_frozen_inputs``), so a residual
    can never be computed against the discarded first fit.
    """
    from xen.sigbar.baselines import residualise

    root = repo_root()
    bl = pl.scan_parquet(root / "python/experiments/INFR-017/results/seasonal_baselines.parquet")
    sym_bl = bl.filter(pl.col("symbol") == symbol).collect()
    if sym_bl.height == 0:
        raise RuntimeError(f"no frozen A5 baseline for {symbol}; it is not among the 194 fitted")
    out = bar_metrics(bars)
    for m in metrics:
        out = residualise(out, sym_bl, m, time_col="OpenTime")
    return out


# ---------------------------------------------------------------------------
# Day-clustered inference
# ---------------------------------------------------------------------------


def day_series(df: pl.DataFrame, value_col: str, day_col: str = "day") -> tuple[np.ndarray, np.ndarray]:
    """Collapse symbol-sessions to one median value per calendar day.

    Sessions on the same UTC day across 20 crypto perpetuals share a market-wide
    shock, so they are not independent draws. Collapsing to the day and
    resampling days is the dependence-honest unit, and it is also the source's
    §6b requirement to bootstrap over episodes rather than raw events.
    """
    g = (
        df.drop_nulls(value_col)
        .group_by(day_col)
        .agg(pl.col(value_col).median().alias("v"), pl.len().alias("n"))
        .sort(day_col)
    )
    return g["v"].to_numpy(), g[day_col].to_numpy()


def paired_day_contrast(
    real: pl.DataFrame, control: pl.DataFrame, value_col: str = "asym"
) -> tuple[np.ndarray, np.ndarray]:
    """Per-day ``real − control`` on the days both arms cover.

    Pairing by day removes the common market shock before inference rather than
    modelling it, which is what makes a modest contrast readable at all.
    """
    r = (
        real.drop_nulls(value_col).group_by("day").agg(pl.col(value_col).median().alias("r"))
    )
    c = (
        control.drop_nulls(value_col).group_by("day").agg(pl.col(value_col).median().alias("c"))
    )
    j = r.join(c, on="day", how="inner").sort("day")
    return (j["r"] - j["c"]).to_numpy(), j["day"].to_numpy()


def day_clustered_ci(values: np.ndarray, *, seed: int = 0) -> dict:
    """Circular block bootstrap over the day series, with the required disclosures.

    Reports the interval and its per-seed spread, a block-sensitivity sweep, and
    a trimmed-mean robustness read. Phrased as *the interval excludes zero* —
    never as a p-value (L-20).
    """
    if len(values) == 0:
        return {"n": 0, "stat": None, "ci": [None, None], "unpowered": True}
    main = block_bootstrap_ci(values, np.median, block=DAY_BLOCK, seed=seed)
    trimmed = block_bootstrap_ci(values, trimmed_mean, block=DAY_BLOCK, seed=seed)
    sens = block_sensitivity(values, [max(1, DAY_BLOCK // 2), DAY_BLOCK, DAY_BLOCK * 2], stat=np.median, seed=seed)
    # Fragility is judged on the ZERO-EXCLUSION decision, not on the sign of the
    # lower bound alone: a negative effect whose interval opens across the sweep
    # ([-0.5,-0.1] -> [-0.5,+0.2]) keeps sign(ci_low) = -1 throughout and would
    # otherwise pass unflagged (QA run 1, I-24).
    excl = {bool(r["ci"][0] > 0 or r["ci"][1] < 0) for r in sens}
    return {
        **main,
        "ci_excludes_zero": bool(main["ci"][0] > 0 or main["ci"][1] < 0),
        "trimmed_mean_ci": trimmed["ci"],
        "block_sensitivity": [{"block_req": r["block_req"], "ci": r["ci"]} for r in sens],
        "block_fragile": len(excl) > 1,
    }


def mde_curve(values: np.ndarray, grid: list[float], *, seed: int = 0) -> dict:
    """Smallest planted shift whose day-clustered interval clears zero.

    The plant is co-designed with the band rather than fixed: the sweep is run on
    the realised sample, so the reported MDE is the detectable effect AT THIS n,
    per stratum, and is published BEFORE the real read (L-08, L-12 mode 3).
    """
    rows = []
    detected = None
    for s in grid:
        r = block_bootstrap_ci(values - float(np.median(values)) + s, np.median, block=DAY_BLOCK, seed=seed)
        ok = bool(r["ci"][0] > 0)
        rows.append({"planted": s, "ci": r["ci"], "detected": ok})
        if ok and detected is None:
            detected = s
    return {"n_days": len(values), "curve": rows, "mde": detected}


# ---------------------------------------------------------------------------
# HYP-I2 future-shift tripwire — survival adjudication (I-29 / I-34)
# ---------------------------------------------------------------------------

#: Same-sign material collapse: destroyed contrast still has |cf| above this
#: with the same sign as the raw contrast.
I2_CF_SURVIVAL = 0.25
#: HYP-I3 path-swap survival threshold (design §4.4) — same magnitude as I2's cf leg.
I3_CF_SURVIVAL = 0.25
#: Day-contrast correlation above this means the day pattern survived the destroy.
I2_DAY_CORR_SURVIVAL = 0.5


def adjudicate_i2_survival(
    *,
    contrast_raw: float | None,
    contrast_shifted: float | None,
    collapse_fraction: float | None,
    day_contrast_correlation: float | None,
) -> dict:
    """Re-derive HYP-I2 tripwire SURVIVAL from primitives (QA run 3, I-34).

    SURVIVAL := (same-sign collapse_fraction with |cf| > I2_CF_SURVIVAL)
             OR (|day_contrast_correlation| > I2_DAY_CORR_SURVIVAL)

    ``day_contrast_correlation`` is **required** (finite). A null/NaN correlation
    is not treated as "leg off" — that soft path was I-34's freeze bypass.
    Freeze and the race emitter must call the same function so a buggy emitter
    cannot write ``survives: false`` and pin through.
    """
    if collapse_fraction is None:
        raise ValueError("collapse_fraction is required for I2 survival adjudication")
    if day_contrast_correlation is None:
        raise ValueError(
            "day_contrast_correlation is required for I2 survival adjudication "
            "(null is not a free pass — I-34)"
        )
    if not np.isfinite(float(day_contrast_correlation)):
        raise ValueError(
            f"day_contrast_correlation must be finite, got {day_contrast_correlation!r}"
        )
    same_sign_material = bool(
        contrast_raw is not None
        and contrast_shifted is not None
        and float(contrast_raw) * float(contrast_shifted) > 0
        and abs(float(collapse_fraction)) > I2_CF_SURVIVAL
    )
    high_day_corr = bool(abs(float(day_contrast_correlation)) > I2_DAY_CORR_SURVIVAL)
    survives = bool(same_sign_material or high_day_corr)
    return {
        "same_sign_material": same_sign_material,
        "high_day_corr": high_day_corr,
        "survives": survives,
        "thresholds": {
            "cf_survival": I2_CF_SURVIVAL,
            "day_corr_survival": I2_DAY_CORR_SURVIVAL,
        },
    }


def adjudicate_i3_survival(
    *,
    S_raw: float | None,
    S_swapped: float | None,
    collapse_fraction: float | None,
) -> dict:
    """Re-derive HYP-I3 path-swap SURVIVAL from primitives (design §4.4 / QA I-59).

    SURVIVAL := |collapse_fraction| > I3_CF_SURVIVAL **with the same sign as S_raw**
    (equivalently: S_raw and S_swapped same sign and |S_swapped/S_raw| > threshold).

    Magnitude-only refusal was the AMENDMENT-4 trap on this gate: an opposite-sign
    destroy null is not a leak. Emitter and freeze both call this so a precomputed
    flag cannot bypass the sign clause.
    """
    if collapse_fraction is None:
        raise ValueError("collapse_fraction is required for I3 survival adjudication")
    if S_raw is None or S_swapped is None:
        raise ValueError(
            "S_raw and S_swapped are required for I3 survival adjudication "
            "(sign clause — QA I-59); magnitude alone is not survival"
        )
    if not np.isfinite(float(S_raw)) or not np.isfinite(float(S_swapped)):
        raise ValueError(f"S_raw/S_swapped must be finite, got {S_raw!r}/{S_swapped!r}")
    if not np.isfinite(float(collapse_fraction)):
        raise ValueError(f"collapse_fraction must be finite, got {collapse_fraction!r}")
    same_sign_material = bool(
        float(S_raw) * float(S_swapped) > 0
        and abs(float(collapse_fraction)) > I3_CF_SURVIVAL
    )
    return {
        "same_sign_material": same_sign_material,
        "survives": same_sign_material,
        "thresholds": {"cf_survival": I3_CF_SURVIVAL},
    }
