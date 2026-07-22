"""SPDR-009 signed-absorption screen (S9) — TRAIN-only, disposition-only.

Execution order is strict (design §9)::

  1. Frozen-input hash verify (INFR-017/018/020)
  2. Per-pair usable universe from coverage_report (option A 0.50 floor)
  3. Per-pair τ / P_WIDE cuts frozen on **counts only** → pool_cuts.json
  4. Cost floors + power_census; each pair's MDE curves before its first contrast
  5. DESIGN reads T1–T5 + controls **per pair** → tripwire → CONFIRM once
  6. layers + census → screen.md (operator disposition later)

Hard fences: DESIGN/CONFIRM only, COMPLETE-window, causal ≤ t−1, 1-minute
outcomes/profiles, no TEST, no local accounting, no auto-verdict.

Run (prep only — freezes cuts, does not read outcomes unless ``--execute``)::

    python/.venv/bin/python \\
      python/experiments/SPDR-009/screen_code/absorb_screen.py --prep

Full DESIGN execution requires explicit operator approval + ``--execute``::

    python/.venv/bin/python \\
      python/experiments/SPDR-009/screen_code/absorb_screen.py --execute
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import polars as pl
from tqdm.auto import tqdm

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from xen.estimand_validation import check_no_local_accounting  # noqa: E402
from xen.evaluation import spread_scale_route  # noqa: E402
from xen.sigbar import absorb  # noqa: E402
from xen.sigbar.fences import band_window, load_bars, repo_root  # noqa: E402
from xen.sigbar.sessions import anchor_table  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "results"

TAU_GRID = (0.05, 0.10, 0.15, 0.20, 0.25, 0.35, 0.50)
# P_WIDE must be a STRICTLY TIGHTER contact zone than P (design §3.2). The first
# run froze P at the grid floor 0.05, so the old P_WIDE grid could only match it
# and the "tighter τ" leg went unmet — the grid now extends below the P floor
# (count-only, no outcomes consulted; post-measurement AMENDMENT-26).
P_WIDE_TAU_GRID = (0.005, 0.01, 0.02, 0.03, 0.05, 0.10, 0.15, 0.20)
D1_IB_TAU = 0.25
MIN_POOL_EVENTS = 30
SMOKE_SYMBOLS = ("SOLUSDT", "ADAUSDT", "MATICUSDT", "LINKUSDT")
SMOKE_CF_SEEDS = 5
SMOKE_T2_SEEDS = 40
T2_PLANT_SEEDS = 200
SMOKE_T2_PLANT_SEEDS = 40


def _emit(path: Path, obj: object) -> None:
    # Created on write, never at import — an import-time mkdir resurrects a
    # hard-deleted results tree in any process that merely imports this runner
    # (project code standard: no import side effects; QA-13 LOW).
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=str) + "\n")
    print(f"wrote {path}", flush=True)


def step_frozen() -> absorb.Spdr009FrozenInputs:
    check_no_local_accounting(str(Path(__file__).resolve().parent))
    fi = absorb.assert_spdr009_frozen_inputs()
    print(
        f"frozen ok: baselines={fi.baselines_1m_sha256[:8]}… "
        f"registry={fi.registry_pin_sha256[:8]}… "
        f"infr020_pins={fi.infr020_pins_sha256[:8]}…",
        flush=True,
    )
    return fi


def step_universe() -> dict:
    out = {}
    for pair_id in absorb.PAIR_SPECS:
        u = absorb.usable_universe(pair_id)
        out[pair_id] = u
        print(
            f"  {pair_id}: usable={u['n_usable']} "
            f"liquidity_limited={u['n_liquidity_limited']}",
            flush=True,
        )
    _emit(OUT / "universe_membership.json", out)
    return out


def _count_pool(
    symbol: str,
    pair_id: str,
    tau: float,
    zone_mode: str,
    pool_mode: str = "P",
) -> int:
    try:
        ev = absorb.build_contact_events(
            symbol,
            "DESIGN",
            pair_id,
            tau=tau,
            zone_mode=zone_mode,  # type: ignore[arg-type]
            pool_mode=pool_mode,  # type: ignore[arg-type]
            nearest_only=True,
        )
    except Exception:
        return 0
    if ev.height == 0:
        return 0
    return int(absorb.apply_refractory(ev).height)


def step_pool_cuts(universe: dict, *, sample_symbols: list[str] | None = None) -> dict:
    """Freeze per-pair τ for P and P_WIDE on EVENT COUNTS ONLY (design §3.2)."""
    cuts: dict = {
        "band": "DESIGN",
        "zone_primary": "prior_session_range",
        "tau_grid": list(TAU_GRID),
        "p_wide_tau_grid": list(P_WIDE_TAU_GRID),
        "min_pool_events": MIN_POOL_EVENTS,
        "tau_by_pair": {},
        "p_wide_by_pair": {},
        "count_grid": {},
        "d1_ib_width_sensitivity_tau": D1_IB_TAU,
        "note": "count-only freeze — no forward returns consulted",
    }
    for pair_id, u in universe.items():
        symbols = sample_symbols or u["usable"][:20]
        if pair_id == "D1" and sample_symbols is None:
            prefer = [
                "SOLUSDT", "ADAUSDT", "MATICUSDT", "LINKUSDT", "DOGEUSDT",
                "XRPUSDT", "AVAXUSDT", "LTCUSDT", "BTCUSDT", "ETHUSDT",
            ]
            symbols = [s for s in prefer if s in set(u["usable"])] or symbols

        # Primary pool P
        grid_counts: dict[str, int] = {}
        chosen = TAU_GRID[-1]
        for tau in TAU_GRID:
            n = sum(
                _count_pool(sym, pair_id, tau, "prior_session_range", "P")
                for sym in symbols
            )
            grid_counts[str(tau)] = n
            if n >= MIN_POOL_EVENTS:
                chosen = tau
                break
        cuts["tau_by_pair"][pair_id] = {
            "tau": chosen,
            "zone_mode": "prior_session_range",
            "pool": "P",
            "n_sample_symbols": len(symbols),
            "sample_symbols": symbols,
            "n_pool_at_tau": grid_counts[str(chosen)],
        }
        cuts["count_grid"][pair_id] = {"P": grid_counts}

        # P_WIDE: STRICTLY TIGHTER τ than P on the same scale (count-only) plus
        # the p25 no-result leg. Candidates are restricted to τ < τ_P up front,
        # so the two pools can never coincide (design §3.2).
        tighter = [t for t in P_WIDE_TAU_GRID if t < chosen]
        if not tighter:
            raise RuntimeError(
                f"P_WIDE requires a τ strictly tighter than P's {chosen} for "
                f"{pair_id}; extend P_WIDE_TAU_GRID (design §3.2)"
            )
        wide_counts: dict[str, int] = {}
        wide_chosen = tighter[-1]  # loosest of the strictly-tighter set
        for tau in tighter:
            n = sum(
                _count_pool(sym, pair_id, tau, "prior_session_range", "P_WIDE")
                for sym in symbols
            )
            wide_counts[str(tau)] = n
            if n >= MIN_POOL_EVENTS:
                wide_chosen = tau
                break
        assert wide_chosen < chosen, "P_WIDE τ must be strictly tighter than P τ"
        cuts["p_wide_by_pair"][pair_id] = {
            "tau": wide_chosen,
            "tau_primary": chosen,
            "strictly_tighter_than_P": True,
            "zone_mode": "prior_session_range",
            "pool": "P_WIDE",
            "no_result_leg": "p25_range_resid",
            "n_pool_at_tau": wide_counts.get(str(wide_chosen), 0),
            "count_grid": wide_counts,
        }
        cuts["count_grid"][pair_id]["P_WIDE"] = wide_counts
        print(
            f"  {pair_id}: P tau={chosen} n≈{grid_counts[str(chosen)]}; "
            f"P_WIDE tau={wide_chosen} n≈{wide_counts.get(str(wide_chosen), 0)}",
            flush=True,
        )
    _emit(OUT / "pool_cuts.json", cuts)
    return cuts


def step_floors(universe: dict) -> dict:
    table: dict = {"pairs": {}}
    for pair_id in universe:
        h10 = absorb.hold_hours_for_pair(pair_id, 10)
        h5 = absorb.hold_hours_for_pair(pair_id, 5)
        rows = []
        for sym in sorted(
            set(universe[pair_id]["usable"])
            | {"BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT"}
        ):
            if sym not in universe[pair_id]["usable"] and pair_id != "D1":
                continue
            try:
                rows.append(
                    {
                        "symbol": sym,
                        "H5": absorb.cost_floor_bps(sym, hold_hours=h5),
                        "H10": absorb.cost_floor_bps(sym, hold_hours=h10),
                    }
                )
            except Exception as exc:
                rows.append({"symbol": sym, "error": str(exc)})
        table["pairs"][pair_id] = {
            "hold_hours_H5": h5,
            "hold_hours_H10": h10,
            "floors": rows,
        }
    _emit(OUT / "floor_table.json", table)
    return table


def _build_scored(
    symbol: str,
    band: str,
    pair_id: str,
    tau: float,
    zone_mode: str,
    pool_mode: str,
    *,
    bars_1m: pl.DataFrame | None = None,
) -> tuple[pl.DataFrame, int]:
    """Return (events with outcomes, n_located_after_refractory).

    The second value is what the census counts; events without a contiguous
    1-minute outcome path are dropped here and design §3.4 requires the drop to
    be COUNTED — the per-batch column cannot be aggregated, so the caller
    accumulates these instead (post-measurement AMENDMENT-28).
    """
    bars = bars_1m if bars_1m is not None else load_bars(symbol, band)
    ev = absorb.build_contact_events(
        symbol,
        band,
        pair_id,
        tau=tau,
        zone_mode=zone_mode,  # type: ignore[arg-type]
        pool_mode=pool_mode,  # type: ignore[arg-type]
        bars_1m=bars,
        nearest_only=True,
    )
    if ev.height == 0:
        return ev, 0
    ev = absorb.apply_refractory(ev)
    n_located = int(ev.height)
    return absorb.evaluate_outcomes_1m(bars, ev), n_located


def step_power_census(universe: dict, cuts: dict) -> dict:
    census: dict = {"band": "DESIGN", "pairs": {}}
    for pair_id, u in universe.items():
        tau = float(cuts["tau_by_pair"][pair_id]["tau"])
        zone = cuts["tau_by_pair"][pair_id]["zone_mode"]
        per_sym = {}
        totals = {"P": 0, "S9": 0, "MIRROR": 0, "BASE": 0}
        for sym in tqdm(u["usable"], desc=f"power {pair_id}", leave=False):
            try:
                ev = absorb.build_contact_events(
                    sym, "DESIGN", pair_id, tau=tau,
                    zone_mode=zone, pool_mode="P", nearest_only=True,
                )
                ev = absorb.apply_refractory(ev)
            except Exception as exc:
                per_sym[sym] = {"error": str(exc)}
                continue
            arms = {
                a: int((ev["arm"] == a).sum()) if ev.height else 0
                for a in ("S9", "MIRROR", "BASE")
            }
            arms["P"] = int(ev.height)
            per_sym[sym] = arms
            for k in totals:
                totals[k] += arms.get(k, 0)
        census["pairs"][pair_id] = {
            "tau": tau,
            "zone_mode": zone,
            "totals": totals,
            "per_symbol": per_sym,
            "n_usable": u["n_usable"],
        }
        print(f"  {pair_id} totals {totals}", flush=True)
    _emit(OUT / "power_census.json", census)
    return census


def mde_for_arm(
    ev: pl.DataFrame,
    *,
    t2_plant_seeds: int = T2_PLANT_SEEDS,
) -> dict:
    """Plant MDE curves on the arm the contrast will actually use.

    Design §4.2 requires the MDE at the REALISED n of the stratum. The first run
    computed it on a 30-symbol subsample while the read used the full universe,
    so a 1× plant was not material on the real arm and CF* calibration discarded
    every seed (post-measurement AMENDMENT-25).
    """
    s9 = ev.filter(pl.col("arm") == "S9")
    base = ev.filter(pl.col("arm") == "BASE")
    mirror = ev.filter(pl.col("arm") == "MIRROR")
    pair_mde: dict = {
        "n_events": int(ev.height),
        "n_S9": int(s9.height),
        "n_BASE": int(base.height),
        "n_MIRROR": int(mirror.height),
        "n_symbols": int(ev["symbol"].n_unique()) if "symbol" in ev.columns else 0,
        "arm_note": "computed on the same pooled arm the contrasts use",
    }
    for h in absorb.HOLDS_LTF:
        col = f"ret_bps_H{h}"
        pair_mde[f"T1_H{h}"] = absorb.plant_mde_curve(s9, base, ret_col=col)
        pair_mde[f"T1_mirror_H{h}"] = absorb.plant_mde_curve(s9, mirror, ret_col=col)
        pair_mde[f"T2_H{h}"] = absorb.signed_score_plant_mde_curve(
            ev,
            ret_col=col,
            n_seeds=t2_plant_seeds,
        )
    return pair_mde


def mde_for_contrast(
    treat: pl.DataFrame,
    control: pl.DataFrame,
    *,
    prefix: str,
) -> dict:
    """MDE curves for a prebuilt control contrast in its own bps units."""
    out: dict = {
        "n_treat": int(treat.height),
        "n_control": int(control.height),
    }
    for h in absorb.HOLDS_LTF:
        col = f"ret_bps_H{h}"
        out[f"{prefix}_H{h}"] = absorb.plant_mde_curve(
            treat, control, ret_col=col
        )
    return out


def _constant_control_on_treat_days(
    treat: pl.DataFrame,
    control: pl.DataFrame,
    ret_col: str,
) -> pl.DataFrame:
    """Represent T4's global control mean on every treated calendar day.

    T4's registered statistic is the day-clustered S9 mean minus the global
    matched-random mean. This frame lets the canonical contrast/MDE helpers
    evaluate exactly that statistic without changing donor weighting.
    """
    if (
        treat.height == 0
        or control.height == 0
        or "day" not in treat.columns
        or ret_col not in control.columns
    ):
        return pl.DataFrame()
    mean = control[ret_col].drop_nulls().mean()
    if mean is None:
        return pl.DataFrame()
    return treat.select("day").drop_nulls().unique().with_columns(
        pl.lit(float(mean)).alias(ret_col)
    )


def _build_t4_control(
    pair_id: str,
    ev: pl.DataFrame,
    bars_by: dict[str, pl.DataFrame],
) -> tuple[pl.DataFrame, list[dict]]:
    """Build matched-random donors once, before T4 MDE or the real read."""
    s9 = ev.filter(pl.col("arm") == "S9")
    parts: list[pl.DataFrame] = []
    failed: list[dict] = []
    if s9.height == 0:
        return ev.head(0), failed
    for sym in s9["symbol"].unique().to_list():
        bars = bars_by.get(sym)
        if bars is None or bars.height == 0:
            continue
        se = s9.filter(pl.col("symbol") == sym)
        a_spec = absorb._anchor_spec(absorb.PAIR_SPECS[pair_id]["anchor"])
        anchors = anchor_table(
            a_spec, bars["OpenTime"].min(), bars["OpenTime"].max()
        )
        if "session_end" not in se.columns or se["session_end"].null_count() == se.height:
            se = se.join(
                anchors.select("anchor_ts", "session_end"),
                on="anchor_ts",
                how="left",
            )
        try:
            ctrl = absorb.matched_random_timing(bars, se, anchors)
        except Exception as exc:
            failed.append({"symbol": sym, "error": str(exc)})
            continue
        if ctrl.height:
            parts.append(ctrl)
    return (
        pl.concat(parts, how="diagonal_relaxed") if parts else ev.head(0),
        failed,
    )


def _build_t5_control(
    pair_id: str,
    ev: pl.DataFrame,
    bars_by: dict[str, pl.DataFrame],
    *,
    band: str,
    tau: float,
    zone: str,
) -> tuple[pl.DataFrame, list[dict]]:
    """Build bare-level donors once, before T5 MDE or the real read."""
    base = ev.filter(pl.col("arm") == "BASE")
    parts: list[pl.DataFrame] = []
    failed: list[dict] = []
    for sym in list(bars_by)[:30]:
        se = base.filter(pl.col("symbol") == sym) if base.height else base.head(0)
        if se.height == 0:
            # Preserve the approved matching-density fallback; the artifact
            # discloses this residual and QA can trace its contribution.
            se = ev.filter(pl.col("symbol") == sym)
        if se.height == 0:
            continue
        try:
            bare = absorb.bare_level_touch_events(
                sym,
                band,
                pair_id,
                events=se,
                tau=tau,
                zone_mode=zone,  # type: ignore[arg-type]
                n_per_event=30,
                bars_1m=bars_by[sym],
            )
        except Exception as exc:
            failed.append({"symbol": sym, "error": str(exc)})
            continue
        if bare.height:
            parts.append(bare)
    return (
        pl.concat(parts, how="diagonal_relaxed") if parts else ev.head(0),
        failed,
    )


def _t4_mde(s9: pl.DataFrame, control: pl.DataFrame) -> dict:
    """T4 MDE using the same global-control/day-clustered statistic as the read."""
    out: dict = {"n_treat": int(s9.height), "n_control": int(control.height)}
    for h in absorb.HOLDS_LTF:
        col = f"ret_bps_H{h}"
        ref = _constant_control_on_treat_days(s9, control, col)
        out[f"T4_H{h}"] = absorb.plant_mde_curve(s9, ref, ret_col=col)
    return out


def _t4_read(
    s9: pl.DataFrame,
    control: pl.DataFrame,
    *,
    mde_info: dict,
) -> dict:
    """T4 H5/H10 reads against the prebuilt matched-random donor arm."""
    out: dict = {}
    for h in absorb.HOLDS_LTF:
        col = f"ret_bps_H{h}"
        ref = _constant_control_on_treat_days(s9, control, col)
        stat = absorb.contrast_day_clustered(s9, ref, ret_col=col)
        stat["n_control"] = int(control.height)
        stat["control_mean"] = (
            float(control[col].mean()) if control.height and col in control.columns else None
        )
        mde = (mde_info.get(f"T4_H{h}") or {}).get("mde_bps")
        stat["label"] = absorb.label_band(
            stat.get("contrast"), stat.get("ci"), mde
        )
        out[f"H{h}"] = stat
    return out


def _attach_t4_t5_reads(
    ev: pl.DataFrame,
    layers: dict,
    controls: dict,
    mde_info: dict,
) -> None:
    """Attach T4/T5 reads using the already-built, already-powered controls."""
    s9 = ev.filter(pl.col("arm") == "S9")
    t4_control = controls["T4"]
    layers["T4"] = _t4_read(s9, t4_control, mde_info=mde_info)
    layers["T4_control_coverage"] = {
        "n_control": int(t4_control.height),
        "failed": controls["T4_failed"],
    }

    base = ev.filter(pl.col("arm") == "BASE")
    bare = controls["T5"]
    t5_out: dict = {}
    if bare.height and base.height:
        for h in absorb.HOLDS_LTF:
            col = f"ret_bps_H{h}"
            t5 = absorb.contrast_day_clustered(base, bare, ret_col=col)
            mde = (mde_info.get(f"T5_H{h}") or {}).get("mde_bps")
            t5["label"] = absorb.label_band(
                t5.get("contrast"), t5.get("ci"), mde
            )
            t5["n_bare"] = int(bare.height)
            t5["match_rule"] = (
                "per-event: same level_kind × side × phase±30m; "
                "n_per_event=30; disjoint from climax-hold"
            )
            t5_out[f"H{h}"] = t5
    layers["T5"] = t5_out or {"UNPOWERED": True}
    layers["T5_control_coverage"] = {
        "n_control": int(bare.height),
        "failed": controls["T5_failed"],
    }


def _t2_dose(
    pool: pl.DataFrame,
    ret_col: str,
    *,
    n_seeds: int = absorb.N_DERANGE_SEEDS,
) -> dict:
    if pool.height < 8 or ret_col not in pool.columns:
        return {"UNPOWERED": True, "n": int(pool.height)}
    x = pool["signed_score"].to_numpy().astype(float)
    y = pool[ret_col].to_numpy().astype(float)
    rho, n_kept = absorb.spearman_finite(x, y)
    null = []
    for seed in range(n_seeds):
        d, _ = absorb.derange_scores_global(pool, seed=seed)
        if d.height == 0:
            continue
        r, _ = absorb.spearman_finite(
            d["signed_score"].to_numpy().astype(float), y
        )
        if np.isfinite(r):
            null.append(r)
    # within-symbol second null (mitigation disclosure)
    null_ws = []
    for seed in range(min(200, n_seeds)):
        d, _ = absorb.derange_scores_within_symbol(pool, seed=seed)
        if d.height == 0:
            continue
        r, _ = absorb.spearman_finite(
            d["signed_score"].to_numpy().astype(float),
            d[ret_col].to_numpy().astype(float) if ret_col in d.columns else y[: d.height],
        )
        if np.isfinite(r):
            null_ws.append(r)
    null_a = np.array(null)
    usable = bool(null_a.size and np.isfinite(rho))
    # Both tails: the right tail carries SUPPORTED, the left tail carries
    # CONTRADICTED (design §5 — anti-monotone ρ is evidence against, and a
    # result in its own right). A right-tailed p can never flag it (QA-9 I-2).
    p_one = float((null_a >= rho).mean()) if usable else None
    p_one_neg = float((null_a <= rho).mean()) if usable else None
    return {
        "rho": rho,
        "n": n_kept,
        "n_seeds": int(null_a.size),
        "derangement_null_mean": float(null_a.mean()) if null_a.size else None,
        "one_sided_p": p_one,
        "one_sided_p_neg": p_one_neg,
        "derangement_rho_p95": float(np.quantile(null_a, 0.95)) if null_a.size else None,
        "derangement_rho_p05": float(np.quantile(null_a, 0.05)) if null_a.size else None,
        "derangement_ci": (
            [float(np.quantile(null_a, 0.025)), float(np.quantile(null_a, 0.975))]
            if null_a.size
            else None
        ),
        "within_symbol_null_mean": float(np.mean(null_ws)) if null_ws else None,
        "within_symbol_n_seeds": len(null_ws),
    }


def _layers_for_events(
    pair_id: str,
    ev: pl.DataFrame,
    *,
    pool_name: str,
    mde_info: dict | None,
    floors: dict | None,
    t2_seeds: int = absorb.N_DERANGE_SEEDS,
) -> dict:
    if ev.height == 0:
        return {"n": 0, "pool": pool_name, "UNPOWERED": True}
    s9 = ev.filter(pl.col("arm") == "S9")
    base = ev.filter(pl.col("arm") == "BASE")
    mirror = ev.filter(pl.col("arm") == "MIRROR")
    out: dict = {
        "pool": pool_name,
        "n": int(ev.height),
        "n_S9": int(s9.height),
        "n_BASE": int(base.height),
        "n_MIRROR": int(mirror.height),
        "T1": {},
        "T1_mirror": {},
        "T2": {},
        "floor": {},
    }
    for h in absorb.HOLDS_LTF:
        col = f"ret_bps_H{h}"
        t1 = absorb.contrast_day_clustered(s9, base, ret_col=col)
        t1m = absorb.contrast_day_clustered(s9, mirror, ret_col=col)
        mde_h = None
        if mde_info:
            mde_h = (mde_info.get(f"T1_H{h}") or {}).get("mde_bps")
        t1["label"] = absorb.label_band(
            t1.get("contrast"), t1.get("ci"), mde_h
        )
        t1m["label"] = absorb.label_band(
            t1m.get("contrast"), t1m.get("ci"),
            (mde_info or {}).get(f"T1_mirror_H{h}", {}).get("mde_bps") if mde_info else None,
        )
        out["T1"][f"H{h}"] = t1
        out["T1_mirror"][f"H{h}"] = t1m
        t2 = _t2_dose(
            ev.filter(pl.col(col).is_not_null()), col, n_seeds=t2_seeds
        )
        t2_mde = ((mde_info or {}).get(f"T2_H{h}") or {})
        mde_rho = t2_mde.get("mde_rho")
        t2["mde_rho"] = mde_rho
        t2["mde_plant_bps_per_score_sd"] = t2_mde.get(
            "mde_plant_bps_per_score_sd"
        )
        if t2.get("rho") is not None and np.isfinite(float(t2["rho"])):
            supported = (
                t2.get("one_sided_p") is not None
                and t2["one_sided_p"] <= 0.05
                and mde_rho is not None
                and t2["rho"] >= mde_rho
            )
            contradicted = (
                t2.get("one_sided_p_neg") is not None
                and t2["one_sided_p_neg"] <= 0.05
            )
            suggestive = (
                t2.get("one_sided_p") is not None
                and t2["one_sided_p"] <= 0.05
                and not supported
            )
            if contradicted:
                t2["label"] = "CONTRADICTED"
            elif supported:
                t2["label"] = "SUPPORTED"
            elif suggestive:
                t2["label"] = "SUGGESTIVE"
            elif mde_rho is None:
                t2["label"] = "UNPOWERED"
            elif abs(float(t2["rho"])) < float(mde_rho):
                t2["label"] = "WASH"
            else:
                t2["label"] = "IMPRECISE"
        else:
            t2["label"] = "UNPOWERED"
        out["T2"][f"H{h}"] = t2
        if s9.height and col in s9.columns:
            med = float(s9[col].median())
            out["floor"][f"S9_median_H{h}"] = med
    if mde_info:
        out["mde"] = mde_info
    if floors:
        out["cost_floors_ref"] = "results/floor_table.json"
    # SPREAD-SCALE-ROUTING on T1 H10 — per audited symbol present in the arm, else tick floor
    t1 = out["T1"].get("H10") or {}
    if t1.get("contrast") is not None and s9.height and "symbol" in s9.columns:
        hold_h = absorb.hold_hours_for_pair(pair_id, 10)
        routes = {}
        for sym in s9["symbol"].unique().to_list()[:20]:
            try:
                fl = absorb.cost_floor_bps(sym, hold_hours=hold_h)
                routes[sym] = spread_scale_route(
                    float(t1["contrast"]), float(fl["spread_rt_bps"])
                )
                routes[sym]["spread_label"] = fl.get("spread_label")
            except Exception as exc:
                routes[sym] = {"error": str(exc)}
        out["spread_scale_route"] = routes
    # Session-remainder disclosure (secondary hold)
    if s9.height and "ret_bps_session" in s9.columns:
        ok = s9.filter(pl.col("session_remainder_ok") == True)  # noqa: E712
        base_ok = base.filter(pl.col("session_remainder_ok") == True) if "session_remainder_ok" in base.columns else base.head(0)  # noqa: E712
        if ok.height and base_ok.height:
            out["T1_session_remainder"] = absorb.contrast_day_clustered(
                ok, base_ok, ret_col="ret_bps_session"
            )
            out["T1_session_remainder"]["note"] = (
                "DISCLOSURE only — may overlap within session; no promote claim"
            )
        else:
            out["T1_session_remainder"] = {
                "n_S9_ok": int(ok.height) if ok.height else 0,
                "UNPOWERED": True,
                "note": "DISCLOSURE only",
            }
    return out


def _design_third_boundaries() -> list[tuple]:
    """Three immutable, disjoint time thirds of the frozen DESIGN band."""
    start, end = band_window("DESIGN")
    span = end - start
    cut1 = start + span / 3
    cut2 = start + 2 * span / 3
    return [(start, cut1), (cut1, cut2), (cut2, end)]


def _time_slices(events: pl.DataFrame, boundaries: list[tuple]) -> list[pl.DataFrame]:
    if events.height == 0 or "entry_ts" not in events.columns:
        return [events.head(0) for _ in boundaries]
    return [
        events.filter(
            (pl.col("entry_ts") >= start) & (pl.col("entry_ts") < end)
        ).sort("entry_ts")
        for start, end in boundaries
    ]


def _source_control_slice(control: pl.DataFrame, source: pl.DataFrame) -> pl.DataFrame:
    if control.height == 0 or source.height == 0:
        return control.head(0)
    if "src_event_ts" in control.columns and "event_ts" in source.columns:
        return control.filter(
            pl.col("src_event_ts").is_in(source["event_ts"].unique().to_list())
        )
    if "day" in control.columns and "day" in source.columns:
        return control.filter(pl.col("day").is_in(source["day"].unique().to_list()))
    return control.head(0)


def _signed_read(row: dict, effect_key: str = "contrast") -> dict:
    effect = row.get(effect_key)
    return {
        **row,
        "sign": (
            None
            if effect is None or not np.isfinite(float(effect))
            else int(np.sign(float(effect)))
        ),
    }


def _time_stability_thirds(
    ev_p: pl.DataFrame,
    ev_mid: pl.DataFrame | None,
    controls: dict,
    *,
    boundaries: list[tuple],
    t2_seeds: int,
) -> dict:
    """Repeat T1–T5 on three DESIGN thirds; report only, never gate."""
    if ev_p.height == 0:
        return {
            "n_total": 0,
            "thirds": [],
            "sign_consistency": {},
            "UNPOWERED": True,
        }
    p_thirds = _time_slices(ev_p, boundaries)
    mid_thirds = _time_slices(
        ev_mid if ev_mid is not None else ev_p.head(0), boundaries
    )
    rows: list[dict] = []
    sign_paths: dict[str, list[int]] = {
        f"{name}_H{h}": []
        for name in ("T1", "T1_mirror", "T2", "T3", "T4", "T5")
        for h in absorb.HOLDS_LTF
    }
    for i, (part, mid) in enumerate(zip(p_thirds, mid_thirds), start=1):
        s9 = part.filter(pl.col("arm") == "S9")
        base = part.filter(pl.col("arm") == "BASE")
        mirror = part.filter(pl.col("arm") == "MIRROR")
        mid_s9 = mid.filter(pl.col("arm") == "S9")
        mid_base = mid.filter(pl.col("arm") == "BASE")
        t4_control = _source_control_slice(controls["T4"], s9)
        t5_control = _source_control_slice(controls["T5"], part)
        record: dict = {
            "third": i,
            "boundary_start": str(boundaries[i - 1][0]),
            "boundary_end_exclusive": str(boundaries[i - 1][1]),
            "n_P": int(part.height),
            "n_T3": int(mid.height),
            "entry_ts_start": str(part["entry_ts"][0]) if part.height else None,
            "entry_ts_end": str(part["entry_ts"][-1]) if part.height else None,
            "reads": {},
        }
        for h in absorb.HOLDS_LTF:
            col = f"ret_bps_H{h}"
            t1 = _signed_read(
                absorb.contrast_day_clustered(s9, base, ret_col=col)
            )
            t1m = _signed_read(
                absorb.contrast_day_clustered(s9, mirror, ret_col=col)
            )
            t2 = _signed_read(
                _t2_dose(part, col, n_seeds=t2_seeds), effect_key="rho"
            )
            t3 = _signed_read(
                absorb.contrast_day_clustered(mid_s9, mid_base, ret_col=col)
            )
            t4_ref = _constant_control_on_treat_days(s9, t4_control, col)
            t4 = _signed_read(
                absorb.contrast_day_clustered(s9, t4_ref, ret_col=col)
            )
            t5 = _signed_read(
                absorb.contrast_day_clustered(base, t5_control, ret_col=col)
            )
            for name, value in (
                ("T1", t1),
                ("T1_mirror", t1m),
                ("T2", t2),
                ("T3", t3),
                ("T4", t4),
                ("T5", t5),
            ):
                record["reads"][f"{name}_H{h}"] = value
                if value["sign"] is not None:
                    sign_paths[f"{name}_H{h}"].append(value["sign"])
        rows.append(record)
    return {
        "n_total": int(ev_p.height),
        "thirds": rows,
        "sign_consistency": {
            name: (
                len(signs) == 3 and len(set(signs)) == 1
                if signs
                else None
            )
            for name, signs in sign_paths.items()
        },
        "note": (
            "L-24 F02 report layer; shared equal-duration DESIGN-band thirds; "
            "UNPOWERED thirds remain listed with n and available intervals"
        ),
    }


def step_design_reads(
    universe: dict,
    cuts: dict,
    floors: dict,
    *,
    t2_seeds: int = absorb.N_DERANGE_SEEDS,
    t2_plant_seeds: int = T2_PLANT_SEEDS,
    cf_seeds: int = 200,
) -> tuple[dict, dict]:
    """Build each pair's arm ONCE, then MDE → CF* → contrasts on that same arm.

    Design §9 order is preserved: each pair's MDE curves and CF* calibration are
    computed and written before that pair's first real contrast, and all three
    refer to the identical event population.
    """
    layers: dict = {"band": "DESIGN", "pairs": {}}
    mde_curves: dict = {"band": "DESIGN", "pairs": {}}
    # Reset tripwire merge file for this run
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "tripwire.json").write_text("{}\n")

    for pair_id, u in universe.items():
        tau = float(cuts["tau_by_pair"][pair_id]["tau"])
        zone = cuts["tau_by_pair"][pair_id]["zone_mode"]
        tau_w = float(cuts["p_wide_by_pair"][pair_id]["tau"])
        parts_p, parts_w, parts_mid, ib_parts = [], [], [], []
        bars_by: dict[str, pl.DataFrame] = {}
        skipped: list[dict] = []
        ib_failed: list[dict] = []
        located = {"P": 0, "P_WIDE": 0, "MID_RANGE": 0}
        kept = {"P": 0, "P_WIDE": 0, "MID_RANGE": 0}
        for sym in tqdm(u["usable"], desc=f"events {pair_id}", leave=False):
            try:
                bars = load_bars(sym, "DESIGN")
                bars_by[sym] = bars
                for tau_i, mode, dest in (
                    (tau, "P", parts_p),
                    (tau_w, "P_WIDE", parts_w),
                    (tau, "MID_RANGE", parts_mid),
                ):
                    sc, n_loc = _build_scored(
                        sym,
                        "DESIGN",
                        pair_id,
                        tau_i,
                        zone,
                        mode,
                        bars_1m=bars,
                    )
                    located[mode] += n_loc
                    kept[mode] += int(sc.height)
                    if sc.height:
                        dest.append(sc)
                if pair_id == "D1":
                    try:
                        ib_sc, _ = _build_scored(
                            sym,
                            "DESIGN",
                            "D1",
                            D1_IB_TAU,
                            "ib_width",
                            "P",
                            bars_1m=bars,
                        )
                        if ib_sc.height:
                            ib_parts.append(ib_sc)
                    except Exception as exc:
                        ib_failed.append({"symbol": sym, "error": str(exc)})
            except Exception as exc:
                # A swallowed failure silently removes a symbol from the PRIMARY
                # pooled read while power_census still counts it — record it so
                # layers and census can be reconciled (QA-9 I-1).
                skipped.append({"symbol": sym, "error": str(exc)})
                print(f"  skip {sym}/{pair_id}: {exc}", flush=True)

        ev_p = pl.concat(parts_p, how="diagonal_relaxed") if parts_p else None
        ev_w = pl.concat(parts_w, how="diagonal_relaxed") if parts_w else None
        ev_mid = pl.concat(parts_mid, how="diagonal_relaxed") if parts_mid else None

        # Build every control arm before computing any real contrast. The
        # resulting curves therefore satisfy §4.2/§9 for T4 and T5 as well as
        # T1, and the exact same rows are reused for the subsequent read.
        controls: dict[str, dict] = {}
        for name, ev in (("P", ev_p), ("P_WIDE", ev_w)):
            if ev is None:
                controls[name] = {
                    "T4": pl.DataFrame(),
                    "T5": pl.DataFrame(),
                    "T4_failed": [],
                    "T5_failed": [],
                }
                continue
            control_tau = tau if name == "P" else tau_w
            t4, t4_failed = _build_t4_control(pair_id, ev, bars_by)
            t5, t5_failed = _build_t5_control(
                pair_id,
                ev,
                bars_by,
                band="DESIGN",
                tau=control_tau,
                zone=zone,
            )
            controls[name] = {
                "T4": t4,
                "T5": t5,
                "T4_failed": t4_failed,
                "T5_failed": t5_failed,
            }

        ib_ev: pl.DataFrame | None = (
            pl.concat(ib_parts, how="diagonal_relaxed") if ib_parts else None
        )

        # 1. MDE at REALISED n, PER POOL, on the exact arms the contrasts use —
        #    before any contrast. P_WIDE is a separate stratum (design §3.2) and
        #    §5 labels each contrast against ITS OWN MDE.
        pair_mde = (
            mde_for_arm(ev_p, t2_plant_seeds=t2_plant_seeds)
            if ev_p is not None
            else {"UNPOWERED": True}
        )
        mde_by_pool = {
            "P": pair_mde,
            "P_WIDE": (
                mde_for_arm(ev_w, t2_plant_seeds=t2_plant_seeds)
                if ev_w is not None
                else {"UNPOWERED": True}
            ),
        }
        for name, ev in (("P", ev_p), ("P_WIDE", ev_w)):
            if ev is None:
                continue
            s9 = ev.filter(pl.col("arm") == "S9")
            base = ev.filter(pl.col("arm") == "BASE")
            ctrl = controls[name]
            mde_by_pool[name].update(_t4_mde(s9, ctrl["T4"]))
            mde_by_pool[name].update(
                mde_for_contrast(base, ctrl["T5"], prefix="T5")
            )
            mde_by_pool[name]["control_coverage"] = {
                "T4_n": int(ctrl["T4"].height),
                "T5_n": int(ctrl["T5"].height),
                "T4_failed": ctrl["T4_failed"],
                "T5_failed": ctrl["T5_failed"],
            }
        pair_mde_doc: dict = {**mde_by_pool}
        pair_mde_doc["T3_mid_range"] = (
            mde_for_arm(ev_mid, t2_plant_seeds=t2_plant_seeds)
            if ev_mid is not None
            else {"UNPOWERED": True}
        )
        pair_mde_doc["D1_ib_width_sensitivity"] = (
            mde_for_arm(ib_ev, t2_plant_seeds=t2_plant_seeds)
            if ib_ev is not None
            else {"UNPOWERED": True}
        )
        mde_curves["pairs"][pair_id] = pair_mde_doc
        _emit(OUT / "mde_curves.json", mde_curves)
        print(f"  {pair_id} MDE(realised n) {pair_mde.get('T1_H10')}", flush=True)

        # 2. CF* on the SAME pooled arm, planting 1x that MDE — before any contrast.
        mde_bps = (pair_mde.get("T1_H10") or {}).get("mde_bps")
        cf_pre: dict = {
            "cf_star": None,
            "status": "UNDERIVABLE",
            "reason": "no pool-P arm for this pair",
        }
        if ev_p is not None:
            try:
                cf_pre = absorb.calibrate_cf_star(
                    bars_by,
                    ev_p,
                    mde_bps=mde_bps,
                    n_seeds=cf_seeds,
                )
            except Exception as exc:
                cf_pre = {"cf_star": None, "status": "UNDERIVABLE", "error": str(exc)}
        _emit(OUT / f"tripwire_cf_{pair_id}.json", cf_pre)
        print(
            f"  {pair_id} CF* {cf_pre.get('status')} = {cf_pre.get('cf_star')}",
            flush=True,
        )

        failed_syms = {s["symbol"] for s in skipped}
        pair_out: dict = {
            "coverage": {
                "n_usable": u["n_usable"],
                "n_symbols_read": len(set(bars_by) - failed_syms),
                "n_symbols_failed": len(failed_syms),
                "failed": skipped,
                "n_events_located": located,
                "n_events_with_outcome": kept,
                "n_events_dropped_no_1m_path": {
                    k: located[k] - kept[k] for k in located
                },
                "note": (
                    "n_events_dropped_no_1m_path = located events with no "
                    "contiguous 1-minute outcome span (design §3.4 drop-and-COUNT); "
                    "a failed symbol is missing from at least one pool while "
                    "power_census.json still counts it — reconcile before disposition"
                ),
            }
        }
        for name, parts in (("P", parts_p), ("P_WIDE", parts_w)):
            if not parts:
                pair_out[name] = {"n": 0, "UNPOWERED": True}
                continue
            ev = pl.concat(parts, how="diagonal_relaxed")
            ev.write_parquet(OUT / f"events_DESIGN_{pair_id}_{name}.parquet")
            mde_info = mde_by_pool.get(name)
            pair_out[name] = _layers_for_events(
                pair_id,
                ev,
                pool_name=name,
                mde_info=mde_info,
                floors=floors,
                t2_seeds=t2_seeds,
            )

            _attach_t4_t5_reads(
                ev,
                pair_out[name],
                controls[name],
                mde_info,
            )

        # T3 mid-range
        if ev_mid is not None:
            ev_mid.write_parquet(OUT / f"events_DESIGN_{pair_id}_MID_RANGE.parquet")
            pair_out["T3_mid_range"] = _layers_for_events(
                pair_id,
                ev_mid,
                pool_name="MID_RANGE",
                mde_info=pair_mde_doc["T3_mid_range"],
                floors=None,
                t2_seeds=t2_seeds,
            )
        else:
            pair_out["T3_mid_range"] = {"n": 0, "UNPOWERED": True}

        # D1 ib_width sensitivity (count + thin layers on sample)
        if ib_ev is not None:
            pair_out["D1_ib_width_sensitivity"] = _layers_for_events(
                "D1",
                ib_ev,
                pool_name="P_ib025",
                mde_info=pair_mde_doc["D1_ib_width_sensitivity"],
                floors=None,
                t2_seeds=t2_seeds,
            )
            pair_out["D1_ib_width_sensitivity"]["failed"] = ib_failed

        third_boundaries = _design_third_boundaries()
        pair_out["time_stability_thirds"] = {
            "definition": "three equal-duration intervals of the frozen DESIGN band",
            "boundaries": [
                {
                    "third": i,
                    "start": str(start),
                    "end_exclusive": str(end),
                }
                for i, (start, end) in enumerate(third_boundaries, start=1)
            ],
            "P": _time_stability_thirds(
                ev_p if ev_p is not None else pl.DataFrame(),
                ev_mid,
                controls["P"],
                boundaries=third_boundaries,
                t2_seeds=t2_seeds,
            ),
            "P_WIDE": _time_stability_thirds(
                ev_w if ev_w is not None else pl.DataFrame(),
                ev_mid,
                controls["P_WIDE"],
                boundaries=third_boundaries,
                t2_seeds=t2_seeds,
            ),
        }

        # Tripwire on pool P (HARD) — CF* already calibrated above
        pair_out["tripwire"] = _run_tripwire(
            pair_id,
            parts_p,
            bars_by,
            pair_out.get("P") or {},
            cf_precomputed=cf_pre,
        )
        layers["pairs"][pair_id] = pair_out
        n = (pair_out.get("P") or {}).get("n", 0)
        print(f"  {pair_id} layers n_P={n}", flush=True)

    _emit(OUT / "layers.json", layers)
    _emit(OUT / "mde_curves.json", mde_curves)
    return layers, mde_curves


def _run_tripwire(
    pair_id: str,
    parts_p: list[pl.DataFrame],
    bars_by: dict[str, pl.DataFrame],
    p_layers: dict,
    *,
    cf_precomputed: dict,
) -> dict:
    if not parts_p:
        return {"status": "NO_EVENTS"}
    ev = pl.concat(parts_p, how="diagonal_relaxed")
    # CF* is DERIVED on this design's own stream or it does not exist. The
    # INFR-018 0.25 is a PRIOR only (AMENDMENT-4) and is never substituted —
    # an underivable CF* makes the survival rule inapplicable, which is
    # reported, not papered over.
    cf_doc = cf_precomputed
    cf_star = cf_doc.get("cf_star")
    cf_derived = cf_star is not None

    swapped_parts = []
    for sym, bars in bars_by.items():
        se = ev.filter(pl.col("symbol") == sym)
        if se.height < 2:
            continue
        try:
            sw, _cov = absorb.outcome_path_swap_fixed_h(bars, se, hold_ltf=10)
        except Exception:
            continue
        if sw.height:
            swapped_parts.append(sw)
    if not swapped_parts:
        return {
            "status": "NO_MATERIAL_EDGE_OR_NO_DONOR",
            "cf_star": cf_star,
            "cf_calibration": cf_doc,
        }
    sw_all = pl.concat(swapped_parts, how="diagonal_relaxed")
    bite = absorb.path_swap_bite_bps(sw_all)
    raw_t1 = (p_layers.get("T1") or {}).get("H10") or {}
    raw_t2 = (p_layers.get("T2") or {}).get("H10") or {}
    material_t1 = bool(raw_t1.get("excludes_zero"))
    material_t2 = raw_t2.get("label") == "SUPPORTED"
    material = material_t1 or material_t2

    sw_s9 = sw_all.filter(pl.col("arm") == "S9") if "arm" in sw_all.columns else sw_all
    sw_base = (
        sw_all.filter(pl.col("arm") == "BASE")
        if "arm" in sw_all.columns
        else pl.DataFrame()
    )
    dest_t1: dict = {}
    if sw_s9.height and sw_base.height and "ret_bps_H10" in sw_all.columns:
        dest_t1 = absorb.contrast_day_clustered(
            sw_s9, sw_base, ret_col="ret_bps_H10"
        )
    # T2 collapse: Spearman on swapped outcomes
    dest_t2: dict = {}
    if sw_all.height >= 8 and "signed_score" in sw_all.columns and "ret_bps_H10" in sw_all.columns:
        rho_sw, n_sw = absorb.spearman_finite(
            sw_all["signed_score"].to_numpy().astype(float),
            sw_all["ret_bps_H10"].to_numpy().astype(float),
        )
        dest_t2 = {"rho": rho_sw, "n": n_sw}

    def _collapse(dest, raw):
        if raw in (None, 0) or dest is None:
            return None
        return float(dest) / float(raw)

    raw_c = raw_t1.get("contrast")
    dest_c = dest_t1.get("contrast")
    collapse_t1 = _collapse(dest_c, raw_c)
    collapse_t2 = _collapse(dest_t2.get("rho"), raw_t2.get("rho"))

    def _survives(material_i, collapse, raw_val, dest_excl):
        # No derived CF* ⇒ the survival rule has no threshold and cannot be
        # evaluated. Never fall back to the 0.25 prior (AMENDMENT-4).
        if not cf_derived:
            return None
        return bool(
            material_i
            and collapse is not None
            and abs(collapse) > float(cf_star)
            and np.sign(collapse) == np.sign(raw_val if raw_val is not None else 0)
            and dest_excl
        )

    survives_t1 = _survives(
        material_t1, collapse_t1, raw_c, bool(dest_t1.get("excludes_zero"))
    )
    survives_t2 = _survives(
        material_t2,
        collapse_t2,
        raw_t2.get("rho"),
        dest_t2.get("rho") is not None and abs(dest_t2.get("rho") or 0) > 0,
    )
    # None (not False) when the gate could not be evaluated — "did not survive"
    # and "was never applied" must not read the same downstream.
    survives = (
        None if not cf_derived else (bool(survives_t1) or bool(survives_t2))
    )
    if not cf_derived:
        # The gate had no threshold to apply. Per Addendum §2.8 this is NOT a
        # clean bill of health and NOT a leak — it is an inapplicable gate.
        status = "CF_STAR_UNDERIVABLE_GATE_INAPPLICABLE" if material else "NO_MATERIAL_EDGE"
    elif survives:
        status = "LEAK_SURVIVAL_HARD_FAIL"
    else:
        status = "ADJUDICATED" if material else "NO_MATERIAL_EDGE"
    result = {
        "status": status,
        "cf_star_derived": cf_derived,
        "bite_ok": bite.get("bite_ok"),
        "adjudicable": bool(cf_derived and bite.get("bite_ok")),
        "material_raw_edge_T1": material_t1,
        "material_raw_edge_T2": material_t2,
        "raw_T1": raw_t1,
        "raw_T2": raw_t2,
        "swapped_T1": dest_t1,
        "swapped_T2": dest_t2,
        "collapse_fraction_T1": collapse_t1,
        "collapse_fraction_T2": collapse_t2,
        "cf_star": cf_star,
        "cf_calibration": cf_doc,
        "bite": bite,
        "n_swapped": int(sw_all.height),
        "survives_T1": survives_t1,
        "survives_T2": survives_t2,
        "survives": survives,
    }
    # Merge into tripwire.json (do not overwrite other pairs)
    path = OUT / "tripwire.json"
    existing = {}
    if path.exists():
        try:
            existing = json.loads(path.read_text())
        except Exception:
            existing = {}
    existing[pair_id] = result
    existing["cf_star_by_pair"] = {
        **(existing.get("cf_star_by_pair") or {}),
        pair_id: cf_star,
    }
    _emit(path, existing)
    return result


def step_confirm(
    universe: dict,
    cuts: dict,
    *,
    t2_seeds: int = absorb.N_DERANGE_SEEDS,
    t2_plant_seeds: int = T2_PLANT_SEEDS,
) -> dict:
    """One complete T1–T5 CONFIRM verify pass after freeze (design §9)."""
    absorb.assert_confirm_freeze_ready(OUT)
    out: dict = {"band": "CONFIRM", "pairs": {}}
    mde_curves: dict = {"band": "CONFIRM", "pairs": {}}
    for pair_id, u in universe.items():
        tau = float(cuts["tau_by_pair"][pair_id]["tau"])
        zone = cuts["tau_by_pair"][pair_id]["zone_mode"]
        tau_w = float(cuts["p_wide_by_pair"][pair_id]["tau"])
        parts_p: list[pl.DataFrame] = []
        parts_w: list[pl.DataFrame] = []
        parts_mid: list[pl.DataFrame] = []
        ib_parts: list[pl.DataFrame] = []
        bars_by: dict[str, pl.DataFrame] = {}
        failed: list[dict] = []
        ib_failed: list[dict] = []
        for sym in tqdm(u["usable"], desc=f"CONFIRM {pair_id}", leave=False):
            try:
                bars = load_bars(sym, "CONFIRM")
                bars_by[sym] = bars
                for tau_i, mode, dest in (
                    (tau, "P", parts_p),
                    (tau_w, "P_WIDE", parts_w),
                    (tau, "MID_RANGE", parts_mid),
                ):
                    sc, _ = _build_scored(
                        sym,
                        "CONFIRM",
                        pair_id,
                        tau_i,
                        zone,
                        mode,
                        bars_1m=bars,
                    )
                    if sc.height:
                        dest.append(sc)
                if pair_id == "D1":
                    try:
                        ib_sc, _ = _build_scored(
                            sym,
                            "CONFIRM",
                            "D1",
                            D1_IB_TAU,
                            "ib_width",
                            "P",
                            bars_1m=bars,
                        )
                        if ib_sc.height:
                            ib_parts.append(ib_sc)
                    except Exception as exc:
                        ib_failed.append({"symbol": sym, "error": str(exc)})
            except Exception as exc:
                failed.append({"symbol": sym, "error": str(exc)})
                print(f"  CONFIRM skip {sym}: {exc}", flush=True)
        if not parts_p:
            out["pairs"][pair_id] = {"n": 0, "UNPOWERED": True}
            continue

        ev_p = pl.concat(parts_p, how="diagonal_relaxed")
        ev_w = (
            pl.concat(parts_w, how="diagonal_relaxed")
            if parts_w
            else ev_p.head(0)
        )
        ev_mid = (
            pl.concat(parts_mid, how="diagonal_relaxed")
            if parts_mid
            else ev_p.head(0)
        )
        ib_ev = (
            pl.concat(ib_parts, how="diagonal_relaxed")
            if ib_parts
            else ev_p.head(0)
        )
        controls: dict[str, dict] = {}
        for name, ev, control_tau in (
            ("P", ev_p, tau),
            ("P_WIDE", ev_w, tau_w),
        ):
            t4, t4_failed = _build_t4_control(pair_id, ev, bars_by)
            t5, t5_failed = _build_t5_control(
                pair_id,
                ev,
                bars_by,
                band="CONFIRM",
                tau=control_tau,
                zone=zone,
            )
            controls[name] = {
                "T4": t4,
                "T5": t5,
                "T4_failed": t4_failed,
                "T5_failed": t5_failed,
            }

        # Complete realised-n MDE publication precedes every CONFIRM contrast.
        mde_by_pool = {
            "P": mde_for_arm(ev_p, t2_plant_seeds=t2_plant_seeds),
            "P_WIDE": mde_for_arm(ev_w, t2_plant_seeds=t2_plant_seeds),
        }
        for name, ev in (("P", ev_p), ("P_WIDE", ev_w)):
            s9 = ev.filter(pl.col("arm") == "S9")
            base = ev.filter(pl.col("arm") == "BASE")
            mde_by_pool[name].update(_t4_mde(s9, controls[name]["T4"]))
            mde_by_pool[name].update(
                mde_for_contrast(base, controls[name]["T5"], prefix="T5")
            )
        pair_mde = {
            **mde_by_pool,
            "T3_mid_range": mde_for_arm(
                ev_mid,
                t2_plant_seeds=t2_plant_seeds,
            ),
        }
        if pair_id == "D1":
            pair_mde["D1_ib_width_sensitivity"] = mde_for_arm(
                ib_ev,
                t2_plant_seeds=t2_plant_seeds,
            )
        mde_curves["pairs"][pair_id] = pair_mde
        _emit(OUT / "mde_curves_CONFIRM.json", mde_curves)

        pair_out: dict = {"failed": failed}
        for name, ev in (("P", ev_p), ("P_WIDE", ev_w)):
            ev.write_parquet(OUT / f"events_CONFIRM_{pair_id}_{name}.parquet")
            block = _layers_for_events(
                pair_id,
                ev,
                pool_name=name,
                mde_info=mde_by_pool[name],
                floors=None,
                t2_seeds=t2_seeds,
            )
            _attach_t4_t5_reads(
                ev,
                block,
                controls[name],
                mde_by_pool[name],
            )
            pair_out[name] = block
        ev_mid.write_parquet(OUT / f"events_CONFIRM_{pair_id}_MID_RANGE.parquet")
        pair_out["T3_mid_range"] = _layers_for_events(
            pair_id,
            ev_mid,
            pool_name="MID_RANGE",
            mde_info=pair_mde["T3_mid_range"],
            floors=None,
            t2_seeds=t2_seeds,
        )
        if pair_id == "D1":
            ib_ev.write_parquet(
                OUT / f"events_CONFIRM_{pair_id}_IB_WIDTH_SENSITIVITY.parquet"
            )
            pair_out["D1_ib_width_sensitivity"] = _layers_for_events(
                "D1",
                ib_ev,
                pool_name="P_ib025",
                mde_info=pair_mde["D1_ib_width_sensitivity"],
                floors=None,
                t2_seeds=t2_seeds,
            )
            pair_out["D1_ib_width_sensitivity"]["failed"] = ib_failed
        # Preserve the primary summary fields consumed by the census/smoke.
        pair_out["n"] = pair_out["P"].get("n", 0)
        pair_out["n_S9"] = pair_out["P"].get("n_S9", 0)
        out["pairs"][pair_id] = pair_out
    _emit(OUT / "layers_CONFIRM.json", out)
    _emit(OUT / "mde_curves_CONFIRM.json", mde_curves)
    return out


def assert_smoke_integrity(
    power: dict,
    layers: dict,
    confirm: dict,
) -> dict:
    """Fail a throwaway smoke unless every representative read path resolves."""
    checks: dict[str, dict] = {}
    failures: list[str] = []
    for pair_id, pair in layers.get("pairs", {}).items():
        p_power = (power.get("pairs", {}).get(pair_id) or {}).get("totals", {})
        coverage = pair.get("coverage") or {}
        located = (coverage.get("n_events_located") or {}).get("P")
        kept = (coverage.get("n_events_with_outcome") or {}).get("P")
        p = pair.get("P") or {}
        pw = pair.get("P_WIDE") or {}
        confirm_pair = confirm.get("pairs", {}).get(pair_id) or {}

        def _curve_explicit(block: dict, key: str, value_key: str) -> bool:
            curve = ((block.get("mde") or {}).get(key) or {})
            return curve.get(value_key) is not None or curve.get("UNPOWERED") is True

        def _labels_present(block: dict, read: str) -> bool:
            rows = block.get(read) or {}
            return all(
                isinstance(rows.get(f"H{h}"), dict)
                and bool((rows.get(f"H{h}") or {}).get("label"))
                for h in absorb.HOLDS_LTF
            )

        stability = pair.get("time_stability_thirds") or {}
        expected_reads = {
            f"{name}_H{h}"
            for name in ("T1", "T1_mirror", "T2", "T3", "T4", "T5")
            for h in absorb.HOLDS_LTF
        }

        def _thirds_complete(pool_name: str) -> bool:
            thirds = (stability.get(pool_name) or {}).get("thirds") or []
            bounds = stability.get("boundaries") or []
            return len(thirds) == len(bounds) == 3 and all(
                set(third.get("reads") or {}) == expected_reads
                and third.get("boundary_start") == bounds[i].get("start")
                and third.get("boundary_end_exclusive")
                == bounds[i].get("end_exclusive")
                for i, third in enumerate(thirds)
            )

        row = {
            "P_nonempty": int(p.get("n") or 0) > 0,
            "P_WIDE_nonempty": int(pw.get("n") or 0) > 0,
            "T3_nonempty": int((pair.get("T3_mid_range") or {}).get("n") or 0) > 0,
            "CONFIRM_nonempty": int(
                confirm_pair.get("n") or 0
            )
            > 0,
            "CONFIRM_T3_nonempty": int(
                (confirm_pair.get("T3_mid_range") or {}).get("n") or 0
            ) > 0,
            "census_located_reconciles": located == p_power.get("P"),
            "census_kept_reconciles": kept == p.get("n"),
            "DESIGN_boundaries_present": len(
                (pair.get("time_stability_thirds") or {}).get("boundaries") or []
            ) == 3,
            "DESIGN_P_thirds_present": len(
                ((pair.get("time_stability_thirds") or {}).get("P") or {}).get(
                    "thirds"
                ) or []
            ) == 3,
            "DESIGN_P_WIDE_thirds_present": len(
                ((pair.get("time_stability_thirds") or {}).get("P_WIDE") or {}).get(
                    "thirds"
                ) or []
            ) == 3,
            "DESIGN_P_thirds_complete": _thirds_complete("P"),
            "DESIGN_P_WIDE_thirds_complete": _thirds_complete("P_WIDE"),
        }
        for pool_name, block in (("P", p), ("P_WIDE", pw)):
            row[f"{pool_name}_T4_donors"] = int(
                (block.get("T4_control_coverage") or {}).get("n_control") or 0
            ) > 0
            row[f"{pool_name}_T5_donors"] = int(
                (block.get("T5_control_coverage") or {}).get("n_control") or 0
            ) > 0
            row[f"{pool_name}_T2_derangement"] = any(
                int((v or {}).get("n_seeds") or 0) > 0
                for v in (block.get("T2") or {}).values()
            )
            for read in ("T1", "T1_mirror", "T2", "T4", "T5"):
                row[f"{pool_name}_{read}_labels"] = _labels_present(block, read)
            for h in absorb.HOLDS_LTF:
                row[f"{pool_name}_T2_MDE_H{h}"] = _curve_explicit(
                    block, f"T2_H{h}", "mde_rho"
                )
                row[f"{pool_name}_T4_MDE_H{h}"] = _curve_explicit(
                    block, f"T4_H{h}", "mde_bps"
                )
                row[f"{pool_name}_T5_MDE_H{h}"] = _curve_explicit(
                    block, f"T5_H{h}", "mde_bps"
                )
        for name in ("T3_mid_range", "D1_ib_width_sensitivity"):
            block = pair.get(name) or {}
            if block:
                row[f"{name}_MDE_explicit"] = all(
                    _curve_explicit(block, f"T1_H{h}", "mde_bps")
                    for h in absorb.HOLDS_LTF
                )
        for pool_name in ("P", "P_WIDE"):
            block = confirm_pair.get(pool_name) or {}
            row[f"CONFIRM_{pool_name}_nonempty"] = int(block.get("n") or 0) > 0
            for read in ("T1", "T1_mirror", "T2", "T4", "T5"):
                row[f"CONFIRM_{pool_name}_{read}_labels"] = _labels_present(
                    block, read
                )
            for h in absorb.HOLDS_LTF:
                row[f"CONFIRM_{pool_name}_T2_MDE_H{h}"] = _curve_explicit(
                    block, f"T2_H{h}", "mde_rho"
                )
        if pair_id == "D1":
            confirm_ib = confirm_pair.get("D1_ib_width_sensitivity") or {}
            row["CONFIRM_D1_ib_width_nonempty"] = int(
                confirm_ib.get("n") or 0
            ) > 0
            row["CONFIRM_D1_ib_width_MDE_explicit"] = all(
                _curve_explicit(confirm_ib, f"T1_H{h}", "mde_bps")
                for h in absorb.HOLDS_LTF
            )
        cf = ((pair.get("tripwire") or {}).get("cf_calibration") or {})
        cf_status = cf.get("status")
        row["cf_star_explicit"] = bool(
            cf_status == "DERIVED"
            or (cf_status == "UNDERIVABLE" and (cf.get("reason") or cf.get("error")))
        )
        row["path_swap_donors"] = int(
            (pair.get("tripwire") or {}).get("n_swapped") or 0
        ) > 0
        checks[pair_id] = row
        failures.extend(
            f"{pair_id}:{name}" for name, ok in row.items() if not ok
        )
    result = {"passed": not failures, "checks": checks, "failures": failures}
    _emit(OUT / "smoke_integrity.json", result)
    if failures:
        raise RuntimeError("SMOKE integrity failed: " + ", ".join(failures))
    return result


def main() -> None:
    global OUT

    ap = argparse.ArgumentParser(description="SPDR-009 absorb screen")
    ap.add_argument("--prep", action="store_true", help="freeze universe/cuts/floors only")
    ap.add_argument(
        "--execute",
        action="store_true",
        help="run DESIGN+CONFIRM reads (requires operator execution approval)",
    )
    ap.add_argument(
        "--smoke",
        action="store_true",
        help=(
            "run a reduced integrity probe in a new throwaway directory; "
            "never writes SPDR-009/results"
        ),
    )
    ap.add_argument("--symbols", nargs="*", default=None)
    ap.add_argument("--pairs", nargs="*", default=None)
    args = ap.parse_args()
    if not args.prep and not args.execute and not args.smoke:
        ap.error("pass --prep, --smoke, and/or --execute")
    if args.smoke and args.execute:
        ap.error("--smoke and --execute are separate modes")

    if args.smoke:
        OUT = Path(tempfile.mkdtemp(prefix="spdr009-smoke-", dir="/private/tmp"))
        args.symbols = args.symbols or list(SMOKE_SYMBOLS)
        args.pairs = args.pairs or ["D1"]
        print(f"smoke output: {OUT}", flush=True)

    repo_root()
    step_frozen()
    universe = step_universe()
    if args.pairs:
        universe = {k: v for k, v in universe.items() if k in args.pairs}
    if args.symbols:
        for k, v in universe.items():
            v["usable"] = [s for s in v["usable"] if s in args.symbols]
            v["n_usable"] = len(v["usable"])

    cuts = step_pool_cuts(universe, sample_symbols=args.symbols)
    floors = step_floors(universe)

    if args.prep and not args.execute and not args.smoke:
        print(
            "prep complete — pool_cuts/floors/universe frozen; no outcome reads",
            flush=True,
        )
        return

    absorb.assert_confirm_freeze_ready(OUT)
    power = step_power_census(universe, cuts)
    # MDE curves and CF* are computed inside step_design_reads on the SAME arm
    # the contrasts use, and are written to disk before any contrast runs.
    layers, _mde = step_design_reads(
        universe,
        cuts,
        floors,
        t2_seeds=SMOKE_T2_SEEDS if args.smoke else absorb.N_DERANGE_SEEDS,
        t2_plant_seeds=(
            SMOKE_T2_PLANT_SEEDS if args.smoke else T2_PLANT_SEEDS
        ),
        cf_seeds=SMOKE_CF_SEEDS if args.smoke else 200,
    )
    confirm = step_confirm(
        universe,
        cuts,
        t2_seeds=SMOKE_T2_SEEDS if args.smoke else absorb.N_DERANGE_SEEDS,
        t2_plant_seeds=(
            SMOKE_T2_PLANT_SEEDS if args.smoke else T2_PLANT_SEEDS
        ),
    )
    _emit(
        OUT / "census.json",
        {
            "DESIGN": {
                k: {
                    "n": (v.get("P") or {}).get("n"),
                    "n_S9": (v.get("P") or {}).get("n_S9"),
                    "census_P": (power["pairs"].get(k) or {}).get("totals", {}).get("P"),
                    "coverage": (v.get("coverage") or {}),
                }
                for k, v in layers.get("pairs", {}).items()
            },
            "CONFIRM": {
                k: v.get("n") for k, v in confirm.get("pairs", {}).items()
            },
        },
    )
    if args.smoke:
        assert_smoke_integrity(power, layers, confirm)
        print(f"smoke passed — isolated artifacts retained at {OUT}", flush=True)
        return
    print(
        "DESIGN+CONFIRM execution complete — stop for operator disposition",
        flush=True,
    )


if __name__ == "__main__":
    main()
