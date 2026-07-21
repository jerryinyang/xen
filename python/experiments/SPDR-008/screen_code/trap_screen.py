"""SPDR-008 signed-trap breadth screen (S3 Δ+) — TRAIN-only, disposition-only.

Runs the ``xen.sigbar.trap`` object across the A5-fitted breadth cross-section, per
boundary type {IB, PVA, PRIOR} INDEPENDENTLY, and emits the four report-layer reads
(design §4) with dependence-honest uncertainty:

  T1  load-monotonicity : Spearman ρ(trap_load, mfe_rev_norm) vs a >=2000-seed
                          trap-load-derangement null (PRIMARY, signed)
  T2  tier marginal     : HIGH-LOW mfe_rev_norm contrast, day-clustered bootstrap
  T3  unsigned base     : confirmed-trap vs ordinary-touch excursion (P-01, disclosure)
  T4  availability      : trap vs matched-unconditional cross-session control (>=25-seed)
  tripwire              : reversal_path_swap (future-destroy, HARD) + pooled bite

Nothing is booked P&L (``check_no_local_accounting`` stays satisfied); every read is a
report layer (INFR-016), no ``pass`` field, no auto-verdict. Bands are the operator's.

Run:
  uv run --with nautilus_trader==1.230.0 --with polars --with numpy --with pandas
    --with tqdm --with scipy --with matplotlib python
    python/experiments/SPDR-008/screen_code/trap_screen.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import polars as pl
from scipy.stats import spearmanr
from tqdm.auto import tqdm

sys.path.insert(0, "python/src")

from xen.estimand_validation import check_no_local_accounting  # noqa: E402
from xen.evaluation import block_bootstrap_ci  # noqa: E402
from xen.sigbar import acceptance, fences, sessions, spine, trap  # noqa: E402
from xen.sigbar.baselines import residualise  # noqa: E402

ROOT = Path(".").resolve()
OUT = ROOT / "python/experiments/SPDR-008/results"
OUT.mkdir(parents=True, exist_ok=True)
BASELINES = "python/experiments/INFR-017/results/seasonal_baselines.parquet"
L = 15
SPEC = spine.anchor_spec()
BANDS = ("DESIGN", "CONFIRM")
N_DERANGE = 2000
DAY_BLOCK = spine.DAY_BLOCK
BOUNDARY_COLS = {"IB": ("ib_high", "ib_low"), "PVA": ("pva_high", "pva_low"),
                 "PRIOR": ("prior_high", "prior_low")}


# --------------------------------------------------------------------------- #
# Per-symbol event assembly
# --------------------------------------------------------------------------- #
def _attach(symbol: str, band: str):
    bars = fences.load_bars(symbol, band, root=ROOT)
    if bars.height == 0:
        return None, None, None
    lo, hi = bars["OpenTime"].min(), bars["OpenTime"].max()
    anch = sessions.anchor_table(SPEC, lo, hi)
    sess = sessions.session_breaks(bars, anch, L)
    joined = sessions.attach_sessions(bars, anch, L)
    bl = pl.scan_parquet(BASELINES).filter(pl.col("symbol") == symbol).collect()
    if bl.height:
        joined = joined.with_columns(
            pl.when(pl.col("Volume") > 0).then(pl.col("Delta") / pl.col("Volume"))
            .otherwise(None).alias("delta_ratio")
        )
        joined = residualise(joined, bl, "delta_ratio", time_col="OpenTime")
    else:
        joined = joined.with_columns(pl.lit(None, dtype=pl.Float64).alias("delta_ratio_resid"))
    return bars, sess, joined


def _ordinary_touch_entries(joined: pl.DataFrame, pokes: pl.DataFrame,
                            trap_anchors: set) -> pl.DataFrame:
    """Non-trap boundary pokes as −poke_side reversal-direction entries (T3 P-01 base)."""
    nt = pokes.filter(~pl.col("anchor_ts").is_in(list(trap_anchors))) if trap_anchors else pokes
    if nt.height == 0:
        return pl.DataFrame()
    eb = joined.select(pl.col("OpenTime").alias("entry_ts"), pl.col("Open").alias("entry"))
    e = (nt.with_columns((pl.col("poke_ts") + pl.duration(minutes=1)).alias("entry_ts"))
         .join(eb, on="entry_ts", how="inner")
         .with_columns((-pl.col("poke_side")).alias("side"),
                       pl.col("entry_ts").dt.truncate("1d").alias("day")))
    return e.select("anchor_ts", "entry_ts", "session_end", "entry", "side", "ib_width", "day")


def _events_for_symbol(symbol: str, band: str):
    """Confirmed traps + non-trap-touch entries for one symbol/band. + (bars, sessions)."""
    bars, sess, joined = _attach(symbol, band)
    if joined is None:
        return trap._empty_traps(), {}, pl.DataFrame(), pl.DataFrame()
    if band == "DESIGN":
        trap.assert_ib_matches_frozen(joined, sess)  # HARD regression guard, IB only
    lv = trap.boundary_levels(joined, sess)
    ib_lv = sess.select("anchor_ts", "ib_high", "ib_low", "ib_width")
    parts, ot = [], {}
    for bt, (up_c, dn_c) in BOUNDARY_COLS.items():
        levels = ib_lv if bt == "IB" else lv
        if levels.height == 0 or up_c not in levels.columns:
            continue
        pokes = trap.find_pokes_at_level(joined, levels, up_c, dn_c)
        if pokes.height == 0:
            continue
        if bt == "IB":  # reuse FROZEN evaluate_discriminator for the reject call
            fp = acceptance.find_pokes(joined, sess, 0.0)
            rej = acceptance.evaluate_discriminator(joined, fp, trap._D4_FROZEN)
        else:
            rej = trap.d4_reject_at_level(joined, pokes)
        t = trap.find_traps(joined, pokes, rej)
        trap_anchors = set(t["anchor_ts"].to_list()) if t.height else set()
        ot[bt] = _ordinary_touch_entries(joined, pokes, trap_anchors)
        if t.height == 0:
            continue
        parts.append(t.with_columns(pl.lit(bt).alias("boundary"), pl.lit(symbol).alias("symbol")))
    events = pl.concat(parts) if parts else trap._empty_traps()
    if events.height:
        events = events.with_columns(
            ((pl.col("entry_ts") - pl.col("anchor_ts")).dt.total_minutes()).alias("entry_phase"),
            pl.col("anchor_ts").dt.truncate("1d").alias("day"),
        )
    return events, ot, bars, sess


# --------------------------------------------------------------------------- #
# Reads (report layers) — full adjudication machinery (operator directive, QA-3)
# --------------------------------------------------------------------------- #
def _spearman(load: np.ndarray, exc: np.ndarray) -> float:
    ok = ~np.isnan(load) & ~np.isnan(exc)
    if ok.sum() < 5:
        return float("nan")
    return float(spearmanr(load[ok], exc[ok]).correlation)


def _rankdata(a: np.ndarray) -> np.ndarray:
    order = a.argsort()
    r = np.empty(len(a), float)
    r[order] = np.arange(1, len(a) + 1)
    return r


def _spearman_derangement_null(load: np.ndarray, exc: np.ndarray, n_seeds: int, seed: int):
    """(rho, null[]) — derangement of load vs exc, fast rank-Pearson (zero fixed points)."""
    ok = ~np.isnan(load) & ~np.isnan(exc)
    load, exc = load[ok], exc[ok]
    n = len(load)
    if n < 8:
        return float("nan"), np.array([])
    rl, re = _rankdata(load), _rankdata(exc)
    rlc, rec = rl - rl.mean(), re - re.mean()
    denom = np.sqrt((rlc**2).sum() * (rec**2).sum())
    rho = float((rlc * rec).sum() / denom) if denom > 0 else float("nan")
    rng = np.random.default_rng(seed)
    null = np.empty(n_seeds)
    for s in range(n_seeds):
        perm = trap.derange(n, rng)
        null[s] = (rlc[perm] * rec).sum() / denom if denom > 0 else np.nan
    return rho, null[~np.isnan(null)]


def t1_monotonicity(ev: pl.DataFrame, seed: int = 20180801) -> dict:
    """Spearman ρ(trap_load, mfe_rev_norm) vs a >=2000-seed derangement null + MDE."""
    d = ev.filter(pl.col("trap_load").is_not_null()).select("trap_load", "mfe_rev_norm", "mfe_rev_bps")
    n = d.height
    if n < 8:
        return {"n": n, "rho": None, "UNPOWERED": True}
    load = d["trap_load"].to_numpy()
    rho, null = _spearman_derangement_null(load, d["mfe_rev_norm"].to_numpy(), N_DERANGE, seed)
    rho_bps = _spearman(load, d["mfe_rev_bps"].to_numpy())  # raw-bps disclosure (I-3 guard)
    p_one = float((null >= rho).mean()) if null.size else float("nan")
    mde_rho = float(np.quantile(null, 0.95)) if null.size else None  # MDE = null 95th pct
    return {"n": n, "rho": rho, "rho_bps_disclosure": rho_bps,
            "derangement_null_mean": float(null.mean()) if null.size else None,
            "derangement_null_ci": [float(np.quantile(null, 0.025)), float(np.quantile(null, 0.975))]
            if null.size else None,
            "one_sided_p_ge_observed": p_one, "mde_rho_at_n": mde_rho, "n_seeds": int(null.size),
            "SUPPORTED": bool(null.size and rho >= mde_rho and p_one <= 0.05),
            "UNPOWERED": n < 20}


def _plant_mde(treat: np.ndarray, t_days: np.ndarray, base_ctrl: float, grid=None) -> float | None:
    """Smallest additive shift u on the treatment arm whose day-clustered CI of the
    (treat+u − base_ctrl) contrast excludes 0 at the realised n (design §4.2 MDE)."""
    if grid is None:
        grid = np.arange(0.0, 3.01, 0.25)
    uniq = np.unique(t_days)
    if len(uniq) < 3:
        return None
    for u in grid:
        day_means = np.array([np.nanmean(treat[t_days == d]) + u - base_ctrl for d in uniq])
        r = block_bootstrap_ci(day_means, np.nanmean, block=DAY_BLOCK)
        if r["ci"][0] > 0:
            return float(u)
    return None


def t2_tier_marginal(ev: pl.DataFrame) -> dict:
    """HIGH-LOW mfe_rev_norm contrast (day-clustered) + MDE — the signed marginal value."""
    hi = ev.filter(pl.col("tier") == "HIGH")
    lo = ev.filter(pl.col("tier") == "LOW")
    if hi.height < 3 or lo.height < 3:
        return {"n_high": hi.height, "n_low": lo.height, "UNPOWERED": True}

    def _daymean(df):
        g = df.group_by("day").agg(pl.col("mfe_rev_norm").mean().alias("m"))
        return {r["day"]: r["m"] for r in g.iter_rows(named=True)}
    mh, ml = _daymean(hi), _daymean(lo)
    shared = sorted(set(mh) & set(ml))
    if len(shared) >= 3:
        diffs = np.array([mh[d] - ml[d] for d in shared])
        r = block_bootstrap_ci(diffs, np.mean, block=DAY_BLOCK)
        excl = (r["ci"][0] > 0) or (r["ci"][1] < 0)
        paired = {"n_shared_days": len(shared), "mean": r["stat"], "ci": r["ci"], "excludes_zero": excl}
    else:
        paired = {"n_shared_days": len(shared), "UNPOWERED": True}
    mde = _plant_mde(hi["mfe_rev_norm"].to_numpy(),
                     hi["day"].to_numpy(), float(lo["mfe_rev_norm"].mean()))
    return {"n_high": hi.height, "n_low": lo.height,
            "high_mean": float(hi["mfe_rev_norm"].mean()), "low_mean": float(lo["mfe_rev_norm"].mean()),
            "unpaired_diff": float(hi["mfe_rev_norm"].mean() - lo["mfe_rev_norm"].mean()),
            "mde_ibw": mde, "paired_day_contrast": paired}


def t4_availability(ev: pl.DataFrame, bars_by: dict, sess_by: dict) -> dict:
    """Trap mfe_rev_norm vs matched-unconditional cross-session control (pooled) + day-clustered CI."""
    trap_vals, trap_days, ctrl_vals = [], [], []
    for sym in ev["symbol"].unique().to_list():
        se = ev.filter(pl.col("symbol") == sym)
        bars, sess = bars_by.get(sym), sess_by.get(sym)
        if bars is None or sess is None or se.height == 0:
            continue
        req = se.select("anchor_ts", "side", "session_end",
                        pl.col("entry_phase").cast(pl.Int64).alias("entry_phase"))
        try:
            ctrl = spine.matched_unconditional(bars, req, sess, tp1_ibw=None)
        except Exception:
            continue
        if ctrl.height:
            ctrl_vals.append(ctrl["mfe_norm"].to_numpy())
        trap_vals.append(se["mfe_rev_norm"].to_numpy())
        trap_days.append(se["day"].to_numpy())
    if not trap_vals or not ctrl_vals:
        return {"UNPOWERED": True}
    tv, td = np.concatenate(trap_vals), np.concatenate(trap_days)
    cv = np.concatenate(ctrl_vals)
    cmean = float(np.nanmean(cv))
    # day-clustered CI on (trap day-mean − pooled control mean)
    uniq = np.unique(td)
    day_contrast = np.array([np.nanmean(tv[td == d]) - cmean for d in uniq])
    r = block_bootstrap_ci(day_contrast, np.nanmean, block=DAY_BLOCK) if len(uniq) >= 3 else None
    mde = _plant_mde(tv, td, cmean)
    return {"n_trap": int(len(tv)), "n_control": int(len(cv)),
            "trap_mean": float(np.nanmean(tv)), "control_mean": cmean,
            "contrast": float(np.nanmean(tv) - cmean),
            "day_clustered_ci": (r["ci"] if r else None),
            "excludes_zero": (bool(r["ci"][0] > 0 or r["ci"][1] < 0) if r else None),
            "mde_ibw": mde}


def t3_ordinary_touch(ev_trap: pl.DataFrame, pokes_nontrap: dict, bars_by: dict) -> dict:
    """P-01 base: confirmed-trap vs ordinary (non-trap) boundary-touch reversal-direction excursion."""
    ot_vals = []
    for sym, req in pokes_nontrap.items():
        bars = bars_by.get(sym)
        if bars is None or req.height == 0:
            continue
        try:
            e = spine.evaluate_entries(bars, req, tp1_ibw=None)
        except Exception:
            continue
        if e.height:
            ot_vals.append(e["mfe_norm"].to_numpy())
    if not ot_vals or ev_trap.height == 0:
        return {"UNPOWERED": True}
    ot = np.concatenate(ot_vals)
    tv = ev_trap["mfe_rev_norm"].to_numpy()
    return {"n_trap": int(len(tv)), "n_ordinary_touch": int(len(ot)),
            "trap_mean": float(np.nanmean(tv)), "ordinary_touch_mean": float(np.nanmean(ot)),
            "contrast_geometry": float(np.nanmean(tv) - np.nanmean(ot)),
            "note": "P-01 disclosure: how much reversal is failed-poke GEOMETRY vs a generic touch; "
                    "the SIGNED warrant is T1/T2, not this"}


def tripwire_path_swap(ev: pl.DataFrame, bars_by: dict, t1: dict, t2: dict) -> dict:
    """reversal_path_swap (future-destroy, HARD): collapse of the SIGNED reads + bite.

    A within-trap future-derangement (spine.outcome_path_swap) breaks the pairing of
    each trap's LOAD/TIER with its outcome, so it correctly referees the SIGNED reads —
    T1 ρ(load, excursion) and the T2 HIGH−LOW tier contrast must collapse toward 0 when
    the outcome is a random other trap's future. It is deliberately NOT used to adjudicate
    the T4 mean-availability contrast: a permutation preserves the trap mean, so it cannot
    referee a mean (B-6 vacuity). T4's causality rests on the ≤t−1 construction (poke/
    reclaim all before entry) and the matched-unconditional control (the unconditional-
    entry comparison itself). Material-edge precondition (design §4.3) on the SIGNED reads:
    with T1 ρ≈0 and the T2 CI spanning 0, there is no material signed edge to leak-test →
    NO_MATERIAL_EDGE (SPDR-007 D-2 precedent), never a hard fail.
    """
    swapped_parts, real_mfe_map = [], {}
    n_spliced = 0
    for sym in ev["symbol"].unique().to_list():
        se = ev.filter(pl.col("symbol") == sym)
        bars = bars_by.get(sym)
        if bars is None or se.height < 2:
            continue
        req = se.select("anchor_ts", "entry_ts", "session_end", "entry", "side", "ib_width",
                        "day", "trap_load", "tier")
        try:
            real = spine.evaluate_entries(bars, req, tp1_ibw=None)
            for rr in real.select("anchor_ts", "mfe").iter_rows(named=True):
                real_mfe_map[(sym, rr["anchor_ts"])] = rr["mfe"]
            sw, cov = spine.outcome_path_swap(bars, req, tp1_ibw=None)
        except Exception:
            continue
        n_spliced += int(cov.get("n_spliced", 0))
        if sw.height:
            swapped_parts.append(sw.with_columns(pl.lit(sym).alias("symbol")))
    if not swapped_parts:
        return {"UNPOWERED": True, "note": "no swappable events"}
    sw_all = pl.concat(swapped_parts, how="diagonal")
    donor_mfe = [real_mfe_map.get((r["symbol"], r["donor_anchor_ts"]))
                 for r in sw_all.select("symbol", "donor_anchor_ts").iter_rows(named=True)]
    sw_all = sw_all.with_columns(pl.Series("donor_mfe", donor_mfe, dtype=pl.Float64))
    bite = spine.path_swap_bite(sw_all)

    # SIGNED-read collapse under the swap (the tripwire's real job).
    d = sw_all.filter(pl.col("trap_load").is_not_null())
    swapped_rho = _spearman(d["trap_load"].to_numpy(), d["mfe_norm"].to_numpy()) if d.height >= 8 else None
    hi = sw_all.filter(pl.col("tier") == "HIGH")["mfe_norm"]
    lo = sw_all.filter(pl.col("tier") == "LOW")["mfe_norm"]
    swapped_tier = (float(hi.mean() - lo.mean()) if hi.len() and lo.len() else None)
    raw_rho = t1.get("rho")
    t2pc = t2.get("paired_day_contrast", {})
    material = bool(t1.get("SUPPORTED") or t2pc.get("excludes_zero"))

    def _cf(dest, raw):
        return (float(dest / raw) if (raw not in (None, 0) and dest is not None) else None)
    return {"n_spliced": n_spliced, "bite": bite,
            "raw_T1_rho": raw_rho, "swapped_T1_rho": swapped_rho,
            "T1_collapse_fraction": _cf(swapped_rho, raw_rho),
            "raw_T2_tier": t2.get("unpaired_diff"), "swapped_T2_tier": swapped_tier,
            "T2_collapse_fraction": _cf(swapped_tier, t2.get("unpaired_diff")),
            "material_signed_edge": material,
            "status": ("ADJUDICATED" if material else "NO_MATERIAL_EDGE"),
            "note": "adjudicates the SIGNED reads (T1 ρ, T2 tier); T4 mean-availability is NOT "
                    "swap-adjudicable (B-6 mean-vacuity) — its causality rests on ≤t−1 + the matched "
                    "control. No material signed edge (T1 ρ≈0, T2 CI spans 0) → NO_MATERIAL_EDGE, not "
                    "a leak; bite>0.5 confirms the swap has teeth"}


# --------------------------------------------------------------------------- #
# Money floor (design §6.1)
# --------------------------------------------------------------------------- #
def money_floor(events: pl.DataFrame) -> list[dict]:
    rows = []
    for sym in events["symbol"].unique().to_list():
        se = events.filter(pl.col("symbol") == sym)
        ibw_bps = 1e4 * (se["ib_width"] / se["entry"]).median()
        rows.append({"symbol": sym, "design_median_ib_width_bps": float(ibw_bps),
                     "taker_rt": 11.0, "funding_approx": 3.0,
                     "floor_ex_spread_bps": 14.0,
                     "note": "spread from tick/flip-pair per symbol at graduation; SpreadBps UNUSABLE"})
    return rows


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main(limit: int | None = None) -> None:
    fences.assert_frozen_inputs(root=ROOT)
    for d in ("python/experiments/SPDR-008/screen_code", "python/experiments/SPDR-008/analysis_code"):
        chk = check_no_local_accounting(d)
        if not chk.get("ok", True):
            raise RuntimeError(f"check_no_local_accounting FAILED on {d}: {chk}")

    a5 = pl.scan_parquet(BASELINES).select("symbol").unique().collect()["symbol"].to_list()
    a5 = sorted(a5)
    if limit:
        a5 = a5[:limit]

    all_ev = {b: [] for b in BANDS}
    bars_by = {b: {} for b in BANDS}
    sess_by = {b: {} for b in BANDS}
    ot_by = {b: {bt: {} for bt in trap.BOUNDARY_TYPES} for b in BANDS}
    n_skip = {b: 0 for b in BANDS}
    for band in BANDS:
        for sym in tqdm(a5, desc=f"events/{band}"):
            try:
                ev, ot, bars, sess = _events_for_symbol(sym, band)
            except Exception as e:
                tqdm.write(f"  skip {sym}/{band}: {type(e).__name__}: {e}")
                n_skip[band] += 1
                continue
            for bt, otf in (ot or {}).items():
                if otf is not None and otf.height:
                    ot_by[band][bt][sym] = otf
            if ev.height:
                all_ev[band].append(ev)
                bars_by[band][sym] = bars
                sess_by[band][sym] = sess

    des = pl.concat(all_ev["DESIGN"]) if all_ev["DESIGN"] else trap._empty_traps()
    con = pl.concat(all_ev["CONFIRM"]) if all_ev["CONFIRM"] else trap._empty_traps()

    # Per-boundary DESIGN trap-load tercile cuts (frozen; applied to both bands).
    cuts = {}
    for bt in trap.BOUNDARY_TYPES:
        v = des.filter((pl.col("boundary") == bt) & pl.col("trap_load").is_not_null())["trap_load"].to_numpy()
        cuts[bt] = trap.tercile_cuts(v)
    cuts_payload = {"per_boundary": {k: {"lo_cut": v[0], "hi_cut": v[1]} for k, v in cuts.items()},
                    "band": "DESIGN", "measure": "poke_side * sum(delta_ratio_resid)"}
    cuts_payload["pin_sha256"] = hashlib.sha256(
        json.dumps(cuts_payload, sort_keys=True, default=str).encode()).hexdigest()
    (OUT / "trap_load_cuts.json").write_text(json.dumps(cuts_payload, indent=2, default=str))

    def _tier(df):
        if df.height == 0:
            return df
        rows = []
        for r in df.iter_rows(named=True):
            lc, hc = cuts.get(r["boundary"], (float("nan"), float("nan")))
            rows.append(trap.assign_tier(r["trap_load"], lc, hc))
        return df.with_columns(pl.Series("tier", rows))
    des, con = _tier(des), _tier(con)

    des.write_parquet(OUT / "trap_DESIGN.parquet")
    con.write_parquet(OUT / "trap_CONFIRM.parquet")

    # Reads per boundary type (independent), on each band. Pooled primary (L-03).
    layers = {"item": "SPDR-008", "measure": "signed trap-load (poke_side*Σ delta_ratio_resid)",
              "n_symbols_with_events": len(bars_by["DESIGN"]),
              "universe": {"a5_fitted_run": len(a5), "breadth_denominator_design_note": 296},
              "per_boundary": {}}
    layers["symbols_skipped"] = n_skip
    for bt in trap.BOUNDARY_TYPES:
        bt_layer = {}
        for band, df, bb, sb in (("DESIGN", des, bars_by["DESIGN"], sess_by["DESIGN"]),
                                 ("CONFIRM", con, bars_by["CONFIRM"], sess_by["CONFIRM"])):
            e = df.filter(pl.col("boundary") == bt)
            if e.height == 0:
                bt_layer[band] = {"n_events": 0, "UNPOWERED": True}
                continue
            t1 = t1_monotonicity(e)
            t2 = t2_tier_marginal(e)
            t3 = t3_ordinary_touch(e, ot_by[band].get(bt, {}), bb)
            t4 = t4_availability(e, bb, sb)
            tw = tripwire_path_swap(e, bb, t1, t2)
            bt_layer[band] = {
                "n_events": e.height, "n_symbols": e["symbol"].n_unique(),
                "T1_load_monotonicity": t1, "T2_tier_marginal": t2,
                "T3_unsigned_base": t3, "T4_availability": t4,
                "tripwire_path_swap": tw,
            }
        layers["per_boundary"][bt] = bt_layer

    (OUT / "layers.json").write_text(json.dumps(layers, indent=2, default=str))

    # Per-(boundary × symbol) allocation map with PER-CELL derangement null (design §4;
    # so the K=3 cluster deliverable is null-tested, not eyeballed — QA-3 finding).
    con_key = {(r["boundary"], r["symbol"]): r for r in con.select(
        "boundary", "symbol", "trap_load", "mfe_rev_norm").group_by(["boundary", "symbol"]).agg(
        pl.col("trap_load"), pl.col("mfe_rev_norm")).iter_rows(named=True)}
    amap = []
    for bt in tqdm(trap.BOUNDARY_TYPES, desc="allocation/per-cell"):
        e = des.filter(pl.col("boundary") == bt)
        for sym in e["symbol"].unique().to_list():
            se = e.filter(pl.col("symbol") == sym)
            hi = se.filter(pl.col("tier") == "HIGH")["mfe_rev_norm"]
            lo = se.filter(pl.col("tier") == "LOW")["mfe_rev_norm"]
            load, exc = se["trap_load"].to_numpy(), se["mfe_rev_norm"].to_numpy()
            n_cell_seeds = 2000 if se.height >= 20 else 0
            if n_cell_seeds:
                rho_c, null_c = _spearman_derangement_null(load, exc, n_cell_seeds, 20180901)
                p_cell = float((null_c >= rho_c).mean()) if null_c.size else None
                mde_c = float(np.quantile(null_c, 0.95)) if null_c.size else None
            else:
                rho_c, p_cell, mde_c = _spearman(load, exc), None, None
            # CONFIRM reproduction of the per-cell rho (sign agreement)
            ck = con_key.get((bt, sym))
            rho_con = (_spearman(np.array(ck["trap_load"], float), np.array(ck["mfe_rev_norm"], float))
                       if ck and len(ck["trap_load"]) >= 8 else None)
            amap.append({"boundary": bt, "symbol": sym, "n": se.height,
                         "rho": rho_c, "per_cell_p": p_cell, "mde_rho": mde_c,
                         "rho_confirm": rho_con,
                         "signed_supported_cell": bool(p_cell is not None and p_cell <= 0.05
                                                        and mde_c is not None and rho_c >= mde_c
                                                        and rho_con is not None and rho_con > 0),
                         "high_low_diff": (float(hi.mean() - lo.mean()) if hi.len() and lo.len() else None),
                         "median_mfe_rev_norm": float(se["mfe_rev_norm"].median())})
    amap_df = pl.DataFrame(amap)
    amap_df.write_parquet(OUT / "allocation_map.parquet")

    # K=3 cluster scan per boundary: >=3 symbols whose signed cell holds (p<=.05, rho>=MDE,
    # CONFIRM sign agrees). A pooled disclosure count is NOT the headline (L-03).
    k3 = {}
    for bt in trap.BOUNDARY_TYPES:
        b = amap_df.filter((pl.col("boundary") == bt) & (pl.col("n") >= 20))
        sup = b.filter(pl.col("signed_supported_cell"))
        k3[bt] = {"n_powered_cells": b.height,
                  "n_signed_supported": sup.height,
                  "cluster_K3_met": sup.height >= 3,
                  "supported_symbols": sup["symbol"].to_list()[:20],
                  "n_rho_pos_gt_010": b.filter(pl.col("rho") > 0.10).height,
                  "n_rho_neg_lt_m010": b.filter(pl.col("rho") < -0.10).height}
    layers["K3_cluster_scan"] = k3
    (OUT / "layers.json").write_text(json.dumps(layers, indent=2, default=str))
    (OUT / "floor_table.json").write_text(json.dumps(money_floor(des), indent=2, default=str))

    print(f"DONE. DESIGN traps {des.height} / CONFIRM {con.height} across {len(a5)} symbols.")
    for bt in trap.BOUNDARY_TYPES:
        d = layers["per_boundary"][bt]["DESIGN"]
        t1 = d["T1_load_monotonicity"]
        print(f"  [{bt}] DESIGN n={d['n_events']} T1 rho={t1.get('rho')} p={t1.get('one_sided_p_ge_observed')} "
              f"MDE={t1.get('mde_rho_at_n')} | K3 supported={k3[bt]['n_signed_supported']}/"
              f"{k3[bt]['n_powered_cells']} met={k3[bt]['cluster_K3_met']}")


if __name__ == "__main__":
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else None
    main(lim)
