"""Arms A and B on the cTrader universe, rebuilt from the parents' own modules.

Arm A — SPDR-012's ``pipeline.prepare_cell`` produces the same per-origin frame the parent scored
(features, walk-forward forecasts, causal HMM states, regime split). It is reshaped into the
panel layout SPDR-018's arm-A scorers already consume, so the scoring code is reused unchanged.

Arm B — SPDR-013's ``capture.simulate_signal`` is the parent's own episode engine, run under
**all five exit modes** ({combined, stop, trail, time, signalflip}). SPDR-018's cTrader read
covered ``signalflip`` only; that gap is closed here, which is what makes the `W/L` movability
evidence testable on a second universe.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import polars as pl

import arm_a                       # SPDR-018 scorers, reused unchanged
import cells
import parents
import retarget
from config18b import CTRADER_SYMBOLS
from deflators import payoff_ratio_per_arm, sigma_ratio


def _cost_deflator():
    """COST scales with realised payoff, not bar noise (deflators.py)."""
    pr = payoff_ratio_per_arm()
    r = pr.get('B', {}).get('ratio')
    return r if (r is not None and r == r) else pr['_default']


# ------------------------------------------------------------------------ arm A
def build_panel_a(symbol: str, manifest, clocks=("H1", "H4", "D1")) -> pd.DataFrame:
    """SPDR-012's own prepared cells, reshaped into the arm-A panel layout."""
    m = parents.load("SPDR-012")
    frames = []
    for clock in clocks:
        try:
            cell = m["pipeline"].prepare_cell(symbol, clock, manifest)
        except Exception as e:                                    # noqa: BLE001
            frames.append(pd.DataFrame([{"symbol": symbol, "clock": clock,
                                         "status": f"PREPARE_FAILED: {e!r}"}]))
            continue
        for band, fr in (("DESIGN", cell.design), ("CONFIRM", cell.confirm)):
            if fr is None or fr.height == 0:
                continue
            d = fr.to_pandas() if isinstance(fr, pl.DataFrame) else fr
            d = d.assign(symbol=symbol, clock=clock, band=band)
            frames.append(d)
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    if "slot_start" in out.columns:
        retarget.assert_ctrader_only(out["slot_start"].to_numpy(), where=f"arm A {symbol}")
    return out


def score_a(panel: pd.DataFrame, *, n_boot: int) -> list[dict]:
    """Reuse SPDR-018's arm-A scorers verbatim — A1, A2, A3, A4, A5."""
    if panel.empty or "target_abs_oo" not in panel.columns:
        return [{"arm": "A", "residue_item": "A1-A5", "universe": "CTRADER",
                 "status": "NO_PANEL", "note": "reported, not skipped"}]
    out: list[dict] = []
    for fn in (arm_a.a1_hmm, arm_a.a2_tail, arm_a.a3_design_deficit, arm_a.a4_vclock):
        try:
            out += fn(panel, n_boot=n_boot)
        except Exception as e:                                    # noqa: BLE001
            out.append({"arm": "A", "residue_item": fn.__name__, "universe": "CTRADER",
                        "status": f"SCORER_FAILED: {e!r}"})
    try:
        out += arm_a.a5_thirds(panel)
    except Exception as e:                                        # noqa: BLE001
        out.append({"arm": "A", "residue_item": "A5", "universe": "CTRADER",
                    "status": f"SCORER_FAILED: {e!r}"})
    for r in out:
        r.setdefault("universe", "CTRADER")
    return out


# ------------------------------------------------------------------------ arm B
def build_episodes_b(symbol: str, manifest, clocks=("H1", "M15"), *,
                     start=None, end=None, design_end_ns=None) -> pd.DataFrame:
    """SPDR-013's episode object under ALL FIVE exit modes.

    ``start`` / ``end`` / ``design_end_ns`` default to the cTrader span but are parameters so the
    design §5 cross-universe guard can drive the SAME code path over the BYBIT span — which is the
    whole point of that check.
    """
    m = parents.load("SPDR-013")
    cfg = m["config"]
    cat, ind, arms_mod, cap_mod = m["catalog_io"], m["indicators"], m["arms"], m["capture"]
    from config18b import (CTRADER_CONFIRM_END, CTRADER_DESIGN_END_NS as _CT_DE,
                           CTRADER_DESIGN_START)
    start = start or CTRADER_DESIGN_START
    end = end or CTRADER_CONFIRM_END
    design_end_ns = _CT_DE if design_end_ns is None else design_end_ns
    rs_mod = m["run_screen"]
    rs_mod.DESIGN_START, rs_mod.CONFIRM_END = start, end
    from datetime import timezone as _tz, datetime as _dt
    band_mid = _dt.fromtimestamp(design_end_ns / 1e9, tz=_tz.utc)
    rows: list[dict] = []

    # Use SPDR-013's OWN prepare_clock rather than reimplementing bar prep. An earlier
    # reimplementation set the ZigZag start to ATR_PERIOD+1 where the parent uses the first index
    # with a finite ATR — a different object, which the design §5 guard duly caught.
    rs = m["run_screen"]
    bands = {"DESIGN": (start, band_mid), "CONFIRM": (band_mid, end)}
    for clock in clocks:
        prep = rs.prepare_clock(symbol, clock, manifest)
        if prep is None:
            continue
        ss_full = prep["slot_start"]
        cap = cfg.CLOCKS[clock]["time_cap_bars"]
        # SPDR-013's OWN band construction (run_screen.py): for each band take every bar up to the
        # band END — preserving indicator warm-up continuity — and zero the signal BEFORE the band
        # START, so trading is confined to the band while history is not truncated. Running once
        # over the full span and splitting by timestamp afterwards yields a DIFFERENT episode set;
        # the design §5 guard caught exactly that.
        for band, (blo_dt, bhi_dt) in bands.items():
            blo = int(blo_dt.timestamp() * 1e9)
            bhi = int(bhi_dt.timestamp() * 1e9)
            nsub = int((ss_full < bhi).sum())
            if nsub <= prep["start"] + 5:
                continue
            sl = slice(0, nsub)
            ss = ss_full[sl]
            op, hi, lo, at = (prep["open"][sl], prep["high"][sl], prep["low"][sl],
                              prep["atr"][sl])
            for name, sig_full in prep["signals"].items():
                sig = sig_full[:nsub].copy()
                sig[ss < blo] = 0.0
                for em, spec in cfg.EXIT_MODES.items():
                    eps = cap_mod.simulate_signal(
                        ss, op, hi, lo, at, sig, cap, prep["start"],
                        use_stop=spec["use_stop"], use_trail=spec["use_trail"],
                        use_time=spec["use_time"], use_signalflip=spec["use_signalflip"])
                    for e in eps:
                        e = dict(e)
                        e.update({"symbol": symbol, "clock": clock, "signal": name,
                                  "exit_mode": em, "band": band})
                        rows.append(e)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)

    # BORROWED crypto cost model (design §3, operator-directed)
    costs = parents.load("SPDR-014")["costs"]
    ent = df["entry_ts"].to_numpy(dtype=np.int64)
    exi = df["exit_ts"].to_numpy(dtype=np.int64)
    g = df["gross_bps"].to_numpy(dtype=float)
    cache: dict[tuple[int, int], float] = {}
    cost = np.empty(len(df))
    for i in range(len(df)):
        k = (int(ent[i]), int(exi[i]))
        if k not in cache:
            cache[k] = -costs.partial_net(0.0, k[0], k[1])["partial_net_bps"]   # positive cost
        cost[i] = cache[k]
    scale = _cost_deflator()
    df["cost_raw_bps"] = cost
    df["cost_bps_vol_scaled"] = cost * scale
    df["c_net_bps"] = g - cost * scale                     # headline: vol-scaled
    df["c_net_unscaled_bps"] = g - cost                    # companion: unscaled borrowed
    df["cost_model"] = "BORROWED_CRYPTO_PAYOFF_SCALED"
    df["cost_deflator"] = scale

    if design_end_ns == _CT_DE:                      # only fence-assert the cTrader path
        retarget.assert_ctrader_only(exi, where=f"arm B {symbol}")
    return df


def score_b(df: pd.DataFrame, *, n_boot: int) -> list[dict]:
    if df.empty:
        return []
    m = parents.load("SPDR-013")
    cm = {c: m["config"].CLOCKS[c]["minutes"] for c in df["clock"].unique()}
    zz_mode = m["config"].ZZ_STRUCTURAL_EXIT_MODE
    out: list[dict] = []

    def item_of(sig, em, clock):
        it = []
        if em in ("stop", "trail"):
            it.append("B1")
        if em == "time":
            it.append("B2")
        if sig == "D-ZZ" and em == zz_mode:
            it.append("B4")
        if clock == "M15":
            it.append("B5")
        return ",".join(it) if it else "B-carried"

    keys = ("symbol", "clock", "band", "signal", "exit_mode")
    for key, g in df.groupby(list(keys), sort=True, observed=True):
        k = dict(zip(keys, key))
        out.append(cells.score_signed_cell(
            g, arm="B", item=item_of(k["signal"], k["exit_mode"], k["clock"]),
            key={**k, "basis": "per_symbol"}, gross_col="gross_bps", net_col="c_net_bps",
            ts_col="entry_ts", exit_ts_col="exit_ts", h=None,
            clock_minutes=cm.get(k["clock"]), n_boot=n_boot))

    for band, src in (("DESIGN", df[df.band == "DESIGN"]), ("CONFIRM", df[df.band == "CONFIRM"]),
                      ("TRAIN", df)):
        for key, g in src.groupby(["clock", "signal", "exit_mode"], sort=True, observed=True):
            k = dict(zip(("clock", "signal", "exit_mode"), key))
            out.append(cells.score_signed_cell(
                g, arm="B", item=item_of(k["signal"], k["exit_mode"], k["clock"]),
                key={**k, "symbol": "__CTRADER_POOLED__", "band": band, "basis": "pooled_raw"},
                gross_col="gross_bps", net_col="c_net_bps", ts_col="entry_ts",
                exit_ts_col="exit_ts", h=None, clock_minutes=cm.get(k["clock"]),
                levers_exhausted=(band == "TRAIN"), n_boot=n_boot))
    for r in out:
        r.setdefault("universe", "CTRADER")
        r.setdefault("cost_model", "BORROWED_CRYPTO_VOL_SCALED")
    return out


def run(*, manifest=None, n_boot: int, symbols=CTRADER_SYMBOLS) -> dict:
    man = manifest or retarget.ctrader_manifest()
    retarget.rebind("SPDR-012")
    a_panels, a_rows = [], []
    for s in symbols:
        p = build_panel_a(s, man)
        if not p.empty:
            a_panels.append(p)
    panel_a = pd.concat(a_panels, ignore_index=True) if a_panels else pd.DataFrame()
    a_rows = score_a(panel_a, n_boot=n_boot)

    retarget.rebind("SPDR-013")
    b_frames = []
    for s in symbols:
        d = build_episodes_b(s, man)
        if not d.empty:
            b_frames.append(d)
    panel_b = pd.concat(b_frames, ignore_index=True) if b_frames else pd.DataFrame()
    b_rows = score_b(panel_b, n_boot=n_boot)
    return {"A_rows": a_rows, "A_panel": panel_a, "B_rows": b_rows, "B_panel": panel_b}
