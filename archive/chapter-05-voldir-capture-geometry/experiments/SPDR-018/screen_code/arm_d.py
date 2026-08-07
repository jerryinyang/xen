"""Arm D — the SPDR-015 residue (conditioner science).

Residue inventory (design §2, complete — nothing narrowed):

  D1  ``trans_up`` / ``trans_dn`` counts   n_trans < 50 — rare switches under sticky regimes
  D2  run-length MAE                       emitted as disclosure only, never powered
  D3  T-GT-MED10                           12/21 SUPPORTED -> INCONCLUSIVE
  D4  T-GT-MED5 failing cells              19/21; the 2 failures unexamined
  D5  2a H4 k=1                            6/16 SUPPORTED, median dBrier ~ +0.0002
  D6  R-HMM-RV empirical and logistic      3/15 and 7/15
  D7  D1 stickiness                        emitted disclosure-only, never scored
  D8  **the CONFIRM verify slice**         2a and 2b on CONFIRM, separately from DESIGN —
                                           NEVER SCORED; SPDR-015 §6 carried it as follow-up

D8 is the one item in SPDR-018 that cannot be answered by re-reading a parent panel: SPDR-015
masked ``is_origin`` to the DESIGN band before scoring (``run_screen.py`` builds ``feat_eval``
with ``is_origin & in_design``), so no CONFIRM origin was ever scored and none is recoverable
from ``regime_states.parquet``. Arm D therefore **re-runs SPDR-015's own modules** — the same
``build_bar_frame`` / ``add_state_models`` / ``evaluate_symbol_clock`` / ``run_zz_ordinal`` — with
the origin mask set to each band in turn. The object is untouched; only the band moves.

Arm D's object is per-origin forecast skill: a measurement object, no P&L claim, so no
``(p, W, L)`` decomposition (design §3, §4.1).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import polars as pl

import cells
import parents
from config import BOOT_RESAMPLES, CONFIRM_END, CONFIRM_START, DESIGN_END, DESIGN_START, NS

BANDS = ("DESIGN", "CONFIRM", "TRAIN")
_BOUNDS = {
    "DESIGN": (int(DESIGN_START.timestamp() * NS), int(DESIGN_END.timestamp() * NS)),
    "CONFIRM": (int(CONFIRM_START.timestamp() * NS), int(CONFIRM_END.timestamp() * NS)),
    "TRAIN": (int(DESIGN_START.timestamp() * NS), int(CONFIRM_END.timestamp() * NS)),
}


def _p15():
    return parents.load("SPDR-015")


def clocks_2a() -> tuple:
    return tuple(parents.const("SPDR-015", "CLOCKS_2A"))


def build_frames(symbol: str, *, manifest=None) -> dict:
    """SPDR-015's own feature + state frames for one symbol, over the FULL TRAIN span.

    The frame is built once over the whole fence so the walk-forward fit history is continuous
    (as the parent does); only the ORIGIN MASK is varied per band afterwards.
    """
    m = _p15()
    cat, feats = m["catalog_io"], m["features"]
    minutes = cat.load_minute_bars(symbol, DESIGN_START, CONFIRM_END, band="TRAIN",
                                   manifest=manifest)
    out: dict = {"symbol": symbol, "frames": {}, "n_minutes": int(minutes.height)}
    if minutes.height == 0:
        return out
    for clock in (*clocks_2a(), "D1"):
        bars = cat.aggregate_clock(minutes, clock)
        f = feats.build_bar_frame(bars, clock)
        if f.height == 0:
            continue
        f, _fits = feats.add_state_models(f, clock)
        out["frames"][clock] = f
    out["h1_bars"] = cat.aggregate_clock(minutes, "H1")
    return out


def _mask_band(frame: pl.DataFrame, band: str) -> pl.DataFrame:
    """Restrict SCORED ORIGINS to ``band`` while keeping the full fit history in the frame."""
    lo, hi = _BOUNDS[band]
    return frame.with_columns(
        (pl.col("is_origin") & (pl.col("slot_end") >= lo) & (pl.col("slot_end") < hi))
        .alias("is_origin"))


def run_symbol(symbol: str, *, manifest=None, n_boot: int = BOOT_RESAMPLES) -> list[dict]:
    """Every arm-D item for one symbol, on all three bands (D8 = the CONFIRM column)."""
    m = _p15()
    trans_mod = m["transitions"]
    built = build_frames(symbol, manifest=manifest)
    rows: list[dict] = []
    if not built.get("frames"):
        return [{"arm": "D", "residue_item": "D1-D8", "symbol": symbol,
                 "status": "NO_FENCED_BARS", "note": "symbol retained, never silently dropped"}]

    for clock, frame in built["frames"].items():
        if clock == "D1":
            rows += d7_stickiness(symbol, frame)
            continue
        for band in BANDS:
            fb = _mask_band(frame, band)
            mrows, trows, rrows, _drows = trans_mod.evaluate_symbol_clock(symbol, clock, fb)
            rows += _wrap_2a(symbol, clock, band, mrows, n_boot=n_boot)
            rows += _wrap_transitions(symbol, clock, band, trows)
            rows += _wrap_runlen(symbol, clock, band, rrows)
    return rows


def _band_of(ts_ns) -> str:
    lo_c, hi_c = _BOUNDS["CONFIRM"]
    return "CONFIRM" if ts_ns >= lo_c else "DESIGN"


def _wrap_2a(symbol: str, clock: str, band: str, mrows: list[dict], *, n_boot: int) -> list[dict]:
    """D5 / D6 / D8 — the 2a metric rows, tagged with the item each answers."""
    out = []
    for r in mrows:
        model = r.get("model")
        method = r.get("method")
        k = r.get("horizon_k")
        items = []
        if clock == "H4" and k == 1:
            items.append("D5")
        if model == "R-HMM-RV" and method in ("empirical_p", "logistic_ridge"):
            items.append("D6")
        if band == "CONFIRM":
            items.append("D8")
        out.append({
            "arm": "D", "residue_item": ",".join(items) if items else "D-carried",
            "symbol": symbol, "clock": clock, "band": band, "leg": "2a",
            "basis": "per_symbol", **r,
            "target_rule": "SPDR-015: n_origins >= 80 AND n_dates >= 30",
            "at_parent_target_precision": bool(
                (r.get("n_origins") or 0) >= 80 and (r.get("n_dates") or 0) >= 30),
            "never_scored_before": band == "CONFIRM",
        })
    return out


def _wrap_transitions(symbol: str, clock: str, band: str, trows: list[dict]) -> list[dict]:
    """D1 — ``trans_up`` / ``trans_dn`` counts, with the realised ``n_trans`` disclosed."""
    return [{
        "arm": "D", "residue_item": "D1" + (",D8" if band == "CONFIRM" else ""),
        "symbol": symbol, "clock": clock, "band": band, "leg": "2a-transitions",
        "basis": "per_symbol", **r,
        "min_trans_rule": 50,
        "at_parent_target_precision": bool((r.get("n_trans") or 0) >= 50),
        "shortfall_n_trans": max(0, 50 - int(r.get("n_trans") or 0)),
    } for r in trows]


def _wrap_runlen(symbol: str, clock: str, band: str, rrows: list[dict]) -> list[dict]:
    """D2 — run-length MAE, now SCORED rather than disclosed."""
    return [{
        "arm": "D", "residue_item": "D2" + (",D8" if band == "CONFIRM" else ""),
        "symbol": symbol, "clock": clock, "band": band, "leg": "2a-runlength",
        "basis": "per_symbol", **r,
    } for r in rrows]


def d7_stickiness(symbol: str, frame_d1: pl.DataFrame) -> list[dict]:
    """D7 — D1 ``P(stay)``, emitted disclosure-only by SPDR-015 and never scored.

    Computed exactly as the parent computed it (``run_screen.py`` D1 block), then scored per band
    with a proper count and a CI instead of being left as a bare number.
    """
    st = frame_d1["s_markov"].to_numpy()
    origin = frame_d1["is_origin"].to_numpy()
    se = frame_d1["slot_end"].to_numpy().astype(np.int64)
    y = np.full(st.size, -1)
    y[:-1] = st[1:]
    out = []
    for band in BANDS:
        lo, hi = _BOUNDS[band]
        m = origin & (st >= 0) & (y >= 0) & (se >= lo) & (se < hi)
        stay = (st[m] == y[m]).astype(float)
        out.append(cells.score_mean_cell(
            stay, se[m], arm="D", item="D7" + (",D8" if band == "CONFIRM" else ""),
            key={"symbol": symbol, "clock": "D1", "band": band, "leg": "2a-stickiness",
                 "model": "R-MARKOV", "metric": "p_stay", "basis": "per_symbol"},
            target_mde=0.05, supported=0.55, contradicted=0.45,
            levers_exhausted=(band == "TRAIN")))
    return out


# --------------------------------------------------------------------------- 2b
def zz_panel() -> pd.DataFrame:
    """SPDR-015's own per-swing ordinal predictions, with the band derived from confirmation."""
    df = pd.read_parquet(parents.published("SPDR-015", "zz_ordinal.parquet"))
    lo_c, _ = _BOUNDS["CONFIRM"]
    df["band"] = np.where(df["confirm_slot_end"].to_numpy(dtype=np.int64) >= lo_c,
                          "CONFIRM", "DESIGN")
    return df


def run_2b(*, n_boot: int = BOOT_RESAMPLES) -> list[dict]:
    """D3 / D4 / D8 — the ordinal targets, scored per band from the parent's own predictions.

    ``T-GT-MED10`` (D3) and ``T-GT-MED5`` (D4) were left INCONCLUSIVE at 12/21 and 19/21; the
    CONFIRM slice (D8) was never scored at all. Both are answered here by partitioning the
    parent's emitted per-swing rows — no model is refitted and no target is redefined.
    """
    df = zz_panel()
    out = []
    item_of = {"T-GT-MED10": "D3", "T-GT-MED5": "D4", "T-GT-CUR": "D-carried"}
    for band in BANDS:
        src = df if band == "TRAIN" else df[df.band == band]
        for keys, g in src.groupby(["symbol", "target", "model"], sort=True, observed=True):
            sym, tgt, mdl = keys
            item = item_of.get(tgt, "D-carried")
            if band == "CONFIRM":
                item += ",D8"
            y = g["y"].to_numpy(dtype=float)
            p = g["p"].to_numpy(dtype=float)
            ts = g["confirm_slot_end"].to_numpy(dtype=np.int64)
            base = float(np.nanmean(y)) if y.size else np.nan
            hit = ((p >= 0.5).astype(float) == y).astype(float)
            brier = (p - y) ** 2
            brier_base = (base - y) ** 2
            common = {"symbol": sym, "target": tgt, "model": mdl, "band": band, "leg": "2b",
                      "basis": "per_symbol", "base_rate": base,
                      "never_scored_before": band == "CONFIRM"}
            out.append(cells.score_mean_cell(
                hit, ts, arm="D", item=item, key={**common, "metric": "hit_rate"},
                target_mde=0.05, supported=0.55, contradicted=0.45,
                levers_exhausted=(band == "TRAIN"), n_boot=n_boot))
            out.append(cells.score_mean_cell(
                brier_base - brier, ts, arm="D", item=item,
                key={**common, "metric": "delta_brier_vs_base_rate"},
                target_mde=0.01, supported=0.01, contradicted=-0.01,
                levers_exhausted=(band == "TRAIN"), n_boot=n_boot))
        # lever 1: pooled across symbols
        for keys, g in src.groupby(["target", "model"], sort=True, observed=True):
            tgt, mdl = keys
            item = item_of.get(tgt, "D-carried") + (",D8" if band == "CONFIRM" else "")
            y = g["y"].to_numpy(dtype=float)
            p = g["p"].to_numpy(dtype=float)
            ts = g["confirm_slot_end"].to_numpy(dtype=np.int64)
            base = float(np.nanmean(y)) if y.size else np.nan
            out.append(cells.score_mean_cell(
                ((p >= 0.5).astype(float) == y).astype(float), ts, arm="D", item=item,
                key={"symbol": "__POOLED__", "target": tgt, "model": mdl, "band": band,
                     "leg": "2b", "metric": "hit_rate", "basis": "pooled_raw",
                     "base_rate": base},
                target_mde=0.05, supported=0.55, contradicted=0.45,
                levers_exhausted=(band == "TRAIN"), n_boot=n_boot))
    return out


def run(unit_pin: dict, *, symbols: list[str], manifest=None,
        n_boot: int = BOOT_RESAMPLES) -> list[dict]:
    out: list[dict] = []
    for sym in symbols:
        out += run_symbol(sym, manifest=manifest, n_boot=n_boot)
    out += run_2b(n_boot=n_boot)
    return out
