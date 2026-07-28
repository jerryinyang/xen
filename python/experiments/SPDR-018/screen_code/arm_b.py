"""Arm B — the SPDR-013 residue (direction expectancy power deficit).

Residue inventory (design §2, complete — nothing narrowed):

  B1  ``stop``-only and ``trail``-only exit arms      degenerate n, one-tail means, all UNPOWERED
  B2  unpowered ``time``-arm cells                    MDE / date floors
  B3  the 125 positive-mean cells                     every one UNPOWERED
  B4  ZZ structural leg, per symbol                   n ~ 230-250, fat-tailed, UNPOWERED via MDE
  B5  M15 arms                                        all D-SMA and D-ZZ arms on the M15 clock

**This is where ``W`` and ``L`` are measured on real episodes** — the axis-B gap SoT §2 exposed,
and the highest-value arm for parameterising SPDR-019/020.

The object is SPDR-013's episode under its declared capture geometry, inherited verbatim: this
module re-scores the parent's own emitted episodes, it does not rebuild them. Powering comes from
levers 1-3 only (pool across symbols with sigma-normalisation; use the full TRAIN span; score
CONFIRM explicitly). No arm is added, no parameter tuned, no direction model proposed — SoT §1.2.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import cells
import parents
from config import BOOT_RESAMPLES

PANEL = "episodes.parquet"
GROSS, NET, TS, EXIT_TS = "gross_bps", "partial_net_bps", "entry_ts", "exit_ts"
KEYS = ("symbol", "clock", "band", "signal", "exit_mode")


def load_panel() -> pd.DataFrame:
    return pd.read_parquet(parents.published("SPDR-013", PANEL))


def _residue_items(row_keys: dict, positive_unpowered: set) -> str:
    """Tag every cell with the 017 open items it belongs to. A cell may carry several."""
    items = []
    em, clock, sig = row_keys["exit_mode"], row_keys["clock"], row_keys["signal"]
    if em in ("stop", "trail"):
        items.append("B1")
    if em == "time":
        items.append("B2")
    if (row_keys.get("symbol"), sig, em, clock, row_keys.get("band")) in positive_unpowered:
        items.append("B3")
    if sig == "D-ZZ" and em == parents.const("SPDR-013", "ZZ_STRUCTURAL_EXIT_MODE"):
        items.append("B4")
    if clock == "M15":
        items.append("B5")
    return ",".join(items) if items else "B-carried"


def positive_unpowered_cells() -> set:
    """The parent's own 125 positive-mean-but-unpowered cells, read off its published table."""
    p = pd.read_parquet(parents.published("SPDR-013", "expectancy_by_cell.parquet"))
    m = (p["expectancy_partial"] > 0) & (p["band_label"] == "UNPOWERED")
    sel = p.loc[m, ["symbol", "signal", "exit_mode", "clock", "band"]]
    return set(map(tuple, sel.to_numpy()))


def sigma_normalised(df: pd.DataFrame, unit_pin: dict) -> pd.DataFrame:
    """Rescale each symbol's returns to the pooled sigma so pooling across vol scales is valid.

    Lever 1. The result is still in **bps** — sigma-normalisation buys power for pooling and never
    becomes a reporting unit of its own (P-15 / L-21).
    """
    pooled = unit_pin.get("pooled_median_sigma_bps")
    per = unit_pin.get("per_symbol", {})
    if not pooled:
        return df
    scale = df["symbol"].map(
        lambda s: (pooled / per.get(s, {}).get("median_sigma_bps"))
        if per.get(s, {}).get("median_sigma_bps") else np.nan)
    out = df.copy()
    out[GROSS] = out[GROSS] * scale
    out[NET] = out[NET] * scale
    return out.loc[np.isfinite(scale.to_numpy(dtype=float))]


def tasks(unit_pin: dict) -> list[dict]:
    """Work units for the orchestrator. Splitting by SYMBOL is a pure partition of the per-symbol
    cells — no cell moves between units, so the union is identical to a sequential run."""
    syms = sorted(load_panel()["symbol"].unique().tolist())
    sigs = sorted(load_panel()["signal"].unique().tolist())
    return ([{"arm": "B", "stage": "per_symbol", "symbol": s} for s in syms]
            # the pooled stage is split by SIGNAL so its (expensive, levers-exhausted) cells
            # parallelise. Signals partition the pooled cells exactly — no cell moves.
            + [{"arm": "B", "stage": "pooled", "signal": g} for g in sigs])


def run_task(task: dict, unit_pin: dict, *, n_boot: int = BOOT_RESAMPLES) -> list[dict]:
    if task["stage"] == "per_symbol":
        return run(unit_pin, n_boot=n_boot, only_symbol=task["symbol"], pooled=False)
    return run(unit_pin, n_boot=n_boot, only_symbol=None, pooled="only",
               only_signal=task.get("signal"))


def run(unit_pin: dict, *, n_boot: int = BOOT_RESAMPLES, full_cells: set | None = None,
        only_symbol: str | None = None, pooled=True,
        only_signal: str | None = None) -> list[dict]:
    panel = load_panel()
    if only_symbol is not None:
        panel = panel[panel.symbol == only_symbol]
    pos_unp = positive_unpowered_cells()
    clock_minutes = {c: parents.const("SPDR-013", "CLOCKS")[c]["minutes"]
                     for c in panel["clock"].unique()}
    out: list[dict] = []
    if pooled == "only":
        panel_all = load_panel()
        if only_signal is not None:
            panel_all = panel_all[panel_all.signal == only_signal]
        clock_minutes = {c: parents.const("SPDR-013", "CLOCKS")[c]["minutes"]
                         for c in panel_all["clock"].unique()}
        return _pooled_cells(panel_all, unit_pin, pos_unp, clock_minutes, n_boot=n_boot)

    # ---- per-symbol cells: the parent's own grid, re-scored (parity target) ----------------
    for key, g in panel.groupby(list(KEYS), sort=True, observed=True):
        k = dict(zip(KEYS, key))
        out.append(cells.score_signed_cell(
            g, arm="B", item=_residue_items(k, pos_unp), key={**k, "basis": "per_symbol"},
            gross_col=GROSS, net_col=NET, ts_col=TS, exit_ts_col=EXIT_TS,
            h=None, clock_minutes=clock_minutes.get(k["clock"]),
            n_boot=n_boot, full=(full_cells is not None and tuple(key) in full_cells)))

    # ---- lever 2: the full TRAIN span per symbol (DESIGN + CONFIRM together) ---------------
    for key, g in panel.groupby(["symbol", "clock", "signal", "exit_mode"], sort=True,
                                observed=True):
        k = dict(zip(("symbol", "clock", "signal", "exit_mode"), key))
        out.append(cells.score_signed_cell(
            g, arm="B", item=_residue_items({**k, "band": "TRAIN"}, pos_unp),
            key={**k, "band": "TRAIN", "basis": "per_symbol_full_train"},
            gross_col=GROSS, net_col=NET, ts_col=TS, exit_ts_col=EXIT_TS,
            h=None, clock_minutes=clock_minutes.get(k["clock"]), n_boot=n_boot))

    if not pooled:
        return out
    out += _pooled_cells(panel, unit_pin, pos_unp, clock_minutes, n_boot=n_boot)
    return out


def _pooled_cells(panel, unit_pin, pos_unp, clock_minutes, *, n_boot) -> list[dict]:
    out: list[dict] = []
    normed = sigma_normalised(panel, unit_pin)
    pooled_sigma = unit_pin.get("pooled_median_sigma_bps")
    for band_name, src in (("DESIGN", panel[panel.band == "DESIGN"]),
                           ("CONFIRM", panel[panel.band == "CONFIRM"]),
                           ("TRAIN", panel)):
        for basis, frame in (("pooled_raw", src),
                             ("pooled_sigma_normalised",
                              normed.loc[normed.index.intersection(src.index)])):
            for key, g in frame.groupby(["clock", "signal", "exit_mode"], sort=True,
                                        observed=True):
                k = dict(zip(("clock", "signal", "exit_mode"), key))
                # levers 1+2+3 are all applied on the pooled full-TRAIN sigma-normalised cell:
                # if THAT is still short of target, the item is NOT_RESOLVABLE (design §5).
                exhausted = (band_name == "TRAIN" and basis == "pooled_sigma_normalised")
                out.append(cells.score_signed_cell(
                    g, arm="B", item=_residue_items({**k, "band": band_name}, pos_unp),
                    key={**k, "symbol": "__POOLED__", "band": band_name, "basis": basis},
                    gross_col=GROSS, net_col=NET, ts_col=TS, exit_ts_col=EXIT_TS,
                    h=None, clock_minutes=clock_minutes.get(k["clock"]),
                    levers_exhausted=exhausted, full=exhausted, n_boot=n_boot,
                    sigma_bps=pooled_sigma))
    return out
