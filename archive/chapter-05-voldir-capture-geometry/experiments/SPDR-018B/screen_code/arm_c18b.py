"""Arm C on the cTrader universe — SPDR-014's residual object, rebuilt from its own engine.

The object is SPDR-014's post-event residual leg, unchanged: zone → mispricing event → residual
held from the breach entry to entry+h. Nothing is re-specified; only the bars underneath differ.
``engine.run_cell`` is the parent's own per-cell driver and is called directly, so the event
grammar, the band construction and the residual definition are the parent's, not a reimplementation.

This arm carries **C2 shock-conditioned MOMO** — the one live thread SPDR-018 left with zero
external replication, which is the main reason SPDR-018B exists.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import cells                       # SPDR-018's uniform layer, reused unchanged
import parents
import retarget
from config18b import CTRADER_SYMBOLS, COST_MODEL_PROVENANCE
from deflators import payoff_ratio_per_arm, sigma_ratio


def _cost_deflator():
    """COST scales with realised payoff, not bar noise (deflators.py)."""
    pr = payoff_ratio_per_arm()
    r = pr.get('C', {}).get('ratio')
    return r if (r is not None and r == r) else pr['_default']

GRID_KEYS = ("symbol", "source", "z", "H", "event_type", "h", "band", "clock", "policy")


def _m14():
    return parents.load("SPDR-014")


def base_keys() -> list[tuple]:
    """The parent's own registered grid (run_screen.process_symbol), inherited verbatim."""
    m = _m14()
    cfg = m["config"]
    keys = []
    for source in cfg.SOURCES:
        for z in cfg.Z_VALUES:
            for H in cfg.H_VALUES:
                for event in cfg.EVENT_TYPES:
                    for band in ("DESIGN", "CONFIRM"):
                        keys.append((source, z, H, event, band, False))
    for band in ("DESIGN", "CONFIRM"):
        keys.append(("Z-MAG", 1.5, 12, "E-TOUCH", band, True))
    return keys


def build_posts(symbol: str, manifest, *, clock: str = "H1") -> pd.DataFrame:
    """Every post-event residual row for one symbol, via the parent's own ``run_cell``."""
    m = _m14()
    pack = m["prepare"].prepare_symbol(symbol, clock, manifest)
    if pack is None:
        return pd.DataFrame()
    cfg = m["config"]
    engine = m["engine"]
    costs = m["costs"]

    rows: list[dict] = []
    for source, z, H, event, band, sens in base_keys():
        for h in cfg.H_POST:
            for policy in ("P-NONE", "P-MOMO", "P-MR"):
                if policy != "P-NONE" and not (
                        z == cfg.MONEY_Z and h == cfg.MONEY_H_POST
                        and event == cfg.MONEY_EVENT and source in cfg.MONEY_SOURCES):
                    continue          # the parent's own money subset, unchanged
                _z, _e, posts = engine.run_cell(
                    pack, source=source, z=z, H=H, event_type=event, h=h, band=band,
                    policy=policy, zmag_sens=sens)
                for r in posts:
                    r = dict(r)
                    r.update({"symbol": symbol, "clock": clock, "band": band, "source": source,
                              "z": z, "H": H, "event_type": event, "h": h, "policy": policy,
                              "zmag_sens": sens})
                    rows.append(r)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)

    # gross: r_h for the characterisation policy, the signed leg for the money policies —
    # exactly the convention SPDR-018 arm C used.
    gross = np.array(df["r_h"].to_numpy(dtype=float), copy=True)
    if "gross_bps" in df.columns:
        money = df["policy"].isin(("P-MOMO", "P-MR")).to_numpy()
        g2 = pd.to_numeric(df["gross_bps"], errors="coerce").to_numpy(dtype=float)
        gross[money & np.isfinite(g2)] = g2[money & np.isfinite(g2)]
    df["c_gross_bps"] = gross

    # net: the BORROWED crypto cost model (design §3, operator-directed). Cached per (entry, exit).
    ent = df["entry_ts"].to_numpy(dtype=np.int64)
    exi = df["exit_ts"].to_numpy(dtype=np.int64)
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
    df["c_net_bps"] = gross - cost * scale                 # headline: vol-scaled
    df["c_net_unscaled_bps"] = gross - cost                # companion: unscaled borrowed
    df["cost_model"] = "BORROWED_CRYPTO_PAYOFF_SCALED"
    df["cost_deflator"] = scale

    retarget.assert_ctrader_only(df["exit_ts"].to_numpy(), where=f"arm C {symbol}")
    return df


def score(df: pd.DataFrame, *, n_boot: int) -> list[dict]:
    """Cells + the C2..C8 conditioner splits, using SPDR-018's uniform scorer unchanged."""
    if df.empty:
        return []
    m = _m14()
    cm = int(m["config"].CLOCKS["H1"]["minutes"])
    out: list[dict] = []

    def sc(g, item, key, **kw):
        return cells.score_signed_cell(
            g, arm="C", item=item, key=key, gross_col="c_gross_bps", net_col="c_net_bps",
            ts_col="entry_ts", exit_ts_col="exit_ts",
            h=int(key["h"]) if key.get("h") is not None else None,
            clock_minutes=cm, n_boot=n_boot, **kw)

    for key, g in df.groupby(list(GRID_KEYS), sort=True, observed=True):
        out.append(sc(g, "C1", {**dict(zip(GRID_KEYS, key)), "basis": "per_symbol"}))

    pool = ("source", "z", "H", "event_type", "h", "clock", "policy")
    for band, src in (("DESIGN", df[df.band == "DESIGN"]), ("CONFIRM", df[df.band == "CONFIRM"]),
                      ("TRAIN", df)):
        for key, g in src.groupby(list(pool), sort=True, observed=True):
            out.append(sc(g, "C1", {**dict(zip(pool, key)), "symbol": "__CTRADER_POOLED__",
                                    "band": band, "basis": "pooled_raw"},
                          levers_exhausted=(band == "TRAIN")))

    # C2-C5 conditioners, INSIDE the event grammar (no un-nesting) — the C2 row is the thread
    for item, conds in (("C2", ("shock_flag",)),
                        ("C3", ("last_k_state_1", "last_k_state_2", "last_k_state_3")),
                        ("C5", ("mag_high", "shock_flag", "vol_tercile"))):
        for cond in conds:
            if cond not in df.columns:
                out.append({"arm": "C", "residue_item": item, "conditioner": cond,
                            "status": "COLUMN_ABSENT", "note": "reported, not skipped"})
                continue
            for key, g in df.groupby([*pool, cond], sort=True, observed=True):
                k = dict(zip([*pool, "conditioner_value"], key))
                out.append(sc(g, item, {**k, "conditioner": cond,
                                        "symbol": "__CTRADER_POOLED__", "band": "TRAIN",
                                        "basis": "pooled_raw"}, levers_exhausted=True))

    # C4 breach-type split; C6 dose response
    for key, g in df.groupby(["source", "z", "H", "h", "clock", "policy", "event_type"],
                             sort=True, observed=True):
        k = dict(zip(("source", "z", "H", "h", "clock", "policy", "event_type"), key))
        out.append(sc(g, "C4", {**k, "symbol": "__CTRADER_POOLED__", "band": "TRAIN",
                                "basis": "pooled_raw"}, levers_exhausted=True))
    for key, g in df.groupby(["source", "event_type", "clock", "policy", "z", "h"],
                             sort=True, observed=True):
        k = dict(zip(("source", "event_type", "clock", "policy", "z", "h"), key))
        out.append(sc(g, "C6", {**k, "symbol": "__CTRADER_POOLED__", "band": "TRAIN",
                                "basis": "dose_response"}, levers_exhausted=True))

    for r in out:
        r.setdefault("universe", "CTRADER")
        r.setdefault("cost_model", COST_MODEL_PROVENANCE["status"])
    return out


def run(*, manifest=None, n_boot: int, symbols=CTRADER_SYMBOLS) -> tuple[list[dict], pd.DataFrame]:
    man = manifest or retarget.ctrader_manifest()
    frames = []
    for s in symbols:
        d = build_posts(s, man)
        if not d.empty:
            frames.append(d)
    if not frames:
        return [], pd.DataFrame()
    panel = pd.concat(frames, ignore_index=True)
    return score(panel, n_boot=n_boot), panel
