"""Arm A — the SPDR-012 residue (volatility characterisation power deficit).

Residue inventory (design §2, complete — nothing narrowed):

  A1  V-REGIME-HMM               2-state Gaussian HMM, causal forward filtering; 76/83 UNPOWERED
  A2  V-TAIL at D1               HIGH-LOW exceedance of the unconditional P90/P95 threshold
  A3  DESIGN-band deficit        V-LEVEL / V-REGIME / V-XS at median 99-102 dates vs the ~225
                                 the parent's own §6.3 rule demands
  A4  V-CLOCK at D1              session + day-of-week dummies as incremental OOS R^2 over V-LEVEL
  A5  §6.4 unsatisfiability      sign-stability in >=2 of 3 DESIGN thirds; 42/45 cells have only
                                 one powered third and the first third precedes the catalog

Arm A's object is a MEASUREMENT object — next-horizon ``|move|`` / state-conditional magnitude,
with no P&L claim, exactly as SPDR-012 registered it. It therefore carries **no** ``(p, W, L)``
decomposition: §4.1 applies that to cells carrying a signed return, and this arm has none.

A3 and A5 are PREDECLARED likely-``NOT_RESOLVABLE`` on the DESIGN band (design §9): the catalog
history cap predates most of that band, so "this band cannot support the claim" is the answer,
and it is not a negative (B-5).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import cells
import parents
from config import BOOT_RESAMPLES

TS = "slot_start"
TARGET = "target_abs_oo"


def load_panel() -> pd.DataFrame:
    return pd.read_parquet(parents.published("SPDR-012", "vol_reliability.parquet"))


def load_xs() -> pd.DataFrame:
    return pd.read_parquet(parents.published("SPDR-012", "xs_panel.parquet"))


def _bands(df: pd.DataFrame):
    """DESIGN, CONFIRM and the full TRAIN span (lever 2) — CONFIRM scored explicitly (lever 3)."""
    yield "DESIGN", df[df.band == "DESIGN"]
    yield "CONFIRM", df[df.band == "CONFIRM"]
    yield "TRAIN", df


def _oos(df: pd.DataFrame) -> pd.DataFrame:
    """Out-of-sample origins — the protocol the parent uses for its FORECAST-SKILL legs.

    SPDR-012 applies the walk-forward OOS split to the model legs (V-LEVEL / V-PERSIST /
    V-MEASURE / V-CLOCK / V-XS), because those score a prediction. The STATE legs (V-REGIME,
    V-REGIME-HMM, V-TAIL) score a causally-labelled state against a realised magnitude — there is
    no fitted predictor to hold out, so the parent scores them on every eligible row. Parent
    parity confirms this split: the V-REGIME gap reproduces to 4.5e-13 on all rows and diverges
    by up to 274 bps on the OOS subset. The distinction is inherited, not invented.
    """
    return df[df["oos"].fillna(False).astype(bool)]


def _state_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Every eligible row — the population the parent's STATE legs are scored on (see ``_oos``)."""
    return df


def run(unit_pin: dict, *, n_boot: int = BOOT_RESAMPLES) -> list[dict]:
    panel = load_panel()
    out: list[dict] = []
    out += a1_hmm(panel, n_boot=n_boot)
    out += a2_tail(panel, n_boot=n_boot)
    out += a3_design_deficit(panel, n_boot=n_boot)
    out += a4_vclock(panel, n_boot=n_boot)
    out += a5_thirds(panel)
    out += a3_xs(load_xs(), n_boot=n_boot)
    return out


# --------------------------------------------------------------------------- A1
def a1_hmm(panel: pd.DataFrame, *, n_boot: int) -> list[dict]:
    """A1 — state-conditional magnitude separation under the causal forward-filtered HMM.

    ``hmm_state`` is the parent's own emitted causal state (-1 / NaN = not yet identified during
    warm-up); those rows are excluded from the state contrast and counted, never re-labelled.
    """
    out = []
    df = _state_rows(panel)
    df = df[np.isfinite(df["hmm_state"].to_numpy(dtype=float))]
    df = df[df["hmm_state"] >= 0]
    for band, src in _bands(df):
        for key, g in src.groupby(["symbol", "clock"], sort=True, observed=True):
            out.append(cells.score_gap_cell(
                g[TARGET].to_numpy(), (g["hmm_state"].to_numpy(dtype=float) == 1),
                g[TS].to_numpy(), arm="A", item="A1",
                key={"symbol": key[0], "clock": key[1], "band": band, "arm_name": "V-REGIME-HMM",
                     "metric": "gap_high_low_bps", "basis": "per_symbol"},
                n_boot=n_boot))
        # lever 1: pooled across symbols (the state label is scale-free, so the gap pools in bps
        # only after sigma-normalisation — emitted as the sigma-normalised companion)
        for key, g in src.groupby(["clock"], sort=True, observed=True):
            out.append(cells.score_gap_cell(
                g[TARGET].to_numpy(), (g["hmm_state"].to_numpy(dtype=float) == 1),
                g[TS].to_numpy(), arm="A", item="A1",
                key={"symbol": "__POOLED__", "clock": key[0] if isinstance(key, tuple) else key,
                     "band": band, "arm_name": "V-REGIME-HMM", "metric": "gap_high_low_bps",
                     "basis": "pooled_raw", "_symbols": g["symbol"].to_numpy()},
                levers_exhausted=(band == "TRAIN"), n_boot=n_boot))
    return out


# --------------------------------------------------------------------------- A2
def a2_tail(panel: pd.DataFrame, *, n_boot: int) -> list[dict]:
    """A2 — V-TAIL: HIGH-LOW exceedance of the UNCONDITIONAL P90 / P95 threshold.

    The threshold is the cell's own unconditional quantile of ``|oo|`` (the parent's definition);
    the read is the difference in exceedance RATE between the HIGH and LOW states. D1 is the
    open item, so D1 is scored first and H1/H4 are co-reported.
    """
    out = []
    df = _state_rows(panel)
    df = df[df["regime_state"].notna()]
    for band, src in _bands(df):
        for q in (90, 95):
            for key, g in src.groupby(["symbol", "clock"], sort=True, observed=True):
                v = g[TARGET].to_numpy(dtype=float)
                v = v[np.isfinite(v)]
                if v.size == 0:
                    continue
                thr = float(np.percentile(v, q))
                gg = g[np.isfinite(g[TARGET].to_numpy(dtype=float))]
                exceed = (gg[TARGET].to_numpy(dtype=float) > thr).astype(float)
                out.append(cells.score_gap_cell(
                    exceed, (gg["regime_state"].to_numpy(dtype=float) == 1),
                    gg[TS].to_numpy(), arm="A", item="A2",
                    key={"symbol": key[0], "clock": key[1], "band": band, "arm_name": "V-TAIL",
                         "metric": f"exceed_diff_p{q}", "threshold_bps": thr,
                         "threshold_definition": f"unconditional P{q} of |oo| within the cell",
                         "basis": "per_symbol", "is_d1_open_item": key[1] == "D1"},
                    n_boot=n_boot))
            for clock, g in src.groupby("clock", sort=True, observed=True):
                v = g[TARGET].to_numpy(dtype=float)
                v = v[np.isfinite(v)]
                if v.size == 0:
                    continue
                thr = float(np.percentile(v, q))
                gg = g[np.isfinite(g[TARGET].to_numpy(dtype=float))]
                out.append(cells.score_gap_cell(
                    (gg[TARGET].to_numpy(dtype=float) > thr).astype(float),
                    (gg["regime_state"].to_numpy(dtype=float) == 1),
                    gg[TS].to_numpy(), arm="A", item="A2",
                    key={"symbol": "__POOLED__", "clock": clock, "band": band,
                         "arm_name": "V-TAIL", "metric": f"exceed_diff_p{q}",
                         "threshold_bps": thr, "basis": "pooled_raw",
                         "is_d1_open_item": clock == "D1",
                         "_symbols": gg["symbol"].to_numpy()},
                    levers_exhausted=(band == "TRAIN"), n_boot=n_boot))
    return out


# --------------------------------------------------------------------------- A3
def a3_design_deficit(panel: pd.DataFrame, *, n_boot: int) -> list[dict]:
    """A3 — the DESIGN-band power deficit across V-LEVEL and V-REGIME.

    Every cell carries its realised ``n_dates`` against the parent's own ~225 requirement, so the
    deficit is a number per cell. Levers 1-3 are then applied and the SAME cells are re-read: if
    the pooled full-TRAIN cell still cannot reach 225 effective dates, A3 is ``NOT_RESOLVABLE``
    on that band and that IS the answer 017 needed.
    """
    out = []
    df = _oos(panel)
    pred_cols = [c for c in df.columns if c.startswith("pred__") and c.endswith(f"__{TARGET}")]
    for band, src in _bands(df):
        # V-LEVEL / V-PERSIST / V-MEASURE forecast skill, as rank IC against the parent's target
        for pc in pred_cols:
            model = pc[len("pred__"):-len(f"__{TARGET}")]
            for key, g in src.groupby(["symbol", "clock"], sort=True, observed=True):
                out.append(cells.score_ic_cell(
                    g[pc].to_numpy(), g[TARGET].to_numpy(), g[TS].to_numpy(),
                    arm="A", item="A3",
                    key={"symbol": key[0], "clock": key[1], "band": band, "arm_name": "V-LEVEL",
                         "model": model, "metric": "oos_ic", "target": TARGET,
                         "basis": "per_symbol"},
                    n_boot=n_boot))
            for clock, g in src.groupby("clock", sort=True, observed=True):
                out.append(cells.score_ic_cell(
                    g[pc].to_numpy(), g[TARGET].to_numpy(), g[TS].to_numpy(),
                    arm="A", item="A3",
                    key={"symbol": "__POOLED__", "clock": clock, "band": band,
                         "arm_name": "V-LEVEL", "model": model, "metric": "oos_ic",
                         "target": TARGET, "basis": "pooled_raw"},
                    levers_exhausted=(band == "TRAIN"), n_boot=n_boot))
        # V-REGIME (the rolling-median split, not the HMM) — a STATE leg, scored on all rows
        reg = _state_rows(panel)
        reg = reg[(reg["regime_state"].notna())
                  & (reg["band"] == band if band != "TRAIN" else True)]
        for key, g in reg.groupby(["symbol", "clock"], sort=True, observed=True):
            out.append(cells.score_gap_cell(
                g[TARGET].to_numpy(), (g["regime_state"].to_numpy(dtype=float) == 1),
                g[TS].to_numpy(), arm="A", item="A3",
                key={"symbol": key[0], "clock": key[1], "band": band, "arm_name": "V-REGIME",
                     "metric": "gap_high_low_bps", "basis": "per_symbol"},
                n_boot=n_boot))
        for clock, g in reg.groupby("clock", sort=True, observed=True):
            out.append(cells.score_gap_cell(
                g[TARGET].to_numpy(), (g["regime_state"].to_numpy(dtype=float) == 1),
                g[TS].to_numpy(), arm="A", item="A3",
                key={"symbol": "__POOLED__", "clock": clock, "band": band,
                     "arm_name": "V-REGIME", "metric": "gap_high_low_bps", "basis": "pooled_raw",
                     "_symbols": g["symbol"].to_numpy()},
                levers_exhausted=(band == "TRAIN"), n_boot=n_boot))
    return out


def a3_xs(xs: pd.DataFrame, *, n_boot: int) -> list[dict]:
    """A3 — the V-XS leg: cross-sectional rank vs the same target."""
    out = []
    for band, src in _bands(xs):
        for key, g in src.groupby(["symbol", "clock"], sort=True, observed=True):
            out.append(cells.score_ic_cell(
                g["xs_pct"].to_numpy(), g["target_abs_oo"].to_numpy(), g["slot_start"].to_numpy(),
                arm="A", item="A3",
                key={"symbol": key[0], "clock": key[1], "band": band, "arm_name": "V-XS",
                     "metric": "xs_ic_rank_vs_target", "basis": "per_symbol"},
                n_boot=n_boot))
        for clock, g in src.groupby("clock", sort=True, observed=True):
            out.append(cells.score_ic_cell(
                g["xs_pct"].to_numpy(), g["target_abs_oo"].to_numpy(), g["slot_start"].to_numpy(),
                arm="A", item="A3",
                key={"symbol": "__POOLED__", "clock": clock, "band": band, "arm_name": "V-XS",
                     "metric": "xs_ic_rank_vs_target", "basis": "pooled_raw"},
                levers_exhausted=(band == "TRAIN"), n_boot=n_boot))
            gg = g[g["xs_tercile"].notna()]
            if len(gg):
                out.append(cells.score_gap_cell(
                    gg["target_abs_oo"].to_numpy(),
                    (gg["xs_tercile"].to_numpy(dtype=float) == 2),
                    gg["slot_start"].to_numpy(), arm="A", item="A3",
                    key={"symbol": "__POOLED__", "clock": clock, "band": band,
                         "arm_name": "V-XS", "metric": "xs_gap_top_minus_bottom_bps",
                         "basis": "pooled_raw", "_symbols": gg["symbol"].to_numpy()},
                    levers_exhausted=(band == "TRAIN"), n_boot=n_boot))
    return out


# --------------------------------------------------------------------------- A4
def a4_vclock(panel: pd.DataFrame, *, n_boot: int) -> list[dict]:
    """A4 — V-CLOCK: session + day-of-week dummies as incremental OOS R^2 over V-LEVEL.

    The open question is whether the D1 penalty is overfitting rather than evidence against
    calendar structure, so every cell co-reports its observations-per-date: 7 dummies on ~100
    daily observations is a statement about the estimator, not about the market.
    """
    out = []
    df = _oos(panel)
    base_col = f"pred__vlevel_ridge__{TARGET}"
    variants = {"vclock_full": "session+dow", "vclock_session": "session", "vclock_dow": "dow"}
    for band, src in _bands(df):
        for pc, label in variants.items():
            col = f"pred__{pc}__{TARGET}"
            if col not in src.columns:
                out.append({"arm": "A", "residue_item": "A4", "variant": label,
                            "status": "COLUMN_ABSENT_IN_PARENT_PANEL",
                            "note": "reported, not skipped (design §1.1)"})
                continue
            for key, g in src.groupby(["symbol", "clock"], sort=True, observed=True):
                out.append(cells.score_r2_cell(
                    g[TARGET].to_numpy(), g[col].to_numpy(), g[base_col].to_numpy(),
                    g[TS].to_numpy(), arm="A", item="A4",
                    key={"symbol": key[0], "clock": key[1], "band": band, "arm_name": "V-CLOCK",
                         "variant": label, "metric": f"incr_r2_{label}",
                         "base_model": "vlevel_ridge", "basis": "per_symbol",
                         "is_d1_open_item": key[1] == "D1", "n_dummies": {"session+dow": 9,
                                                                          "session": 2,
                                                                          "dow": 6}[label]},
                    n_boot=n_boot))
            for clock, g in src.groupby("clock", sort=True, observed=True):
                out.append(cells.score_r2_cell(
                    g[TARGET].to_numpy(), g[col].to_numpy(), g[base_col].to_numpy(),
                    g[TS].to_numpy(), arm="A", item="A4",
                    key={"symbol": "__POOLED__", "clock": clock, "band": band,
                         "arm_name": "V-CLOCK", "variant": label,
                         "metric": f"incr_r2_{label}", "base_model": "vlevel_ridge",
                         "basis": "pooled_raw", "is_d1_open_item": clock == "D1"},
                    levers_exhausted=(band == "TRAIN"), n_boot=n_boot))
    return out


# --------------------------------------------------------------------------- A5
def a5_thirds(panel: pd.DataFrame) -> list[dict]:
    """A5 — the §6.4 clause unsatisfiability and the calendar-thirds vacuity, MEASURED.

    For every cell: how many of the three calendar thirds contain any scored origin at all, how
    many contain enough to carry a sign, and where the first populated third starts. A clause
    that requires sign-stability in >=2 of 3 thirds is UNSATISFIABLE for a cell whose first third
    precedes the catalog — and that is a property of the band, not a finding about volatility.
    """
    out = []
    df = _oos(panel)
    for band, src in _bands(df):
        for key, g in src.groupby(["symbol", "clock"], sort=True, observed=True):
            ts = g[TS].to_numpy(dtype=np.int64)
            v = g[TARGET].to_numpy(dtype=float)
            ok = np.isfinite(v)
            ts, v = ts[ok], v[ok]
            pop = cells.thirds_populated(v, ts)
            per_third = []
            if ts.size:
                lo, hi = ts.min(), ts.max()
                edges = np.linspace(lo, hi + 1, 4)
                for i in range(3):
                    m = (ts >= edges[i]) & (ts < edges[i + 1])
                    per_third.append({"third": i + 1, "n": int(m.sum()),
                                      "n_dates": int(np.unique(ts[m] // (86_400 * 10 ** 9)).size)})
            out.append({
                "arm": "A", "residue_item": "A5", "symbol": key[0], "clock": key[1],
                "band": band, "arm_name": "STABILITY", "metric": "calendar_thirds_populated",
                "basis": "per_symbol",
                "n": int(ts.size), "thirds_populated": int(pop),
                "thirds_sign_agree": cells.thirds_sign_agree(v, ts),
                "per_third": per_third,
                "clause_satisfiable": bool(pop >= 2),
                "clause": "sign-stability in >= 2 of 3 DESIGN thirds (SPDR-012 §6.4)",
                "interpretation": (
                    "a cell with fewer than two populated thirds cannot satisfy the clause on "
                    "this band at all; the clause is unsatisfiable there, which is a property of "
                    "the catalog span, not evidence about volatility structure (B-5)"),
            })
    return out
