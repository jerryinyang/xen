"""INFR-014 Bybit/Nautilus XENA CAL harness — INFR-009 P-C form, re-measured.

> **LEGACY CAL APPARATUS (INFR-022).** This module and its siblings
> (``calibration_p3b`` / ``calibration_p3d`` / ``calibration_pc`` / ``calibration_bybit15`` /
> ``calibration``) are the pre-INFR-022 calibration stack. They are **not bindable on the
> live research path** without a post-INFR-022 CAL redesign. Retired names used here for
> historical replay only: ``bybit_round_trip_cost_bps`` (now in ``evaluation_cost_legacy``),
> ``PARTIAL_FEES_FUNDING_ONLY`` cost scope, ``g_net`` stage-1 selection (L-26
> net-cost-binding), the ``n_legs_floor`` / AMENDMENT-7 domain guards, and the
> ``stage2_net_lcb_positive`` deployability binding. Under INFR-022 the programme is
> zero-cost and gross-only; none of the above may bind on a live experiment.

Binder form constants §5.4 verbatim; α̂ re-measured under net-cost-binding stage-1
(L-26) — historical record; the live selection path is gross-only after INFR-022.
Chapter-03 pin db87dc1a… is VOID — never loaded as binding.

Class-shaped nulls: CLS-FILTER (BASE+FILT thinning) and CLS-EPISODE (episode objects).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable

import numpy as np
import polars as pl

import xen.xena.calibration_p3b as p3b
from xen.evaluation_cost_legacy import bybit_round_trip_cost_bps  # ARCHIVED (INFR-022)
from xen.xena.calibration import SegmentLayout, path_universe, regime_gbm_path
from xen.xena.calibration_p3b import HIGH, LOW, CadenceSpec, ScaleSpec, bank_seeds
from xen.xena.calibration_p3d import binomial_se, eval_lcb_legs, wilson
from xen.xena.calibration_pc import (
    BLOCK_LEGS,
    EMBARGO_FRAC,
    N_BOOT,
    STAGE_RANKING_FRAC,
    STAGE_SEARCH_FRAC,
    c_layout,
    deplant_stage2,
)
from xen.xena.certify import certify_and_rank, contiguous_purged_folds
from xen.xena.fill_basis import next_open_discriminating_control
from xen.xena.high_cadence_null import HighCadenceNullSpec, build_high_cadence_null
from xen.xena.oracle import CandidateStream, OracleConfig
from xen.xena.search import SearchParams, run_restart

ALPHA = 0.05
NS = 1_000_000_000
SCHEMA_ID = "xena.infr014.bybit_pc_registry.v1"

# §5.4 form constants (inherited, not invented)
BITE_EDGE_BPS = 20.0
BITE_N = 8
BITE_SURVIVAL_MAX = 0.125
BITE_SELECT_MIN = 0.5
_SELECTION_INFLATION_MAX = 0.02

# Disjoint Bybit banks (design §5.2) — never reuse chapter-03 seeds
DESIGN_SEEDS = {"low": 91_000, "high": 92_000}
CONFIRM_SEEDS = {"low": 93_000, "high": 94_000}
BITE_SEEDS = {"low": 951_000, "high": 952_000}

DESIGN_SCALE = ScaleSpec("design", n_null=80, n_cand=64, budget=200, n_restarts=5,
                         n_power=6, n_coverage=80)
CONFIRM_SCALE = ScaleSpec("confirm", n_null=200, n_cand=64, budget=200, n_restarts=5,
                          n_power=6, n_coverage=200)

# Synthetic cost defaults (design §6.1)
# Spread is not charged anywhere in the programme (no quote/effective spread exists on the
# Bybit T1 lane and a fixed pin is not a substitute). The former GAP_SPREAD_BPS = 5.0 proxy
# is retired; the cost stack is fees + discrete funding only.
FUNDING_BPS_PER_8H = 1.0  # conservative GAP default
HOLD_DEFAULT_H = {"low": 8.0, "high": 2.0}
CLASS_IDS = ("CLS-FILTER", "CLS-EPISODE")
_PLANT_PREFIXES = ("plant", "HCPLANT", "filtplant", "epplant")

VOID_PRIORS = [
    "db87dc1a",  # chapter-03 pc_frozen_registry (VOID on Bybit)
    "537d691a",  # INFR-006 v3 extensive-F (superseded)
]


class IntegrityError(RuntimeError):
    """Hard integrity refuse (L-26 costless stage-1, seed collision, schema)."""


def _set_seeds(low: int, high: int) -> None:
    p3b.SEED_BASE_LOW = low
    p3b.SEED_BASE_HIGH = high


def assert_stage1_net_binding(*, charge_costs: bool, score_kind: str) -> None:
    """LEGACY L-26 guard (historical CAL semantics — retained verbatim for tests/replay).

    INFR-022 supersedes net-cost-binding selection programme-wide; live callers must use
    :func:`assert_stage1_zero_cost` instead. This function keeps its historical behavior
    only inside the bannered legacy CAL apparatus.
    """
    if not charge_costs or score_kind != "g_net":
        raise IntegrityError(
            "CLS-* forbids costless stage-1 — L-26 "
            f"(charge_costs={charge_costs}, score_kind={score_kind!r})"
        )


def assert_stage1_zero_cost(*, charge_costs: bool, score_kind: str) -> None:
    """INFR-022 zero-cost stage-1 guard: live CAL selection is gross-only."""
    if charge_costs or score_kind != "g_gross":
        raise IntegrityError(
            "INFR-022 zero-cost model: stage-1 must be gross-only "
            f"(charge_costs={charge_costs}, score_kind={score_kind!r}) — "
            "the net-cost-binding selection path (L-26) is retired"
        )


def bybit_cost_bps_for_hold(
    symbol: str,
    *,
    hold_hours: float,
    entry_price: float = 100.0,
    funding_bps_per_8h: float = FUNDING_BPS_PER_8H,
) -> float:
    """COST-STACK via bybit_round_trip_cost_bps (design §6).

    Fees + discrete funding only; spread is not charged (programme-wide policy). This lane's
    costs are therefore identical in scope to every other lane's.
    """
    out = bybit_round_trip_cost_bps(
        symbol,
        entry_price,
        liquidity="taker",
        funding_bps_per_8h=funding_bps_per_8h,
        hold_hours=hold_hours,
        funding_coverage="GAP",
    )
    return float(out["total_bps"])


def _apply_stream_cost(s: CandidateStream, cost_bps: float) -> CandidateStream:
    return CandidateStream(
        s.candidate_id, s.symbol, s.trades, s.marks, float(cost_bps), s.money_per_unit
    )


def _hold_hours_from_trades(trades: pl.DataFrame, default_h: float) -> float:
    if trades.height == 0 or "EntryTime" not in trades.columns:
        return default_h
    et = trades.get_column("EntryTime").to_numpy().astype(np.int64)
    xt = trades.get_column("ExitTime").to_numpy().astype(np.int64)
    hours = (xt - et).astype(float) / (3600.0 * NS)
    hours = hours[np.isfinite(hours) & (hours > 0)]
    if len(hours) == 0:
        return default_h
    return float(max(1.0 / 60.0, float(np.median(hours))))


# --------------------------------------------------------------------------- #
# CLS-FILTER null / plant factory
# --------------------------------------------------------------------------- #
def make_filter_null_universe(
    seed: int,
    cadence: CadenceSpec,
    *,
    n_candidates: int = 64,
    edge_bps: float = 0.0,
    plant: bool = False,
) -> list[CandidateStream]:
    """CLS-FILTER: mix of BASE (high cadence) + FILT (same entries thinned by synthetic HTF).

    Under pure null E[g]≈0 for both roles; FILT has lower cadence. Plant injects +edge on
    FILT exits in stage-1 only (deplant applied by caller for bite).
    """
    rng = np.random.default_rng(seed)
    n_cand = n_candidates
    n_filt = max(int(np.ceil(0.25 * n_cand)), 1)
    n_base = max(int(np.ceil(0.25 * n_cand)), 1)
    n_rest = n_cand - n_filt - n_base
    # remainder random mix
    n_filt += int(rng.integers(0, n_rest + 1)) if n_rest > 0 else 0
    n_base = n_cand - n_filt

    default_h = HOLD_DEFAULT_H[cadence.name]
    cost_base = bybit_cost_bps_for_hold("SYNTH", hold_hours=default_h)

    # BASE: unfiltered path / high-cadence null
    if cadence.kind == "high":
        base_spec = HighCadenceNullSpec(
            n_candidates=n_base,
            n_bars=cadence.n_bars,
            target_legs_per_candidate=min(cadence.n_trades, cadence.n_bars // 8),
            hold_bars=cadence.hold_bars,
            cost_bps=cost_base,
            edge_bps=0.0,
            seed=seed,
            noise_bps=8.0,
        )
        bases = build_high_cadence_null(base_spec)
        # rename ids to base*
        bases = [
            CandidateStream(f"base{i}", s.symbol, s.trades, s.marks, s.cost_bps, s.money_per_unit)
            for i, s in enumerate(bases)
        ]
    else:
        bases = path_universe(
            n_planted=0, n_null=n_base, edge_bps=0.0, seed=seed,
            n_trades=cadence.n_trades, n_bars=cadence.n_bars, cost_bps=cost_base,
        )
        bases = [
            CandidateStream(f"base{i}", s.symbol, s.trades, s.marks, s.cost_bps, s.money_per_unit)
            for i, s in enumerate(bases)
        ]

    # FILT: shared path, thinned entries (τ), optional plant edge
    opens, hv = regime_gbm_path(n_bars=cadence.n_bars, seed=seed * 7_919 + 3)
    t = np.arange(cadence.n_bars, dtype=np.int64) * 60 * NS
    marks = pl.DataFrame({"CloseTime": t, "Open": opens})
    filts: list[CandidateStream] = []
    for i in range(n_filt):
        tau = float(rng.choice([0.3, 0.5, 0.7]))
        n_trades = max(4, int(cadence.n_trades * tau))
        cid = f"filtplant{i}" if (plant and edge_bps > 0) else f"filt{i}"
        edge = float(edge_bps) if plant else 0.0
        # thin from a dense entry pool
        eligible = np.arange(10, cadence.n_bars - cadence.hold_bars - 2)
        # synthetic HTF gate independent of future PnL: keep every k-th after RNG mask
        keep = rng.random(len(eligible)) < tau
        pool = eligible[keep]
        if len(pool) < n_trades:
            pool = eligible
        entries = np.sort(rng.choice(pool, size=min(n_trades, len(pool)), replace=False))
        rows = []
        for ei in entries:
            d = 1.0 if rng.random() < 0.5 else -1.0
            ep = float(opens[int(ei)])
            raw_exit = float(opens[int(ei) + cadence.hold_bars])
            exit_px = raw_exit * (1.0 + d * edge / 1e4)
            stop = ep * (8.0 / 1e4) * (3.0 if hv[int(ei)] else 1.0) * 5.0
            rows.append({
                "EntryTime": int(t[int(ei)]),
                "ExitTime": int(t[int(ei) + cadence.hold_bars]),
                "Direction": d,
                "EntryPrice": ep,
                "ExitPrice": exit_px,
                "StopDistance": stop,
                "Censored": False,
            })
        trades = pl.DataFrame(rows, schema={
            "EntryTime": pl.Int64, "ExitTime": pl.Int64, "Direction": pl.Float64,
            "EntryPrice": pl.Float64, "ExitPrice": pl.Float64,
            "StopDistance": pl.Float64, "Censored": pl.Boolean,
        })
        hold_h = _hold_hours_from_trades(trades, default_h)
        cost = bybit_cost_bps_for_hold("SYNTH", hold_hours=hold_h)
        filts.append(CandidateStream(cid, "SYNTH", trades, marks, cost, 1.0))

    # re-cost BASE with hold-derived costs
    out: list[CandidateStream] = []
    for s in bases:
        h = _hold_hours_from_trades(s.trades, default_h)
        out.append(_apply_stream_cost(s, bybit_cost_bps_for_hold(s.symbol, hold_hours=h)))
    out.extend(filts)
    # tag class
    for i, s in enumerate(out):
        # CandidateStream is frozen dataclass — class_id carried only in id prefix
        del i
    assert len(out) == n_cand
    return out


# --------------------------------------------------------------------------- #
# CLS-EPISODE null / plant factory
# --------------------------------------------------------------------------- #
def make_episode_null_universe(
    seed: int,
    cadence: CadenceSpec,
    *,
    n_candidates: int = 64,
    edge_bps: float = 0.0,
    plant: bool = False,
) -> list[CandidateStream]:
    """CLS-EPISODE: episode objects with duration ~ truncated lognormal (design §4.1)."""
    rng = np.random.default_rng(seed)
    opens, _hv = regime_gbm_path(n_bars=cadence.n_bars, seed=seed * 5_017)
    t = np.arange(cadence.n_bars, dtype=np.int64) * 60 * NS
    marks = pl.DataFrame({"CloseTime": t, "Open": opens})
    median_h = 4.0 if cadence.name == "low" else 1.0
    cap_h = 48.0
    streams: list[CandidateStream] = []
    n_trades = cadence.n_trades
    for i in range(n_candidates):
        cid = f"epplant{i}" if (plant and edge_bps > 0 and i < max(1, n_candidates // 4)) else f"ep{i}"
        edge = float(edge_bps) if cid.startswith("epplant") else 0.0
        # episode durations in hours → bars
        dur_h = np.clip(rng.lognormal(mean=np.log(median_h), sigma=0.6, size=n_trades), 1 / 60, cap_h)
        hold_bars = np.maximum(1, np.round(dur_h * 60).astype(int))  # 1m bars
        eligible_max = cadence.n_bars - int(hold_bars.max()) - 2
        if eligible_max <= 20:
            eligible_max = cadence.n_bars // 2
        entries = np.sort(rng.choice(np.arange(10, max(11, eligible_max)),
                                     size=min(n_trades, max(1, eligible_max - 10)),
                                     replace=False))
        rows = []
        for j, ei in enumerate(entries):
            hb = int(hold_bars[j % len(hold_bars)])
            xi = min(int(ei) + hb, cadence.n_bars - 1)
            d = 1.0 if rng.random() < 0.5 else -1.0
            ep = float(opens[int(ei)])
            raw_exit = float(opens[xi])
            exit_px = raw_exit * (1.0 + d * edge / 1e4)
            stop = ep * 0.01
            rows.append({
                "EntryTime": int(t[int(ei)]),
                "ExitTime": int(t[xi]),
                "Direction": d,
                "EntryPrice": ep,
                "ExitPrice": exit_px,
                "StopDistance": stop,
                "Censored": False,
            })
        trades = pl.DataFrame(rows, schema={
            "EntryTime": pl.Int64, "ExitTime": pl.Int64, "Direction": pl.Float64,
            "EntryPrice": pl.Float64, "ExitPrice": pl.Float64,
            "StopDistance": pl.Float64, "Censored": pl.Boolean,
        })
        hold_h = _hold_hours_from_trades(trades, HOLD_DEFAULT_H[cadence.name])
        cost = bybit_cost_bps_for_hold("SYNTH", hold_hours=hold_h)
        streams.append(CandidateStream(cid, "SYNTH", trades, marks, cost, 1.0))
    return streams


def factory_fingerprint(fn: Callable[..., Any]) -> str:
    """Stable fingerprint of factory source for CLS-FILTER ≠ CLS-EPISODE assert."""
    import inspect
    src = inspect.getsource(fn)
    return hashlib.sha256(src.encode("utf-8")).hexdigest()


# Factories must not be byte-identical (design §4.1)
assert factory_fingerprint(make_filter_null_universe) != factory_fingerprint(
    make_episode_null_universe
), "CLS-FILTER and CLS-EPISODE factories must differ"


def universe_factory(class_id: str) -> Callable[..., list[CandidateStream]]:
    if class_id == "CLS-FILTER":
        return make_filter_null_universe
    if class_id == "CLS-EPISODE":
        return make_episode_null_universe
    raise IntegrityError(f"unknown class_id {class_id!r}")


# --------------------------------------------------------------------------- #
# Two-stage pipeline (net stage-1; gross α̂ stage-2)
# --------------------------------------------------------------------------- #
def _search_params(cadence: CadenceSpec) -> SearchParams:
    return SearchParams(L=40, n_boot=80, block_bars=max(64, cadence.hold_bars), init_size=4)


def run_two_stage(
    streams: list[CandidateStream],
    cadence: CadenceSpec,
    layout: SegmentLayout,
    *,
    scale: ScaleSpec,
    seed: int,
    n_boot: int = N_BOOT,
    block_legs: int = BLOCK_LEGS,
) -> dict[str, Any]:
    """Stage-1 search→select(top-1) on g_gross; stage-2 leg-studentized LCB(g_gross).

    INFR-022: gross-only (zero-cost model) — the retired L-26 net-cost-binding stage-1
    and the stage-2 net (deployability) read are removed.
    """
    assert_stage1_zero_cost(charge_costs=False, score_kind="g_gross")
    config = OracleConfig(charge_costs=False)
    params = _search_params(cadence)
    finalists = [
        run_restart(
            streams, config, budget=scale.budget, restart_id=r + 1,
            params=params, segment=layout.search,
            skip_economics_precondition=True,
        )
        for r in range(scale.n_restarts)
    ]
    folds = contiguous_purged_folds(
        layout.ranking[0], layout.ranking[1], n_folds=3,
        purge_ns=max(cadence.hold_bars, 1) * 60 * NS,
    )
    pkg = certify_and_rank(
        finalists, streams, config, folds=folds, params=params,
        search_segment=layout.search, include_random_ref=False,
        include_fill_basis=False,
    )
    if not pkg["ranked"]:
        return {
            "empty": True, "gross_pass": False, "top": [],
            "g_search_hat": None,
        }
    top = pkg["ranked"][0].subset
    # stage-2: GROSS LCB only (the NET/deployability read is retired, INFR-022)
    lcb_g = eval_lcb_legs(
        top, streams, config, layout.gate, n_boot=n_boot, seed=seed,
        block_legs=block_legs,
    )
    top_ids = sorted(str(x) for x in top)
    return {
        "empty": False,
        "top": top_ids,
        "plant_in_top": any(t.startswith(_PLANT_PREFIXES) for t in top_ids),
        "gross_pass": bool(lcb_g.get("pass_positive")),
        "gross_lcb": lcb_g.get("lcb"),
        "gross_point": lcb_g.get("point"),
        "n_legs": lcb_g.get("n_legs"),
        "g_search_hat": pkg["ranked"][0].search_F_hat,
        "stage1_score_kind": "g_gross",
        "stage1_charge_costs": False,
        "cost_model": "NO_COST_CHARGED",
    }


# --------------------------------------------------------------------------- #
# Bite-check
# --------------------------------------------------------------------------- #
def bite_check(
    class_id: str,
    cadence: CadenceSpec,
    *,
    scale: ScaleSpec,
    embargo_frac: float = EMBARGO_FRAC,
    n: int = BITE_N,
) -> dict[str, Any]:
    """Stage-1-only plant must not survive stage-2; stage-1 must select plant ≥0.5."""
    fac = universe_factory(class_id)
    layout = c_layout(cadence.n_bars, cadence.hold_bars, embargo_frac=embargo_frac)
    stage2_start = layout.gate[0]
    base = BITE_SEEDS[cadence.name]
    survive = selected = 0
    rows = []
    for i in range(n):
        seed = base + i
        streams = fac(
            seed, cadence, n_candidates=scale.n_cand, edge_bps=BITE_EDGE_BPS, plant=True,
        )
        streams = deplant_stage2(
            streams, edge_bps=BITE_EDGE_BPS, stage2_start_ns=stage2_start,
        )
        # deplant only knows plant/HCPLANT prefixes — extend for filtplant/epplant
        streams = _deplant_class_plants(
            streams, edge_bps=BITE_EDGE_BPS, stage2_start_ns=stage2_start,
        )
        out = run_two_stage(streams, cadence, layout, scale=scale, seed=seed)
        selected += int(out.get("plant_in_top", False))
        survive += int(out.get("gross_pass", False))
        rows.append({
            "seed": seed, "plant_in_top": out.get("plant_in_top"),
            "stage2_pass": out.get("gross_pass"), "gross_lcb": out.get("gross_lcb"),
            "n_legs": out.get("n_legs"), "empty": out.get("empty"),
        })
    survival_rate = survive / max(n, 1)
    select_rate = selected / max(n, 1)
    select_ok = select_rate >= BITE_SELECT_MIN
    survival_ok = survival_rate <= BITE_SURVIVAL_MAX
    return {
        "class_id": class_id,
        "cadence": cadence.name,
        "n": n,
        "stage2_survival_rate": survival_rate,
        "stage1_select_rate": select_rate,
        "select_ok": bool(select_ok),
        "survival_ok": bool(survival_ok),
        "bite_ok": bool(select_ok and survival_ok),
        "thresholds": {
            "survival_max": BITE_SURVIVAL_MAX,
            "select_min": BITE_SELECT_MIN,
            "planted_edge_bps": BITE_EDGE_BPS,
        },
        "embargo_frac": embargo_frac,
        "stage2_start_ns": int(stage2_start),
        "rows": rows,
    }


def _deplant_class_plants(
    streams: list[CandidateStream],
    *,
    edge_bps: float,
    stage2_start_ns: int,
) -> list[CandidateStream]:
    """Deplant filtplant*/epplant* in stage-2 (same inverse as deplant_stage2)."""
    out: list[CandidateStream] = []
    for s in streams:
        if not s.candidate_id.startswith(("filtplant", "epplant")):
            out.append(s)
            continue
        tr = s.trades
        et = tr.get_column("EntryTime").to_numpy().astype(np.int64)
        d = tr.get_column("Direction").to_numpy().astype(float)
        xp = tr.get_column("ExitPrice").to_numpy().astype(float)
        in_s2 = et >= int(stage2_start_ns)
        raw = xp / (1.0 + d * edge_bps / 1e4)
        new_xp = np.where(in_s2, raw, xp)
        tr2 = tr.with_columns(pl.Series("ExitPrice", new_xp))
        out.append(CandidateStream(s.candidate_id, s.symbol, tr2, s.marks,
                                   s.cost_bps, s.money_per_unit))
    return out


# --------------------------------------------------------------------------- #
# Coverage + e2e α
# --------------------------------------------------------------------------- #
def no_search_coverage(
    class_id: str,
    cadence: CadenceSpec,
    *,
    scale: ScaleSpec,
    embargo_frac: float = EMBARGO_FRAC,
    n_universes: int,
    subset_size: int = 5,
    block_legs: int = BLOCK_LEGS,
    n_boot: int = N_BOOT,
    alpha: float = ALPHA,
) -> dict[str, Any]:
    """No-search LCB pass rate on stage-2. Gross-only (INFR-022)."""
    fac = universe_factory(class_id)
    config = OracleConfig(charge_costs=False)
    layout = c_layout(cadence.n_bars, cadence.hold_bars, embargo_frac=embargo_frac)
    hits = 0
    rows = []
    # bank_seeds reads p3b.SEED_BASE_LOW/HIGH set by caller — do not override here
    seed_base_low = int(p3b.SEED_BASE_LOW)
    seed_base_high = int(p3b.SEED_BASE_HIGH)
    for seed, cspec in bank_seeds(cadence, n_universes):
        streams = fac(seed, cspec, n_candidates=scale.n_cand, edge_bps=0.0, plant=False)
        rng = np.random.default_rng(seed + 91)
        ids = [s.candidate_id for s in streams]
        k = min(subset_size, len(ids))
        pick = frozenset(str(x) for x in rng.choice(ids, size=k, replace=False))
        lcb = eval_lcb_legs(
            pick, streams, config, layout.gate, n_boot=n_boot, seed=seed,
            block_legs=block_legs,
        )
        pos = bool(lcb.get("pass_positive"))
        hits += int(pos)
        rows.append({"seed": seed, "pass": pos, "lcb": lcb.get("lcb"),
                     "n_legs": lcb.get("n_legs")})
    n = len(rows)
    rate = hits / max(n, 1)
    return {
        "class_id": class_id, "cadence": cadence.name, "n": n,
        "n_lcb_positive": hits, "rate": rate,
        "coverage_ok": bool(n > 0 and rate <= float(alpha)), "rows": rows,
        "seed_bases": {"low": seed_base_low, "high": seed_base_high},
        "alpha_target": float(alpha),
    }


def e2e_alpha(
    class_id: str,
    cadence: CadenceSpec,
    *,
    scale: ScaleSpec,
    embargo_frac: float = EMBARGO_FRAC,
    n_boot: int = N_BOOT,
    block_legs: int = BLOCK_LEGS,
    alpha: float = ALPHA,
) -> dict[str, Any]:
    """Full two-stage over null bank; α̂ = frac stage-2 LCB(g_gross)>0 on top-1.

    Uses current ``p3b.SEED_BASE_*`` (caller sets design or confirm). Gate compares
    point α̂ to ``alpha`` (frozen procedure value), not a free global.
    """
    fac = universe_factory(class_id)
    layout_by: dict = {}
    rows = []
    seed_base_low = int(p3b.SEED_BASE_LOW)
    seed_base_high = int(p3b.SEED_BASE_HIGH)
    for seed, cspec in bank_seeds(cadence, scale.n_null):
        key = (cspec.n_bars, cspec.hold_bars)
        layout = layout_by.get(key) or c_layout(
            cspec.n_bars, cspec.hold_bars, embargo_frac=embargo_frac,
        )
        layout_by[key] = layout
        streams = fac(seed, cspec, n_candidates=scale.n_cand, edge_bps=0.0, plant=False)
        out = run_two_stage(
            streams, cspec, layout, scale=scale, seed=seed,
            n_boot=n_boot, block_legs=block_legs,
        )
        rows.append({
            "seed": seed, "symbol": cspec.symbol,
            "gross_pass": bool(out.get("gross_pass")),
            "gross_lcb": out.get("gross_lcb"), "gross_point": out.get("gross_point"),
            "g_search_hat": out.get("g_search_hat"), "n_legs": out.get("n_legs"),
            "empty": out.get("empty", False),
        })
    n = len(rows)
    k = sum(1 for r in rows if r["gross_pass"])
    ph = k / max(n, 1)
    lo, hi = wilson(k, n)
    return {
        "class_id": class_id, "cadence": cadence.name, "n": n,
        "n_gross_lcb_positive": k, "alpha_hat": ph,
        "alpha_se": binomial_se(ph, n),
        "alpha_wilson_95": {"low": lo, "high": hi},
        "pass_stop": bool(ph <= float(alpha)),
        "seed_bases": {"low": seed_base_low, "high": seed_base_high},
        "alpha_target": float(alpha),
        "rows": rows,
    }


def _failure_label(no_search_cov: float, e2e: float) -> str:
    inflation = e2e - no_search_cov
    if inflation <= _SELECTION_INFLATION_MAX:
        return "coverage_limited"
    return "selection_unsafe"


def _outcome(low_cert: bool, high_cert: bool) -> dict[str, Any]:
    if low_cert and high_cert:
        return {
            "verdict": "DUAL_CERTIFY", "certified_cadences": ["low", "high"],
            "recommend": "route_both", "terminal": False,
        }
    if high_cert:
        return {
            "verdict": "HIGH_ONLY_CERTIFY", "certified_cadences": ["high"],
            "recommend": "route_high_only", "terminal": False,
        }
    if low_cert:
        return {
            "verdict": "LOW_ONLY_CERTIFY", "certified_cadences": ["low"],
            "recommend": "route_low_only", "terminal": False,
        }
    return {
        "verdict": "TERMINAL", "certified_cadences": [], "terminal": True,
        "recommend": "TERMINAL_cannot_certify",
    }


def assert_seed_disjoint() -> None:
    """Design vs confirm vs bite + archive banks must not collide (G2)."""
    design = set(range(DESIGN_SEEDS["low"], DESIGN_SEEDS["low"] + 500)) | set(
        range(DESIGN_SEEDS["high"], DESIGN_SEEDS["high"] + 500)
    )
    confirm = set(range(CONFIRM_SEEDS["low"], CONFIRM_SEEDS["low"] + 500)) | set(
        range(CONFIRM_SEEDS["high"], CONFIRM_SEEDS["high"] + 500)
    )
    bite = set(range(BITE_SEEDS["low"], BITE_SEEDS["low"] + 50)) | set(
        range(BITE_SEEDS["high"], BITE_SEEDS["high"] + 50)
    )
    # chapter-03 known bases
    archive = set(range(71_000, 71_500)) | set(range(72_000, 72_500)) | set(
        range(81_000, 81_500)
    ) | set(range(82_000, 82_500)) | set(range(791_000, 791_050)) | set(
        range(792_000, 792_050)
    )
    if design & confirm:
        raise IntegrityError("design/confirm seed collision")
    if design & bite or confirm & bite:
        raise IntegrityError("bite seed collision with design/confirm")
    if design & archive or confirm & archive or bite & archive:
        raise IntegrityError("Bybit bank collides with chapter-03 archive seeds")


# --------------------------------------------------------------------------- #
# DESIGN bank
# --------------------------------------------------------------------------- #
def run_design(
    class_id: str,
    *,
    scale: ScaleSpec = DESIGN_SCALE,
) -> dict[str, Any]:
    """Bite + no-search coverage disclosure; freeze procedure constants only if bite OK."""
    if class_id not in CLASS_IDS:
        raise IntegrityError(f"unknown class_id {class_id!r}")
    assert_seed_disjoint()
    _set_seeds(DESIGN_SEEDS["low"], DESIGN_SEEDS["high"])
    print(f"[INFR-014] DESIGN {class_id}: bite-check...", flush=True)
    bite: dict[str, Any] = {}
    for c in (LOW, HIGH):
        b = bite_check(class_id, c, scale=scale, embargo_frac=EMBARGO_FRAC)
        bite[c.name] = b
        print(
            f"  bite {c.name}: survival={b['stage2_survival_rate']:.3f} "
            f"(≤{BITE_SURVIVAL_MAX}) select={b['stage1_select_rate']:.3f} "
            f"ok={b['bite_ok']}",
            flush=True,
        )
    bite_ok = all(bite[c]["bite_ok"] for c in ("low", "high"))
    if not bite_ok:
        return {
            "bank": "design",
            "class_id": class_id,
            "seeds": dict(DESIGN_SEEDS),
            "bite": {
                k: {kk: vv for kk, vv in v.items() if kk != "rows"}
                for k, v in bite.items()
            },
            "frozen_procedure": None,
            "design_ok": False,
            "stop_reason": "bite_failed",
            "terminal": True,
            "recommend": "TERMINAL_temporal_independence_failed",
            "note": "bite FAIL = TERMINAL, no confirm (Fork B / design §5.3)",
        }

    print(f"[INFR-014] DESIGN {class_id}: no-search coverage...", flush=True)
    cov: dict[str, Any] = {}
    _set_seeds(DESIGN_SEEDS["low"], DESIGN_SEEDS["high"])
    for c in (LOW, HIGH):
        cv = no_search_coverage(
            class_id, c, scale=scale, embargo_frac=EMBARGO_FRAC,
            n_universes=scale.n_coverage, alpha=ALPHA,
        )
        cov[c.name] = cv
        print(
            f"  cov {c.name}: rate={cv['rate']:.4f} ok={cv['coverage_ok']} (n={cv['n']}) "
            f"bases={cv.get('seed_bases')}",
            flush=True,
        )

    frozen = {
        "binder": "two_stage_sample_split",
        "stage1": "search+certify top-1 on stage-1 bands",
        "stage1_score_kind": "g_gross",
        "stage1_charge_costs": False,
        "stage2": "lcb_g_leg_studentized(g_gross) > 0 on distant embargoed band",
        "e2e_pass_event": "stage2_gross_lcb_positive",
        "deployability_binding": "RETIRED (INFR-022 zero-cost; historical: stage2_net_lcb_positive)",
        "functional": "g_gross_ratio",
        "estimator": "leg_studentized_bootstrap_t",
        "embargo_frac": EMBARGO_FRAC,
        "search_frac": STAGE_SEARCH_FRAC,
        "ranking_frac": STAGE_RANKING_FRAC,
        "n_boot": N_BOOT,
        "block_legs": BLOCK_LEGS,
        "confidence": 0.95,
        "alpha": ALPHA,
        "one_subset": True,
        "shortlist": False,
        "design_seeds": dict(DESIGN_SEEDS),
        "confirm_seeds": dict(CONFIRM_SEEDS),
        "design_bite_ok": True,
        "design_cov_low": cov["low"]["rate"],
        "design_cov_high": cov["high"]["rate"],
        "held_out_escalation": False,
        "gate_rule": "per_cadence point α̂≤5% AND no-search cov≤5% (Fork A)",
        "cost_stack": "bybit_round_trip_cost_bps_v2_no_spread",
        "spread_cost_status": "UNAVAILABLE_NOT_CHARGED",
        "cost_scope": "PARTIAL_FEES_FUNDING_ONLY",
        "class_id": class_id,
    }
    return {
        "bank": "design",
        "class_id": class_id,
        "seeds": dict(DESIGN_SEEDS),
        "bite": {
            k: {kk: vv for kk, vv in v.items() if kk != "rows"} for k, v in bite.items()
        },
        "bite_rows": {k: v["rows"] for k, v in bite.items()},
        "coverage": {
            k: {kk: vv for kk, vv in v.items() if kk != "rows"} for k, v in cov.items()
        },
        "frozen_procedure": frozen,
        "design_ok": True,
        "stop_reason": None,
    }


# --------------------------------------------------------------------------- #
# CONFIRM bank — no optional stopping, no peek-and-extend
# --------------------------------------------------------------------------- #
def confirm_gate(
    class_id: str,
    procedure: dict,
    *,
    scale: ScaleSpec = CONFIRM_SCALE,
) -> dict[str, Any]:
    """Binding e2e α̂ + coverage; gate on point α̂ ≤ 0.05 ∧ no_search_cov ≤ 0.05."""
    if not procedure or not procedure.get("design_bite_ok"):
        raise IntegrityError("confirm blocked unless design_ok procedure exists")
    # refuse free thresholds — only frozen procedure dict (G4)
    required = (
        "embargo_frac", "n_boot", "block_legs", "alpha", "stage1_score_kind",
        "stage1_charge_costs", "e2e_pass_event",
    )
    for k in required:
        if k not in procedure:
            raise IntegrityError(f"frozen procedure missing {k}")
    assert_stage1_net_binding(
        charge_costs=bool(procedure["stage1_charge_costs"]),
        score_kind=str(procedure["stage1_score_kind"]),
    )
    assert_seed_disjoint()
    embargo_frac = float(procedure["embargo_frac"])
    n_boot = int(procedure["n_boot"])
    block_legs = int(procedure["block_legs"])
    alpha = float(procedure["alpha"])  # frozen procedure only (QA Issue 13)
    # n_null fixed for binding runs — no optional stopping / peek-and-extend
    if scale.name == "confirm" and scale.n_null != CONFIRM_SCALE.n_null:
        raise IntegrityError(
            f"binding confirm n_null must be {CONFIRM_SCALE.n_null}, got {scale.n_null}"
        )

    per: dict[str, Any] = {}
    # pin confirm seed bases once; coverage + e2e both consume the same bases (Issue 9)
    _set_seeds(CONFIRM_SEEDS["low"], CONFIRM_SEEDS["high"])
    for c in (LOW, HIGH):
        print(f"[INFR-014] CONFIRM {class_id} {c.name}: no-search coverage...", flush=True)
        cov = no_search_coverage(
            class_id, c, scale=scale, embargo_frac=embargo_frac,
            n_universes=scale.n_coverage, block_legs=block_legs, n_boot=n_boot,
            alpha=alpha,
        )
        # integrity: coverage must not have drifted to design bases
        if cov.get("seed_bases") != dict(CONFIRM_SEEDS):
            raise IntegrityError(
                f"confirm coverage seed_bases {cov.get('seed_bases')} != CONFIRM_SEEDS "
                f"{CONFIRM_SEEDS} (QA Issue 9)"
            )
        print(
            f"  cov {c.name}: {cov['rate']:.4f} ok={cov['coverage_ok']} "
            f"bases={cov.get('seed_bases')}",
            flush=True,
        )
        print(f"[INFR-014] CONFIRM {class_id} {c.name}: e2e α...", flush=True)
        a = e2e_alpha(
            class_id, c, scale=scale, embargo_frac=embargo_frac,
            n_boot=n_boot, block_legs=block_legs, alpha=alpha,
        )
        if a.get("seed_bases") != dict(CONFIRM_SEEDS):
            raise IntegrityError(
                f"confirm e2e seed_bases {a.get('seed_bases')} != CONFIRM_SEEDS"
            )
        print(f"  α̂ {c.name}: {a['alpha_hat']:.4f} ok={a['pass_stop']}", flush=True)
        certified = bool(cov["coverage_ok"] and a["pass_stop"])
        band = "CERTIFIED" if certified else (
            "FAIL_ALPHA" if not a["pass_stop"] else "FAIL_COV"
        )
        per[c.name] = {
            "cadence": c.name,
            "band": band,
            "no_search_cov": cov["rate"],
            "e2e_alpha": a["alpha_hat"],
            "selection_inflation": a["alpha_hat"] - cov["rate"],
            "coverage_ok": cov["coverage_ok"],
            "alpha_ok": a["pass_stop"],
            "certified": certified,
            "alpha_se": a["alpha_se"],
            "alpha_wilson_95": a["alpha_wilson_95"],
            "n": a["n"],
            "n_gross_lcb_positive": a["n_gross_lcb_positive"],
            "seed_bases": a.get("seed_bases"),
            "alpha_target": alpha,
            "failure_label": (
                None if certified else _failure_label(cov["rate"], a["alpha_hat"])
            ),
            "coverage_rows": cov["rows"],
            "alpha_rows": a["rows"],
        }
    outcome = _outcome(per["low"]["certified"], per["high"]["certified"])
    return {
        "bank": "confirm",
        "class_id": class_id,
        "seeds": dict(CONFIRM_SEEDS),
        "procedure": procedure,
        "per_cadence": {
            k: {kk: vv for kk, vv in v.items() if kk not in ("coverage_rows", "alpha_rows")}
            for k, v in per.items()
        },
        "alpha_low_rows": per["low"]["alpha_rows"],
        "alpha_high_rows": per["high"]["alpha_rows"],
        "coverage_low_rows": per["low"]["coverage_rows"],
        "coverage_high_rows": per["high"]["coverage_rows"],
        "outcome": outcome,
        "stop_condition": {
            "alpha_target": alpha,
            "gate_rule": (
                f"point α̂≤{alpha} ∧ no_search_cov≤{alpha} "
                "(Wilson disclosure-only; alpha from frozen procedure)"
            ),
            "low_certified": per["low"]["certified"],
            "high_certified": per["high"]["certified"],
            "verdict": outcome["verdict"],
            "recommend": outcome["recommend"],
            "terminal": outcome["terminal"],
            "forbidden": [
                "no optional stopping",
                "no peek-and-extend",
                "no UCB gate",
                "no chapter-03 pin",
                "no costless stage-1",
                "confirm coverage must use confirm seeds (not design)",
            ],
        },
    }


def run_class_pipeline(
    class_id: str,
    *,
    scale_design: ScaleSpec = DESIGN_SCALE,
    scale_confirm: ScaleSpec = CONFIRM_SCALE,
) -> tuple[dict, dict | None]:
    design = run_design(class_id, scale=scale_design)
    if not design.get("design_ok"):
        return design, None
    confirm = confirm_gate(class_id, design["frozen_procedure"], scale=scale_confirm)
    return design, confirm


# --------------------------------------------------------------------------- #
# Registry write + verify (schema v1)
# --------------------------------------------------------------------------- #
def write_bybit_registry(
    class_results: dict[str, dict],
    *,
    out_path: str | Path,
    selection_rule_default_hash: str = "",
    next_open_artifact: dict | None = None,
) -> dict:
    """Write results/bybit_pc_frozen_registry.json per design §4.2.

    Partial-write: only if ≥1 class has verdict in
    {DUAL_CERTIFY, HIGH_ONLY_CERTIFY, LOW_ONLY_CERTIFY}.
    """
    certifiable = {
        "DUAL_CERTIFY", "HIGH_ONLY_CERTIFY", "LOW_ONLY_CERTIFY",
    }
    class_configs = []
    any_cert = False
    for cid in CLASS_IDS:
        cr = class_results.get(cid) or {}
        confirm = cr.get("confirm") or {}
        design = cr.get("design") or {}
        outcome = (confirm.get("outcome") or {})
        verdict = outcome.get("verdict", "TERMINAL")
        if verdict in certifiable:
            any_cert = True
        procedure = design.get("frozen_procedure") or confirm.get("procedure") or {}
        certified = verdict in certifiable
        class_configs.append({
            "class_id": cid,
            "family_prior": (
                "CF-HTFCAP-001" if cid == "CLS-FILTER" else "CF-EPSOSC-001"
            ),
            "procedure": procedure,
            "design_seeds": dict(DESIGN_SEEDS),
            "confirm_seeds": dict(CONFIRM_SEEDS),
            "cost_stack": "bybit_round_trip_cost_bps_v1",
            "stage1_score_kind": "g_net",
            "stage1_charge_costs": True,
            "e2e_pass_event": "stage2_gross_lcb_positive",
            "deployability_binding": "stage2_net_lcb_positive",
            "confirm_summary": {
                "verdict": verdict,
                "certified": certified,
                "per_cadence": confirm.get("per_cadence") or {},
                "recommend": outcome.get("recommend"),
                "terminal": bool(outcome.get("terminal", True)),
            },
            "limit_entry_cells": False,
            "design_ok": bool(design.get("design_ok")),
        })

    if not any_cert:
        raise IntegrityError(
            "partial-write policy: refuse registry when zero classes certifiable "
            f"(verdicts={[c['confirm_summary']['verdict'] for c in class_configs]})"
        )

    registry = {
        "schema": SCHEMA_ID,
        "substrate": "bybit_nautilus",
        "void_priors": list(VOID_PRIORS),
        "limit_entry_cells": False,
        "l27_next_open_tool": "xen.xena.fill_basis.next_open_discriminating_control",
        "next_open_sanity": next_open_artifact or {},
        "pin_usage": {
            "forbid_chapter03_on_bybit": True,
            "limit_print_sole_certify_forbidden": True,
            "note_spdr005_2_3b": (
                "CF-EPSOSC must not be certified solely on limit-print passive edge"
            ),
        },
        "selection_rule_default_hash": selection_rule_default_hash,
        "class_configs": class_configs,
        "partial_writes": False,  # single file; classes carry certified:false when terminal
    }
    blob = json.dumps(registry, sort_keys=True).encode("utf-8")
    artifact = {
        "registry": registry,
        "sha256": hashlib.sha256(blob).hexdigest(),
    }
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    return artifact


def verify_bybit_registry(path: str | Path) -> dict:
    """Schema + re-hash verify for INFR-014 Bybit registry (extends hash pin)."""
    artifact = json.loads(Path(path).read_text(encoding="utf-8"))
    if "registry" not in artifact or "sha256" not in artifact:
        raise IntegrityError("artifact missing registry/sha256")
    reg = artifact["registry"]
    if reg.get("schema") != SCHEMA_ID:
        raise IntegrityError(f"unexpected schema {reg.get('schema')!r}")
    if reg.get("substrate") != "bybit_nautilus":
        raise IntegrityError("substrate must be bybit_nautilus")
    if reg.get("limit_entry_cells") is not False:
        raise IntegrityError("limit_entry_cells must be false")
    pin = reg.get("pin_usage") or {}
    if not pin.get("forbid_chapter03_on_bybit"):
        raise IntegrityError("pin_usage.forbid_chapter03_on_bybit required")
    if not pin.get("limit_print_sole_certify_forbidden"):
        raise IntegrityError("pin_usage.limit_print_sole_certify_forbidden required")
    cfgs = reg.get("class_configs")
    if not isinstance(cfgs, list) or len(cfgs) < 1:
        raise IntegrityError("class_configs[] required")
    for c in cfgs:
        if c.get("stage1_charge_costs") is not True or c.get("stage1_score_kind") != "g_net":
            raise IntegrityError(f"{c.get('class_id')}: stage-1 must be g_net + charge_costs")
    blob = json.dumps(reg, sort_keys=True).encode("utf-8")
    digest = hashlib.sha256(blob).hexdigest()
    if digest != artifact["sha256"]:
        raise IntegrityError(f"hash mismatch: {digest} != {artifact['sha256']}")
    # void_priors must list known VOID chapter pins (binding refuse contract)
    listed = " ".join(str(x) for x in (reg.get("void_priors") or []))
    for vp in VOID_PRIORS:
        if vp not in listed:
            raise IntegrityError(
                f"void_priors missing required prior prefix {vp!r} "
                f"(chapter-03 / superseded pins must be explicit VOID)"
            )
    if not pin.get("forbid_chapter03_on_bybit"):
        raise IntegrityError("pin_usage.forbid_chapter03_on_bybit must be true")
    return reg


def next_open_sanity_artifact(seed: int = 42) -> dict[str, Any]:
    """Market-only CAL sanity: next-open control on a small null (gap ≈ 0 expected)."""
    streams = make_filter_null_universe(seed, LOW, n_candidates=8, edge_bps=0.0)
    return next_open_discriminating_control(streams)


def cost_pins_payload() -> dict[str, Any]:
    """Disclosed cost defaults for synthetic CAL banks (spread never charged)."""
    return {
        "stack": "bybit_round_trip_cost_bps_v2_no_spread",
        "spread_rt_bps": None,
        "spread_cost_status": "UNAVAILABLE_NOT_CHARGED",
        "cost_scope": "PARTIAL_FEES_FUNDING_ONLY",
        "funding_bps_per_8h": FUNDING_BPS_PER_8H,
        "funding_coverage": "GAP",
        "liquidity": "taker",
        "hold_defaults_h": dict(HOLD_DEFAULT_H),
        "note": "synthetic null banks use GAP spread=5.0; live pilots pin per-symbol medians",
    }
