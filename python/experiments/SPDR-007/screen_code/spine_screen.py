"""SPDR-007 — the statistical-spine screen (CF-SIGAUC-001 master gate).

TRAIN-only, causal, vectorised SPDR lane (no Nautilus; no P&L booked). Orchestrates
the reads defined in `python/experiments/SPDR-007/design.md` on the frozen INFR-018
instrument pin:

  R0  money floor (cost floor + IB-width thresholds), computed FIRST
  R1  Protection-quantile reproduction  (DESIGN estimate → CONFIRM verify)   [master gate]
  R2  target-before-invalidation race rate vs cost/gross breakeven
  R3  regime conditioning (contrast-only, normaliser-mechanic guard)
  R4  Δ-coherence stratification
  R5  matched-unconditional control (binding on every read) + side-derangement
  HARD outcome-path-swap tripwire (+ required positive-control plant)

Integrity is code-asserted: band fences (raise), frozen-hash re-verification,
freeze-before-CONFIRM ordering, causal ≤ t−1, no per-level Δ, no local accounting.
Value reads are report layers (L-32) — no `pass` field, nothing machine-dropped.

Run:  python -m spine_screen            (from python/experiments/SPDR-007/screen_code)
  or  python python/experiments/SPDR-007/screen_code/spine_screen.py

DEVIATIONS FROM design.md (raised before/at implementation; silent-deviation rule).
Two forced corrections; both STRENGTHEN the reads and neither loosens a validity check.
The operator should ratify them (pre-measurement) before the run is treated as final.

  D-1 (design §4.2) — matched control is CROSS-SESSION, not within-session.
      The design's within-session phase-matched control is infeasible by construction:
      the real event enters ≈45–55 min into the session, which is exactly the
      [poke−30, qualify_end+30] exclusion band, so a within-session draw matched to
      that phase always lands in the exclusion and is forced to a mid-session minute —
      reintroducing the horizon confound QA I-2 fixed (measured: within-session control
      remaining-horizon 723 min vs the real 1391). Phase-matching therefore REQUIRES
      other sessions. The control now draws donor SESSIONS at the event's own phase and
      side, normalised by the donor's own IB width — phase/side matched, disjoint,
      unconditional on acceptance. Direction: NEUTRAL/TIGHTER (removes the confound).

  D-2 (design §4.3 / §7) — the HARD future-destroy tripwire fires only on a MATERIAL raw
      edge (its day-clustered interval excludes zero). A future-destroy cannot adjudicate
      a leak on an edge that does not exist: with raw contrast ≈ 0 the collapse ratio is
      noise/noise and "survival" (|cf|>0.25) is meaningless. The positive-control PLANT
      still must fire (bite proven) regardless, so a toothless gate is refused. When no
      material edge exists the tripwire is reported UNPOWERED — not a leak, not a hard
      fail. This is the L-32 discipline (no auto-decide at a point of no estimator
      resolution) applied to the tripwire. Direction: NEUTRAL (a soundness precondition;
      it cannot hide a real leak — a material surviving edge still HARD-fails).
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import polars as pl
from tqdm.auto import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "python" / "src"))

from xen.estimand_validation import check_no_local_accounting  # noqa: E402
from xen.evaluation import (  # noqa: E402
    block_bootstrap_ci, block_sensitivity, bybit_round_trip_cost_bps, spread_scale_route, trimmed_mean,
)
from xen.sigbar import fences, sessions, spine  # noqa: E402
from xen.sigbar.baselines import residualise  # noqa: E402
from xen.sigbar.classes import derive_thresholds  # noqa: E402
from xen.sigbar.data_types import SPREAD_UNUSABLE  # noqa: E402

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
ROOT = Path(__file__).resolve().parents[4]
RESULTS = ROOT / "python" / "experiments" / "SPDR-007" / "results"
PLOTS = ROOT / "python" / "experiments" / "SPDR-007" / "plots"
REGISTRY_PIN = "5c3869845bd514bf"  # instrument_registry.json pin_sha256 prefix (design §0)
BASELINES_PARQUET = ROOT / "python/experiments/INFR-017/results/seasonal_baselines.parquet"

FUNDING_BPS_PER_8H = 1.0
SESSION_HOLD_HOURS = 24.0
GROSS_BREAKEVEN = 1.0 / 3.0  # R=2 → p0 = 1/(1+R)

# INFR-017 flip-pair spreads (bps, round-trip) on the 20 audited symbol-days, and
# the tick reference; max(tick, flip) per the money-floor rule (design §6.3).
AUDITED_SPREAD_BPS = {
    "BTCUSDT": max(0.0429, 0.244), "ETHUSDT": max(0.058, 0.305),
    "SOLUSDT": max(0.376, 0.727), "DOGEUSDT": max(1.477, 1.470),
    "XRPUSDT": max(1.965, 1.929),
}
DEFAULT_TICK_FLOOR_BPS = 1.0  # tick-size floor for unaudited symbols (conservative lower bound)


# --------------------------------------------------------------------------- #
# Frozen-input verification (design §0 — raise on any mismatch)
# --------------------------------------------------------------------------- #
def assert_frozen() -> dict:
    fi = fences.assert_frozen_inputs(ROOT)  # baselines + column pins + SpreadBps UNUSABLE
    reg = json.loads((ROOT / "python/experiments/INFR-018/results/instrument_registry.json").read_text())
    if not reg["pin_sha256"].startswith(REGISTRY_PIN):
        raise RuntimeError(f"registry pin mismatch: {reg['pin_sha256'][:16]} != {REGISTRY_PIN}")
    a = reg["anchor"]
    if a["anchor_id"] != spine.ANCHOR_ID or a["ib_minutes"] != spine.IB_MINUTES:
        raise RuntimeError("registry anchor != frozen spine anchor")
    if reg["a6_rule"]["disc_id"] != spine.A6_DISCRIMINATOR.disc_id:
        raise RuntimeError("registry A6 rule != frozen spine discriminator")
    return {"registry_pin": reg["pin_sha256"], "baselines_sha256": fi.baselines_sha256,
            "column_pins_sha256": fi.column_pins_sha256, "spread_status": SPREAD_UNUSABLE}


# --------------------------------------------------------------------------- #
# R0 — money floor (computed first)
# --------------------------------------------------------------------------- #
def money_floor(symbols: list[str], ibw_bps: dict[str, float]) -> dict:
    rows = {}
    for s in symbols:
        spread = AUDITED_SPREAD_BPS.get(s, DEFAULT_TICK_FLOOR_BPS)
        cost = bybit_round_trip_cost_bps(
            s, 0.0, liquidity="taker", spread_bps=spread,
            funding_bps_per_8h=FUNDING_BPS_PER_8H, hold_hours=SESSION_HOLD_HOURS, funding_coverage="OK",
        )
        floor = cost["total_bps"]
        w = ibw_bps.get(s)
        rows[s] = {
            "spread_rt_bps": spread, "spread_source": "audited" if s in AUDITED_SPREAD_BPS else "tick_floor",
            "cost_floor_bps": floor, "median_ib_width_bps": w,
            "tp1_must_exceed_ibw": (floor / w) if w else None,
            "cost_breakdown": cost,
        }
    return {"note": "cost floor computed before estimation (design §6.3 R0); "
            "TP1-vs-floor comparison follows q̂", "per_symbol": rows}


# --------------------------------------------------------------------------- #
# Per-symbol event assembly
# --------------------------------------------------------------------------- #
def bar_metrics_local(bars: pl.DataFrame, symbol: str) -> pl.DataFrame:
    bl = pl.scan_parquet(BASELINES_PARQUET).filter(pl.col("symbol") == symbol).collect()
    if bl.height == 0:
        return bars.with_columns(pl.lit(None, dtype=pl.Float64).alias("delta_ratio_resid"))
    m = bars.with_columns(
        pl.when(pl.col("Volume") > 0).then(pl.col("Delta") / pl.col("Volume")).otherwise(None).alias("delta_ratio"),
    )
    return residualise(m, bl, "delta_ratio", time_col="OpenTime")


def symbol_events(symbol: str, band: str) -> tuple[pl.DataFrame, pl.DataFrame, dict]:
    """Build the S1 event population for one symbol/band, with regime + coherence.

    Returns ``(events, sessions_table, diag)`` — the session table is returned so
    the cross-session matched control (§4.2) can draw phase-matched donor entries.
    """
    empty_sess = pl.DataFrame()
    bars = fences.load_bars(symbol, band, root=ROOT)
    base_diag = {"symbol": symbol, "n_pokes": 0, "n_accepts": 0, "n_missing_entry": 0}
    if bars.height == 0:
        return spine._empty_events(), empty_sess, base_diag
    lo, hi = bars["OpenTime"].min(), bars["OpenTime"].max()
    anch = sessions.anchor_table(spine.anchor_spec(), lo, hi)
    sess = sessions.session_breaks(bars, anch, spine.IB_MINUTES)
    if sess.height == 0:
        return spine._empty_events(), empty_sess, base_diag
    joined = sessions.attach_sessions(bars, anch, spine.IB_MINUTES)
    joined_resid = bar_metrics_local(joined, symbol)
    events, diag = spine.build_events_with_diag(joined, sess)
    if events.height:
        ev = spine.evaluate_entries(bars, events, tp1_ibw=None)
        ev = spine.regime_percentile(ev, sess)
        ev = spine.attach_coherence(ev, joined_resid)
        events = ev.with_columns(pl.lit(symbol).alias("symbol"))
    diag = {"symbol": symbol, **diag}
    return events, sess, diag


# --------------------------------------------------------------------------- #
# Day-clustered inference (thin wrappers over xen.evaluation; L-20 hardened)
# --------------------------------------------------------------------------- #
def day_clustered_ci(values: np.ndarray, *, seed: int = 0) -> dict:
    if len(values) == 0:
        return {"n": 0, "stat": None, "ci": [None, None], "ci_excludes_zero": False, "unpowered": True}
    main = block_bootstrap_ci(values, np.median, block=spine.DAY_BLOCK, seed=seed)
    trimmed = block_bootstrap_ci(values, trimmed_mean, block=spine.DAY_BLOCK, seed=seed)
    sens = block_sensitivity(values, [max(1, spine.DAY_BLOCK // 2), spine.DAY_BLOCK, spine.DAY_BLOCK * 2],
                             stat=np.median, seed=seed)
    excl = {bool(r["ci"][0] > 0 or r["ci"][1] < 0) for r in sens}
    return {**main, "ci_excludes_zero": bool(main["ci"][0] > 0 or main["ci"][1] < 0),
            "trimmed_mean_ci": trimmed["ci"],
            "block_sensitivity": [{"block_req": r["block_req"], "ci": r["ci"]} for r in sens],
            "block_fragile": len(excl) > 1}


def mde_curve(values: np.ndarray, grid: list[float], *, seed: int = 0) -> dict:
    rows, detected = [], None
    for s in grid:
        r = block_bootstrap_ci(values - float(np.median(values)) + s, np.median, block=spine.DAY_BLOCK, seed=seed)
        ok = bool(r["ci"][0] > 0)
        rows.append({"planted": s, "ci": r["ci"], "detected": ok})
        if ok and detected is None:
            detected = s
    return {"n_days": len(values), "curve": rows, "mde": detected}


def paired_day_contrast(real: pl.DataFrame, control: pl.DataFrame, col: str) -> np.ndarray:
    r = real.drop_nulls(col).group_by("day").agg(pl.col(col).median().alias("r"))
    c = control.drop_nulls(col).group_by("day").agg(pl.col(col).median().alias("c"))
    j = r.join(c, on="day", how="inner").sort("day")
    return (j["r"] - j["c"]).to_numpy()


def day_median_series(df: pl.DataFrame, col: str) -> np.ndarray:
    g = df.drop_nulls(col).group_by("day").agg(pl.col(col).median().alias("v")).sort("day")
    return g["v"].to_numpy()


# --------------------------------------------------------------------------- #
# Freeze / hash
# --------------------------------------------------------------------------- #
def _hash_obj(obj: dict) -> str:
    payload = {k: v for k, v in obj.items() if k != "pin_sha256"}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def freeze_protection(design_events: pl.DataFrame, frozen: dict) -> dict:
    """Estimate + freeze the Protection quantile (pooled + per-symbol) on DESIGN."""
    mfe = design_events["mfe_norm"].to_numpy()
    pooled = {f"p{int(p*100)}": {"q": 1 - p, "protection_ibw": spine.protection_level(mfe, p)} for p in spine.P_VALUES}
    per_symbol = {}
    for sym, g in design_events.group_by("symbol"):
        s = sym[0] if isinstance(sym, tuple) else sym
        arr = g["mfe_norm"].to_numpy()
        per_symbol[s] = {
            "n": int(np.isfinite(arr).sum()),
            **{f"p{int(p*100)}": spine.protection_level(arr, p) for p in spine.P_VALUES},
        }
    obj = {
        "item": "SPDR-007", "band": "DESIGN", "frozen_inputs": frozen,
        "rule": "Protection Level = (1-p) quantile of mfe_norm; TP1=Protection, STOP=TP1/2 (R=2)",
        "n_events": int(design_events.height), "pooled": pooled, "per_symbol": per_symbol,
        "generated_utc": datetime.utcnow().isoformat() + "Z",
    }
    obj["pin_sha256"] = _hash_obj(obj)
    (RESULTS / "protection_freeze.json").write_text(json.dumps(obj, indent=2, default=str))
    return obj


def require_freeze() -> dict:
    p = RESULTS / "protection_freeze.json"
    if not p.exists():
        raise RuntimeError("CONFIRM path invoked before protection_freeze.json exists (design §7)")
    obj = json.loads(p.read_text())
    if obj.get("pin_sha256") != _hash_obj(obj):
        raise RuntimeError("protection_freeze.json hash mismatch — freeze tampered")
    return obj


# --------------------------------------------------------------------------- #
# Integrity asserts (design §7 HARD — raise, not warn)
# --------------------------------------------------------------------------- #
def assert_hard_integrity() -> dict:
    """Fail closed on local accounting + per-level Δ ban (QA I-10)."""
    acc_screen = check_no_local_accounting(ROOT / "python/experiments/SPDR-007/screen_code")
    acc_shared = check_no_local_accounting(ROOT / "python/src/xen/sigbar")
    if not acc_screen["ok"] or not acc_shared["ok"]:
        raise RuntimeError(
            f"LOCAL ACCOUNTING BARRED: screen={acc_screen} shared={acc_shared} (design §7)"
        )
    # Contract check: volume may enter a profile kernel; signed delta may not.
    fences.assert_no_per_level_delta(pl.Series("Volume", []))
    for banned in ("Delta", "BuyVolume", "SellVolume", "signed_flow"):
        try:
            fences.assert_no_per_level_delta(pl.Series(banned, []))
        except RuntimeError:
            pass  # expected raise
        else:
            raise RuntimeError(f"assert_no_per_level_delta failed to bar {banned!r}")
    return {"check_no_local_accounting_screen": acc_screen,
            "check_no_local_accounting_sigbar": acc_shared,
            "assert_no_per_level_delta": "BARRED — volume ok, signed columns raise"}


def session_median_ibw_bps(sess_by_sym: dict[str, pl.DataFrame]) -> dict[str, float]:
    """DESIGN-session median ib_width_bps (all sessions with ib_width>0) — CONVERSION-PIN object."""
    out: dict[str, float] = {}
    for sym, sess in sess_by_sym.items():
        if sess is None or sess.height == 0 or "ib_width" not in sess.columns:
            continue
        w = sess.filter(pl.col("ib_width") > 0)
        if w.height == 0:
            continue
        bps = (1e4 * w["ib_width"] / ((w["ib_high"] + w["ib_low"]) / 2.0)).to_numpy()
        bps = bps[np.isfinite(bps)]
        if bps.size:
            out[sym] = float(np.median(bps))
    return out


def horizon_match_disclosure(events: pl.DataFrame, control: pl.DataFrame) -> dict:
    """Side-by-side remaining-horizon distributions (design §4.2) — auditable, not asserted."""
    def summary(df: pl.DataFrame) -> dict:
        if df.height == 0 or "remaining_horizon" not in df.columns:
            return {"n": 0}
        a = df["remaining_horizon"].drop_nulls().to_numpy()
        if a.size == 0:
            return {"n": 0}
        qs = np.quantile(a, [0.1, 0.5, 0.9])
        return {
            "n": int(a.size), "mean": float(np.mean(a)), "median": float(np.median(a)),
            "q10": float(qs[0]), "q50": float(qs[1]), "q90": float(qs[2]),
        }
    per_symbol = {}
    if "symbol" in events.columns:
        for sym in sorted(events["symbol"].unique().to_list()):
            per_symbol[sym] = {
                "signal": summary(events.filter(pl.col("symbol") == sym)),
                "control": summary(control.filter(pl.col("symbol") == sym)) if "symbol" in control.columns
                else summary(control),
            }
    return {"pooled": {"signal": summary(events), "control": summary(control)},
            "per_symbol": per_symbol,
            "note": "D-1 cross-session phase match; horizons should match by construction"}


def _outcome_win(df: pl.DataFrame, col: str) -> pl.DataFrame:
    """Attach is_tp (1/0/null) for day-level race contrasts."""
    return df.with_columns(
        pl.when(pl.col(col) == "TP").then(1.0)
        .when(pl.col(col) == "STOP").then(0.0)
        .otherwise(None).alias("_is_tp")
    )


def paired_day_rate_contrast(real: pl.DataFrame, control: pl.DataFrame, outcome_col: str) -> np.ndarray:
    r = _outcome_win(real, outcome_col).drop_nulls("_is_tp").group_by("day").agg(
        pl.col("_is_tp").mean().alias("r"))
    c = _outcome_win(control, outcome_col).drop_nulls("_is_tp").group_by("day").agg(
        pl.col("_is_tp").mean().alias("c"))
    j = r.join(c, on="day", how="inner").sort("day")
    return (j["r"] - j["c"]).to_numpy()


def cost_adjusted_breakeven(qhat_ibw: float, cost_floor_bps: float, ibw_bps: float) -> float | None:
    """p0ᶜ = (STOP + cost_rt) / (TP1 + STOP) in consistent units (design §5.2)."""
    if not ibw_bps or not np.isfinite(ibw_bps) or ibw_bps <= 0 or not np.isfinite(qhat_ibw):
        return None
    tp1_bps = qhat_ibw * ibw_bps
    stop_bps = spine.STOP_FRACTION * tp1_bps
    denom = tp1_bps + stop_bps
    if denom <= 0:
        return None
    return float((stop_bps + cost_floor_bps) / denom)


# --------------------------------------------------------------------------- #
# The reads
# --------------------------------------------------------------------------- #
def r1_calibration(confirm_events: pl.DataFrame, freeze: dict) -> dict:
    """R1 master gate: realised P(mfe_norm ≥ q̂) on CONFIRM vs nominal p (pooled + per-symbol)."""
    mfe = confirm_events["mfe_norm"].to_numpy()
    mfe = mfe[np.isfinite(mfe)]
    out = {"n_confirm": int(mfe.size), "pooled": {}, "per_symbol": {},
           "note": "TRAIN_INTERNAL_CONFIRMATION — not programme OOS; per-symbol uses freeze per_symbol q̂"}
    for p in spine.P_VALUES:
        qhat = freeze["pooled"][f"p{int(p*100)}"]["protection_ibw"]
        realised = float((mfe >= qhat).mean()) if mfe.size else None
        out["pooled"][f"p{int(p*100)}"] = {
            "q_hat_ibw": qhat, "nominal_p": p, "realised_hit_rate": realised,
            "calib_err": (realised - p) if realised is not None else None,
        }
    # Per-symbol: only symbols with a frozen q̂ (DESIGN-covered).
    frozen_syms = freeze.get("per_symbol") or {}
    for sym, g in confirm_events.group_by("symbol"):
        s = sym[0] if isinstance(sym, tuple) else sym
        if s not in frozen_syms:
            continue
        arr = g["mfe_norm"].drop_nulls().to_numpy()
        row = {"n": int(arr.size)}
        for p in spine.P_VALUES:
            key = f"p{int(p*100)}"
            qhat = frozen_syms[s].get(key)
            if qhat is None or not arr.size:
                row[key] = {"q_hat_ibw": qhat, "nominal_p": p, "realised_hit_rate": None, "calib_err": None}
                continue
            realised = float((arr >= qhat).mean())
            row[key] = {
                "q_hat_ibw": qhat, "nominal_p": p, "realised_hit_rate": realised,
                "calib_err": realised - p,
                "label": ("BROKEN" if abs(realised - p) > 0.10
                          else "DRIFTED" if abs(realised - p) > 0.05 else "REPRODUCES"),
            }
        out["per_symbol"][s] = row
    return out


def r2_race(events: pl.DataFrame, control: pl.DataFrame, freeze: dict, floor: dict) -> dict:
    """R2 race rate vs gross + cost-adjusted breakevens, with matched-control contrast."""
    out = {"gross_breakeven": GROSS_BREAKEVEN, "pooled": {}, "per_symbol": {}, "cost_breakeven": {}}
    for p in spine.P_VALUES:
        qhat = freeze["pooled"][f"p{int(p*100)}"]["protection_ibw"]
        sig = events.filter(pl.col(f"outcome_p{int(p*100)}").is_in(["TP", "STOP"]))
        w_sig = float((sig[f"outcome_p{int(p*100)}"] == "TP").mean()) if sig.height else None
        ctl = control.filter(pl.col(f"outcome_p{int(p*100)}").is_in(["TP", "STOP"]))
        w_ctl = float((ctl[f"outcome_p{int(p*100)}"] == "TP").mean()) if ctl.height else None
        out["pooled"][f"p{int(p*100)}"] = {
            "tp1_ibw": qhat, "w_signal": w_sig, "w_control": w_ctl,
            "n_resolved_signal": int(sig.height), "n_resolved_control": int(ctl.height),
            "w_contrast": (w_sig - w_ctl) if (w_sig is not None and w_ctl is not None) else None,
        }
    # Per-symbol cost-adjusted p0ᶜ and race rates at p70 (primary).
    p = 0.70
    qhat = freeze["pooled"]["p70"]["protection_ibw"]
    for sym, row in (floor.get("per_symbol") or {}).items():
        p0c = cost_adjusted_breakeven(qhat, row["cost_floor_bps"], row.get("median_ib_width_bps") or 0)
        g = events.filter(pl.col("symbol") == sym) if "symbol" in events.columns else events.head(0)
        c = control.filter(pl.col("symbol") == sym) if "symbol" in control.columns else control.head(0)
        sig = g.filter(pl.col("outcome_p70").is_in(["TP", "STOP"])) if g.height else g
        ctl = c.filter(pl.col("outcome_p70").is_in(["TP", "STOP"])) if c.height else c
        w_sig = float((sig["outcome_p70"] == "TP").mean()) if sig.height else None
        w_ctl = float((ctl["outcome_p70"] == "TP").mean()) if ctl.height else None
        out["per_symbol"][sym] = {
            "p0_cost": p0c, "gross_breakeven": GROSS_BREAKEVEN,
            "tp1_ibw": qhat, "w_signal": w_sig, "w_control": w_ctl,
            "w_contrast": (w_sig - w_ctl) if (w_sig is not None and w_ctl is not None) else None,
            "n_resolved_signal": int(sig.height), "n_resolved_control": int(ctl.height),
        }
        out["cost_breakeven"][sym] = p0c
    # Pooled p0ᶜ disclosure = median of per-symbol p0ᶜ on majors if present.
    p0s = [v for v in out["cost_breakeven"].values() if v is not None]
    out["pooled_p0_cost_median"] = float(np.median(p0s)) if p0s else None
    return out


def r3_regime(events: pl.DataFrame, control: pl.DataFrame) -> dict:
    """R3 regime: contrast-only ρ (signal − control) + raw-MFE disclosure (I-3 guard)."""
    def rho(df: pl.DataFrame, x: str, y: str) -> float | None:
        d = df.drop_nulls([x, y])
        if d.height < 10:
            return None
        return float(pl.DataFrame({"x": d[x], "y": d[y]}).select(pl.corr("x", "y", method="spearman")).item())
    r_sig = rho(events, "ib_width_pctl", "mfe_norm")
    r_ctl = rho(control, "ib_width_pctl", "mfe_norm") if "ib_width_pctl" in control.columns else None
    # raw MFE disclosure needs ib_width_bps; control may lack it — compute if possible.
    if "ib_width_bps" in events.columns:
        raw = events.with_columns((pl.col("mfe_norm") * pl.col("ib_width_bps")).alias("mfe_bps_disc"))
        raw_rho = rho(raw, "ib_width_pctl", "mfe_bps_disc")
    else:
        raw_rho = None
    return {
        "rho_signal_normalised": r_sig, "rho_control_normalised": r_ctl,
        "rho_contrast": (r_sig - r_ctl) if (r_sig is not None and r_ctl is not None) else None,
        "raw_mfe_disclosure_rho": raw_rho,
        "note": "binding statistic is the CONTRAST; raw signal ρ carries the normaliser mechanic (I-3)",
    }


def r4_coherence(events: pl.DataFrame, freeze: dict | None = None) -> dict:
    """R4 Δ-coherence: mfe_norm + race-rate (w) contrast, top vs bottom coherence tercile."""
    d = events.drop_nulls("coh")
    if d.height < spine.N_TERCILES * 3:
        return {"unpowered": True, "n": int(d.height)}
    lo, hi = spine.tercile_edges(d["coh"].to_numpy())
    d = d.with_columns(spine.apply_terciles(pl.col("coh"), lo, hi).alias("coh_tercile"))
    top = d.filter(pl.col("coh_tercile") == 2)
    bot = d.filter(pl.col("coh_tercile") == 0)
    out = {
        "tercile_edges": [lo, hi], "n": int(d.height),
        "mfe_norm_top_median": float(top["mfe_norm"].median()),
        "mfe_norm_bottom_median": float(bot["mfe_norm"].median()),
        "mfe_norm_contrast": float(top["mfe_norm"].median() - bot["mfe_norm"].median()),
        "n_top": int(top.height), "n_bottom": int(bot.height),
    }
    # Race-rate (w) tercile contrast at frozen p70 TP1 (QA I-4).
    if "outcome_p70" in d.columns:
        top_r = top.filter(pl.col("outcome_p70").is_in(["TP", "STOP"]))
        bot_r = bot.filter(pl.col("outcome_p70").is_in(["TP", "STOP"]))
        w_top = float((top_r["outcome_p70"] == "TP").mean()) if top_r.height else None
        w_bot = float((bot_r["outcome_p70"] == "TP").mean()) if bot_r.height else None
        out["w_top"] = w_top
        out["w_bottom"] = w_bot
        out["w_contrast"] = (w_top - w_bot) if (w_top is not None and w_bot is not None) else None
        out["n_resolved_top"] = int(top_r.height)
        out["n_resolved_bottom"] = int(bot_r.height)
    return out


def chronological_thirds_report(events: pl.DataFrame, control: pl.DataFrame, freeze: dict) -> dict:
    """L-24 F02: every key read on three chronological DESIGN thirds (report layer, not gated)."""
    if events.height == 0:
        return {"n": 0, "thirds": []}
    e = events.sort("entry_ts")
    n = e.height
    cuts = [0, n // 3, 2 * n // 3, n]
    thirds = []
    for i in range(3):
        part = e.slice(cuts[i], cuts[i + 1] - cuts[i])
        # control rows matched by day overlap approximate; use same day set for disclosure
        days = set(part["day"].to_list()) if "day" in part.columns else set()
        ctl = control.filter(pl.col("day").is_in(list(days))) if days and control.height else control.head(0)
        asym_c = paired_day_contrast(part, ctl, "asym") if ctl.height else np.array([])
        r2 = None
        if "outcome_p70" in part.columns and ctl.height:
            sc = part.filter(pl.col("outcome_p70").is_in(["TP", "STOP"]))
            cc = ctl.filter(pl.col("outcome_p70").is_in(["TP", "STOP"]))
            w_s = float((sc["outcome_p70"] == "TP").mean()) if sc.height else None
            w_c = float((cc["outcome_p70"] == "TP").mean()) if cc.height else None
            r2 = {"w_signal": w_s, "w_control": w_c,
                  "w_contrast": (w_s - w_c) if (w_s is not None and w_c is not None) else None,
                  "n_resolved_signal": int(sc.height)}
        mfe = part["mfe_norm"].drop_nulls().to_numpy()
        r1 = {}
        for p in spine.P_VALUES:
            qhat = freeze["pooled"][f"p{int(p*100)}"]["protection_ibw"]
            hit = float((mfe >= qhat).mean()) if mfe.size else None
            r1[f"p{int(p*100)}"] = {"realised_hit_rate": hit,
                                    "calib_err": (hit - p) if hit is not None else None}
        r3 = r3_regime(part, ctl) if ctl.height else {"rho_contrast": None}
        r4 = r4_coherence(part, freeze)
        thirds.append({
            "third": i + 1, "n": int(part.height),
            "entry_ts_start": str(part["entry_ts"][0]) if part.height else None,
            "entry_ts_end": str(part["entry_ts"][-1]) if part.height else None,
            "R1_self_hit": r1,
            "R2_race": r2,
            "R3_rho_contrast": r3.get("rho_contrast"),
            "R4_mfe_norm_contrast": r4.get("mfe_norm_contrast"),
            "R4_w_contrast": r4.get("w_contrast"),
            "R5_asym_contrast_median": float(np.median(asym_c)) if len(asym_c) else None,
            "R5_ci_excludes_zero": bool(day_clustered_ci(asym_c).get("ci_excludes_zero")) if len(asym_c) else False,
        })
    # Sign consistency on R5 median contrast across thirds with a value.
    signs = [np.sign(t["R5_asym_contrast_median"]) for t in thirds
             if t["R5_asym_contrast_median"] is not None and t["R5_asym_contrast_median"] != 0]
    return {
        "n_total": int(n), "thirds": thirds,
        "R5_sign_consistent": bool(len(signs) == 3 and len(set(signs)) == 1) if signs else None,
        "note": "report layer (L-24 F02); UNPOWERED cells still listed with n",
    }


def spread_scale_routing(events: pl.DataFrame, control: pl.DataFrame, floor: dict,
                         ibw_bps: dict[str, float]) -> dict:
    """§6.4 SPREAD-SCALE-ROUTING per symbol from matched-unconditional contrast × ib_width_bps."""
    out = {}
    for sym, row in (floor.get("per_symbol") or {}).items():
        g = events.filter(pl.col("symbol") == sym) if "symbol" in events.columns else events.head(0)
        c = control.filter(pl.col("symbol") == sym) if "symbol" in control.columns else control.head(0)
        if g.height == 0 or c.height == 0:
            out[sym] = {"n_signal": int(g.height), "t1_undecidable": None, "note": "no events/control"}
            continue
        # contrast in mfe_norm (signal − control median)
        sig_m = float(g["mfe_norm"].drop_nulls().median()) if g["mfe_norm"].drop_nulls().len() else 0.0
        ctl_m = float(c["mfe_norm"].drop_nulls().median()) if c["mfe_norm"].drop_nulls().len() else 0.0
        contrast_ibw = sig_m - ctl_m
        w = ibw_bps.get(sym) or row.get("median_ib_width_bps") or 0.0
        gross_bps = contrast_ibw * w
        rt_spread = row["spread_rt_bps"]
        route = spread_scale_route(gross_bps, rt_spread)
        out[sym] = {
            "contrast_mfe_norm": contrast_ibw, "median_ib_width_bps": w,
            "gross_edge_bps": gross_bps, **route,
        }
    n_und = sum(1 for v in out.values() if v.get("t1_undecidable") is True)
    return {
        "per_symbol": out,
        "n_symbols": len(out),
        "n_t1_undecidable": n_und,
        "note": "if t1_undecidable YES → AWAITING_MBP; pooled T1 disclosure-only",
    }


def adjudicate_contrast(name: str, raw_series: np.ndarray, swap_series: np.ndarray,
                        *, raw_stat: float | None = None, swap_stat: float | None = None) -> dict:
    """Material-edge + collapse for one effect-contrast (design §4.3 / AMENDMENT-4)."""
    if raw_series is not None and len(raw_series):
        raw_ci = day_clustered_ci(raw_series)
        raw_med = float(np.median(raw_series))
        material = bool(raw_ci.get("ci_excludes_zero"))
    elif raw_stat is not None and np.isfinite(raw_stat):
        raw_ci = {"ci": [None, None], "ci_excludes_zero": False, "unpowered": True}
        raw_med = float(raw_stat)
        material = False  # no day CI → cannot claim material edge
    else:
        return {"name": name, "status": "UNPOWERED", "material_edge": False, "survives": False,
                "raw_contrast": None, "swapped_contrast": None, "collapse_fraction": None}

    if swap_series is not None and len(swap_series):
        swap_ci = day_clustered_ci(swap_series)
        swap_med = float(np.median(swap_series))
    elif swap_stat is not None and np.isfinite(swap_stat):
        swap_ci = {"ci": [None, None], "ci_excludes_zero": False}
        swap_med = float(swap_stat)
    else:
        swap_ci, swap_med = {"ci": [None, None], "ci_excludes_zero": False}, None

    cf = (swap_med / raw_med) if (swap_med is not None and abs(raw_med) > 1e-9) else None
    survives = bool(
        material and cf is not None and abs(cf) > 0.25
        and raw_med * swap_med > 0 and swap_ci.get("ci_excludes_zero")
    )
    status = ("SURVIVED_HARD_FAIL" if survives
              else "NO_MATERIAL_EDGE_TRIPWIRE_UNINFORMATIVE" if not material
              else "COLLAPSED")
    return {
        "name": name, "status": status, "material_edge": material, "survives": survives,
        "raw_contrast_median": raw_med, "raw_ci": raw_ci.get("ci"),
        "raw_ci_excludes_zero": material,
        "swapped_contrast_median": swap_med, "swapped_ci": swap_ci.get("ci"),
        "collapse_fraction": cf,
    }


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def _add_race_columns(ev: pl.DataFrame, bars_by_sym: dict, freeze: dict) -> pl.DataFrame:
    """Evaluate the race per symbol at each p and attach outcome_p65/p70 columns."""
    parts = []
    for sym, g in ev.group_by("symbol"):
        s = sym[0] if isinstance(sym, tuple) else sym
        bars = bars_by_sym[s]
        gg = g
        for p in spine.P_VALUES:
            qhat = freeze["pooled"][f"p{int(p*100)}"]["protection_ibw"]
            r = spine.evaluate_entries(bars, gg.select(
                "anchor_ts", "entry_ts", "session_end", "entry", "side", "ib_width", "day"),
                tp1_ibw=qhat)
            gg = gg.join(r.select("entry_ts", pl.col("outcome").alias(f"outcome_p{int(p*100)}")),
                         on="entry_ts", how="left")
        parts.append(gg)
    return pl.concat(parts, how="diagonal_relaxed")


def run() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    PLOTS.mkdir(parents=True, exist_ok=True)

    # --- HARD integrity (design §7) — fail closed before any band work ---
    integrity = assert_hard_integrity()
    print(f"hard integrity OK — accounting clean; per-level Δ barred")

    frozen = assert_frozen()
    print(f"frozen inputs OK — registry {frozen['registry_pin'][:16]}  SpreadBps={frozen['spread_status']}")

    # --- universe (both bands) ---
    from xen.sigbar.fences import build_universe, daily_turnover, load_admitted
    admitted = load_admitted(ROOT)
    staged = sorted(p.stem for p in (ROOT / "python/experiments/INFR-011/data/staging/bars").glob("*.parquet"))

    for band in ("DESIGN", "CONFIRM"):
        per_sym = {}
        for sym in tqdm(staged, desc=f"universe {band}"):
            if sym not in admitted:
                continue
            try:
                b = fences.load_bars(sym, band, root=ROOT)
            except RuntimeError:
                raise
            except Exception:
                continue
            if b.height:
                per_sym[sym] = daily_turnover(b)
        membership = build_universe(per_sym)
        membership.write_parquet(RESULTS / f"universe_membership_{band}.parquet")
        panel = sorted(membership["symbol"].unique().to_list())
        globals()[f"_PANEL_{band}"] = panel
        print(f"{band}: {len(panel)} panel symbols")

    design_panel = globals()["_PANEL_DESIGN"]
    confirm_panel = globals()["_PANEL_CONFIRM"]

    # --- events + bars + ALL sessions (for CONVERSION-PIN session medians) ---
    d_events, diags, bars_by_sym, sess_by_sym = [], [], {}, {}
    for sym in tqdm(design_panel, desc="events DESIGN"):
        ev, sess, diag = symbol_events(sym, "DESIGN")
        diags.append(diag)
        if sess is not None and getattr(sess, "height", 0):
            sess_by_sym[sym] = sess
        if ev.height:
            d_events.append(ev)
            bars_by_sym[sym] = fences.load_bars(sym, "DESIGN", root=ROOT)
            if sym not in sess_by_sym and sess is not None:
                sess_by_sym[sym] = sess
    design_events = pl.concat(d_events, how="diagonal_relaxed")
    print(f"DESIGN events (A6 accepts): {design_events.height}")

    # CONVERSION-PIN object: DESIGN-session median ib_width_bps (all sessions, not accept-events)
    ibw_bps = session_median_ibw_bps(sess_by_sym)
    print(f"session-median ib_width_bps majors: "
          + ", ".join(f"{s}={ibw_bps[s]:.3f}" for s in
                      ("BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT") if s in ibw_bps))

    # --- R0 money floor (FIRST) ---
    floor = money_floor(sorted(ibw_bps), ibw_bps)
    floor["divisor_object"] = ("DESIGN-session median ib_width_bps (ib_width>0); "
                               "CONVERSION-PIN design §6.3 — NOT accept-event median")
    (RESULTS / "floor_table.json").write_text(json.dumps(floor, indent=2, default=str))

    # --- freeze protection quantile (DESIGN) ---
    freeze = freeze_protection(design_events, frozen)
    print(f"protection frozen: pooled p65 q̂={freeze['pooled']['p65']['protection_ibw']:.4f} "
          f"p70 q̂={freeze['pooled']['p70']['protection_ibw']:.4f}  pin {freeze['pin_sha256'][:12]}")

    # --- race columns on DESIGN signal events ---
    design_events = _add_race_columns(design_events, bars_by_sym, freeze)
    design_events.write_parquet(RESULTS / "spine_events_DESIGN.parquet")

    # --- matched control + tripwire swap (DESIGN, per symbol) ---
    qhat = freeze["pooled"]["p70"]["protection_ibw"]
    control_parts, tripwire_cov, swap_events = [], [], []
    for sym in tqdm(design_panel, desc="controls+tripwire DESIGN"):
        g = design_events.filter(pl.col("symbol") == sym)
        if g.height == 0:
            continue
        bars = bars_by_sym[sym]
        ctl = spine.matched_unconditional(bars, g, sess_by_sym[sym], qhat)
        # attach race outcomes at both p — keyed on the UNIQUE _rid, never entry_ts
        ctl = ctl.with_columns(pl.lit(sym).alias("symbol"))
        # D-1 integrity with symbol key (assert inside matched_unconditional is anchor-only)
        spine.assert_control_cross_session_disjoint(g, ctl)
        for p in spine.P_VALUES:
            q = freeze["pooled"][f"p{int(p*100)}"]["protection_ibw"]
            rr = spine.evaluate_entries(bars, ctl.select(
                "_rid", "entry_ts", "session_end", "entry", "side", "ib_width", "day"), tp1_ibw=q)
            ctl = ctl.join(rr.select("_rid", pl.col("outcome").alias(f"outcome_p{int(p*100)}")),
                           on="_rid", how="left")
        control_parts.append(ctl)
        # future-destroy swap on the spliced path; multi-p race outcomes attached
        # under high/low overrides (never re-eval on raw bars — that undoes the destroy).
        race_levels = {f"p{int(p*100)}": freeze["pooled"][f"p{int(p*100)}"]["protection_ibw"]
                       for p in spine.P_VALUES}
        sw, cov = spine.outcome_path_swap(bars, g, race_levels)
        tripwire_cov.append({"symbol": sym, **cov})
        if sw.height:
            # donor real mfe already joinable via donor_anchor_ts from the swap helper;
            # re-attach donor_mfe for the bite test if not already present.
            if "donor_mfe" not in sw.columns:
                sw = sw.join(
                    g.select(pl.col("anchor_ts").alias("donor_anchor_ts"),
                             pl.col("mfe").alias("donor_mfe"),
                             pl.col("asym").alias("donor_asym")),
                    on="donor_anchor_ts", how="left",
                )
            sw = sw.with_columns(pl.lit(sym).alias("symbol"))
            swap_events.append(sw)
    control = pl.concat(control_parts, how="diagonal_relaxed")
    control.write_parquet(RESULTS / "spine_control_DESIGN.parquet")
    swapped = pl.concat(swap_events, how="diagonal_relaxed") if swap_events else design_events.head(0)

    # --- tripwire adjudication (HARD) — R5 + R2 + R3 + R4 (design §4.3 / AMENDMENT-4) ---
    bite = spine.path_swap_bite(swapped) if swapped.height else {"corr": None, "n": 0, "bite": False}

    # R5 excursion contrast (primary day-clustered)
    r5_raw = paired_day_contrast(design_events, control, "asym")
    r5_sw = paired_day_contrast(swapped, control, "asym") if swapped.height else np.array([])
    adj_r5 = adjudicate_contrast("R5_excursion_asym", r5_raw, r5_sw)

    # R2 race-rate contrast at p70
    r2_raw = paired_day_rate_contrast(design_events, control, "outcome_p70")
    r2_sw = (paired_day_rate_contrast(swapped, control, "outcome_p70")
             if swapped.height and "outcome_p70" in swapped.columns else np.array([]))
    adj_r2 = adjudicate_contrast("R2_race_w", r2_raw, r2_sw)

    # R3 ρ contrast (global statistic; day CI not available → material_edge false unless series)
    r3_raw_obj = r3_regime(design_events, control)
    r3_sw_obj = r3_regime(swapped, control) if swapped.height else {"rho_contrast": None}
    adj_r3 = adjudicate_contrast(
        "R3_rho_contrast", np.array([]), np.array([]),
        raw_stat=r3_raw_obj.get("rho_contrast"), swap_stat=r3_sw_obj.get("rho_contrast"),
    )
    # Attach the raw levels for disclosure even when UNPOWERED for HARD
    adj_r3["rho_signal_control_raw"] = r3_raw_obj
    adj_r3["rho_signal_control_swapped"] = {k: r3_sw_obj.get(k) for k in
                                            ("rho_signal_normalised", "rho_control_normalised", "rho_contrast")}

    # R4 tercile mfe + w contrasts
    r4_raw_obj = r4_coherence(design_events, freeze)
    r4_sw_obj = r4_coherence(swapped, freeze) if swapped.height and "coh" in swapped.columns else {"mfe_norm_contrast": None, "w_contrast": None}
    adj_r4 = adjudicate_contrast(
        "R4_coherence_mfe", np.array([]), np.array([]),
        raw_stat=r4_raw_obj.get("mfe_norm_contrast"), swap_stat=r4_sw_obj.get("mfe_norm_contrast"),
    )
    adj_r4_w = adjudicate_contrast(
        "R4_coherence_w", np.array([]), np.array([]),
        raw_stat=r4_raw_obj.get("w_contrast"), swap_stat=r4_sw_obj.get("w_contrast"),
    )

    per_read = {"R5": adj_r5, "R2": adj_r2, "R3": adj_r3, "R4_mfe": adj_r4, "R4_w": adj_r4_w}
    survives = any(bool(v.get("survives")) for v in per_read.values())
    any_material = any(bool(v.get("material_edge")) for v in per_read.values())
    status = ("SURVIVED_HARD_FAIL" if survives
              else "NO_MATERIAL_EDGE_TRIPWIRE_UNINFORMATIVE" if not any_material
              else "COLLAPSED")
    plant_ok = bool(bite.get("bite"))
    tripwire = {
        "class": "future_destroy (HARD)", "status": status,
        "survives": survives, "any_material_edge": any_material,
        "per_read": per_read,
        # keep top-level R5 fields for backward compatibility with screen.md / plots
        "raw_excursion_contrast_median": adj_r5.get("raw_contrast_median"),
        "raw_ci": adj_r5.get("raw_ci"),
        "raw_ci_excludes_zero": adj_r5.get("raw_ci_excludes_zero"),
        "swapped_excursion_contrast_median": adj_r5.get("swapped_contrast_median"),
        "swapped_ci": adj_r5.get("swapped_ci"),
        "collapse_fraction": adj_r5.get("collapse_fraction"),
        "positive_control_bite": bite,
        "coverage": tripwire_cov,
        "threshold": ("|cf|>0.25 same-sign AND raw+swapped CIs exclude zero on ANY adjudicated "
                      "material contrast (R2/R3/R4/R5); R1 excluded by freeze-order (design §4.3)"),
        "deviation_D2": ("HARD fires only on material raw edge; no-material → UNINFORMATIVE, "
                         "not a hard fail (operator-ratified 2026-07-21)"),
    }
    (RESULTS / "tripwire.json").write_text(json.dumps(tripwire, indent=2, default=str))
    if survives:
        raise RuntimeError("TRIPWIRE SURVIVED: a MATERIAL effect-contrast persisted under the "
                           "outcome-path-swap — EMISSION INVALID, fix the construction (design §7). "
                           "NOT a 'no effect' read.")
    if not plant_ok:
        raise RuntimeError("POSITIVE CONTROL FAILED: the swap did not install the donor outcome "
                           f"(bite corr={bite.get('corr')}) — the tripwire has no teeth (design §4.3).")
    print(f"tripwire: {status}  R5_raw_med={adj_r5.get('raw_contrast_median')}  "
          f"any_material={any_material}  bite_corr={bite.get('corr')}")

    # --- side derangement control ---
    deranged, derange_cov = spine.derange_within_day(design_events, "side")
    if deranged.height:
        drparts = []
        for sym, g in deranged.group_by("symbol"):
            s = sym[0] if isinstance(sym, tuple) else sym
            q = freeze["pooled"]["p70"]["protection_ibw"]
            r = spine.evaluate_entries(bars_by_sym[s], g.select(
                "anchor_ts", "entry_ts", "session_end", "entry", "side", "ib_width", "day"), tp1_ibw=q)
            drparts.append(r.with_columns(pl.lit(s).alias("symbol")))
        deranged_eval = pl.concat(drparts, how="diagonal_relaxed")
    else:
        deranged_eval = design_events.head(0)

    # --- CONFIRM (only after freeze) — R1 master gate ---
    freeze = require_freeze()
    c_events = []
    for sym in tqdm(confirm_panel, desc="events CONFIRM"):
        ev, _, _ = symbol_events(sym, "CONFIRM")
        if ev.height:
            c_events.append(ev)
    confirm_events = pl.concat(c_events, how="diagonal_relaxed")
    confirm_events.write_parquet(RESULTS / "spine_events_CONFIRM.parquet")
    print(f"CONFIRM events: {confirm_events.height}")

    # --- assemble reads / layers ---
    r1 = r1_calibration(confirm_events, freeze)
    r2 = r2_race(design_events, control, freeze, floor)
    r3 = r3_regime(design_events, control)
    r4 = r4_coherence(design_events, freeze)
    horizon = horizon_match_disclosure(design_events, control)
    thirds = chronological_thirds_report(design_events, control, freeze)
    routing = spread_scale_routing(design_events, control, floor, ibw_bps)

    # day-clustered CI on primary R5 excursion contrast + MDE curve
    contrast_series = r5_raw
    r5_ci = day_clustered_ci(contrast_series)
    r5_mde = mde_curve(contrast_series, [0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 0.75, 1.0])

    # R2 MDE plant in w-contrast units (AMENDMENT-9 / QA I-12)
    r2_series = r2_raw
    r2_mde = mde_curve(r2_series, [0.005, 0.01, 0.02, 0.03, 0.05, 0.08, 0.10, 0.15, 0.20]) if len(r2_series) else {
        "n_days": 0, "curve": [], "mde": None}
    r2_ci = day_clustered_ci(r2_series) if len(r2_series) else {"n": 0, "ci": [None, None]}

    # side-derangement collapse fraction on asym
    der_asym = float(day_median_series(deranged_eval, "asym").mean()) if deranged_eval.height else None
    sig_asym = float(day_median_series(design_events, "asym").mean())
    side_cf = (der_asym / sig_asym) if (der_asym is not None and abs(sig_asym) > 1e-9) else None

    layers = {
        "item": "SPDR-007", "family": "CF-SIGAUC-001", "lane": "SPDR (TRAIN-only)",
        "frozen_inputs": frozen, "protection_freeze_pin": freeze["pin_sha256"],
        "counted_reads": 0, "test_touched": False, "holdout_touched": False,
        "hard_integrity": integrity,
        "R0_money_floor": floor,
        "R1_calibration_master_gate": r1,
        "R2_race": {**r2, "day_clustered_w_contrast_ci": r2_ci, "mde_curve_w_units": r2_mde},
        "R3_regime": r3,
        "R4_coherence": r4,
        "R5_matched_control": {
            "primary_excursion_contrast_day_clustered_ci": r5_ci,
            "mde_curve": r5_mde,
            "raw_signal_asym_day_median_mean": sig_asym,
            "control_asym_day_median_mean": float(day_median_series(control, "asym").mean()),
            "collapse_fraction_asym": (float(day_median_series(control, "asym").mean()) / sig_asym)
            if abs(sig_asym) > 1e-9 else None,
            "horizon_match_disclosure": horizon,
        },
        "side_derangement": {**derange_cov, "collapse_fraction_asym": side_cf},
        "tripwire": {k: v for k, v in tripwire.items() if k != "coverage"},
        "time_stability_thirds": thirds,
        "spread_scale_routing": routing,
        "population": {
            "design_events_evaluable": int(design_events.height),
            "confirm_events_evaluable": int(confirm_events.height),
            "design_panel_symbols": len(design_panel),
            "confirm_panel_symbols": len(confirm_panel),
            "note": "evaluable spine = says_accept minus missing entry bars",
        },
        "interpretation": "value reads are report layers (L-32); no pass field; operator judges. "
                          "CONFIRM is TRAIN-INTERNAL, not programme OOS.",
        "generated_utc": datetime.utcnow().isoformat() + "Z",
    }
    (RESULTS / "layers.json").write_text(json.dumps(layers, indent=2, default=str))

    # diagnostics / power
    pl.DataFrame(diags).write_parquet(RESULTS / "event_diagnostics_DESIGN.parquet")
    print("DONE — layers.json + freezes + per-event parquets written to results/")
    print(f"R1 p70 calib_err (pooled): {r1['pooled']['p70']['calib_err']:+.4f} "
          f"(realised {r1['pooled']['p70']['realised_hit_rate']:.3f} vs 0.70)")
    sol = (r1.get("per_symbol") or {}).get("SOLUSDT", {}).get("p70", {})
    if sol:
        print(f"R1 SOL p70 calib_err: {sol.get('calib_err')} label={sol.get('label')}")
    print(f"R2 p70 w_contrast: {r2['pooled']['p70'].get('w_contrast')}  "
          f"pooled_p0_cost_median: {r2.get('pooled_p0_cost_median')}  MDE_w={r2_mde.get('mde')}")
    print(f"R4 w_contrast: {r4.get('w_contrast')}  mfe_contrast: {r4.get('mfe_norm_contrast')}")
    print(f"R5 excursion-contrast CI: {r5_ci['ci']}  excludes_zero={r5_ci['ci_excludes_zero']}  MDE={r5_mde['mde']}")
    print(f"horizon signal/control median: "
          f"{horizon['pooled']['signal'].get('median')}/{horizon['pooled']['control'].get('median')}")
    print(f"spread-scale t1_undecidable: {routing['n_t1_undecidable']}/{routing['n_symbols']}")
    print(f"tripwire {tripwire['status']}  bite_corr={tripwire['positive_control_bite'].get('corr')}")


if __name__ == "__main__":
    run()
