"""Per-cell data preparation and causal forecast production (design §3, §6.2).

One cell = symbol x clock. Features are built once over the continuous TRAIN sub-range
``[DESIGN_START, CONFIRM_END)`` so trailing windows are causal across the DESIGN/CONFIRM
boundary, then origins are split by band. DESIGN carries the walk-forward fits; CONFIRM is
scored only with the model frozen at the DESIGN end (design §7.3).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import polars as pl

from catalog_io import aggregate_clock, load_minute_bars
from config import (
    CLOCKS,
    CONFIRM_END,
    CONFIRM_START,
    DESIGN_END,
    DESIGN_START,
    EWMA_LAMBDA,
    HAR_MEANS,
    INITIAL_FIT_FRACTION,
    NS,
    REGIME_MEDIAN_WINDOW,
    RIDGE_ALPHA,
    V_LEVEL_FEATURES,
)
from features import add_regime_states, build_features
from hmm import HMMParams, fit_gaussian_hmm, filter_high_prob, walk_forward_states
from models import LinearModel, fit_linear, month_key, walk_forward_predict

HAR_FEATURES = ("rv20", "rv20_mean_6", "rv20_mean_24")
MEASURES = ("rv20", "parkinson", "gk")
TARGETS = ("target_abs_oo", "rv_next")
# V-CLOCK design matrix: UTC session buckets (base = 0-8) and DOW (base = Monday).
SESSION_DUMMIES = ("sess_1", "sess_2")
DOW_DUMMIES = tuple(f"dow_{i}" for i in range(1, 7))


@dataclass
class Cell:
    """Prepared per-(symbol, clock) data with DESIGN/CONFIRM origin frames + forecasts."""

    symbol: str
    clock: str
    design: pl.DataFrame = field(default_factory=pl.DataFrame)
    confirm: pl.DataFrame = field(default_factory=pl.DataFrame)
    diagnostics: dict = field(default_factory=dict)
    models: dict = field(default_factory=dict)
    hmm_final: HMMParams | None = None

    @property
    def has_design(self) -> bool:
        return self.design.height > 0


def _split_bands(feats: pl.DataFrame, clock: str) -> tuple[pl.DataFrame, pl.DataFrame, dict]:
    """Split origins into DESIGN / CONFIRM; drop origins whose target crosses the band end."""
    span_ns = CLOCKS[clock]["minutes"] * 60 * NS
    d_end = int(DESIGN_END.timestamp() * NS)
    c_start = int(CONFIRM_START.timestamp() * NS)
    c_end = int(CONFIRM_END.timestamp() * NS)

    org = feats.filter(pl.col("is_origin")).with_columns(
        (pl.col("target_slot_start") + span_ns).alias("target_end")
    )
    # The open-to-open target EXITS at the open of the bar after the target bar, i.e. at
    # target_end. Requiring target_end <= band_end would take that exit price from the first
    # print of the next band (QA F-7); require the whole exit bar to sit inside the band.
    design = org.filter(
        (pl.col("slot_end") <= d_end) & (pl.col("target_end") + span_ns <= d_end)
    )
    confirm = org.filter(
        (pl.col("slot_end") > c_start) & (pl.col("slot_end") <= c_end)
        & (pl.col("target_end") + span_ns <= c_end)
    )
    dropped = org.height - design.height - confirm.height
    return design, confirm, {"n_origins_total": org.height, "n_boundary_dropped": int(dropped)}


def _matrix(df: pl.DataFrame, cols: tuple[str, ...]) -> np.ndarray:
    return np.column_stack([df[c].to_numpy() for c in cols])


def _initial_fit_index(n: int) -> int:
    """Design §6.2 + IN-1: first 40% of this cell's scored DESIGN origins."""
    return max(1, int(np.floor(n * INITIAL_FIT_FRACTION)))


def _add_pred(df: pl.DataFrame, name: str, values: np.ndarray) -> pl.DataFrame:
    return df.with_columns(pl.Series(name, values))


def _add_calendar_dummies(df: pl.DataFrame) -> pl.DataFrame:
    """V-CLOCK design matrix columns (deterministic calendar, known at origin)."""
    if df.height == 0:
        return df
    cols = [(pl.col("session") == i).cast(pl.Float64).alias(f"sess_{i}") for i in (1, 2)]
    cols += [(pl.col("dow") == i).cast(pl.Float64).alias(f"dow_{i}") for i in range(1, 7)]
    return df.with_columns(cols)


def prepare_cell(symbol: str, clock: str, manifest) -> Cell:
    """Load, aggregate, feature-build, band-split and forecast one symbol x clock cell."""
    minutes = load_minute_bars(symbol, DESIGN_START, CONFIRM_END, manifest=manifest)
    bars = aggregate_clock(minutes, clock)
    diag = {
        "n_minute_bars": int(minutes.height),
        "n_clock_slots": int(bars.height),
        "n_complete": int(bars["complete"].sum()) if bars.height else 0,
        "first_minute_ts": int(minutes["ts_event"].min()) if minutes.height else None,
    }
    if bars.height == 0:
        return Cell(symbol, clock, diagnostics=diag | {"status": "NO_DATA"})

    feats = build_features(bars, clock)
    if feats.height == 0:
        return Cell(symbol, clock, diagnostics=diag | {"status": "NO_COMPLETE_BARS"})
    feats = add_regime_states(feats, clock, REGIME_MEDIAN_WINDOW[clock])

    design, confirm, split_diag = _split_bands(feats, clock)
    design, confirm = _add_calendar_dummies(design), _add_calendar_dummies(confirm)
    diag |= split_diag
    diag["n_design_origins"] = int(design.height)
    diag["n_confirm_origins"] = int(confirm.height)
    if design.height:
        diag["contiguous_frac_design"] = float(design["target_contiguous"].mean())
    if confirm.height:
        diag["contiguous_frac_confirm"] = float(confirm["target_contiguous"].mean())

    cell = Cell(symbol, clock, design, confirm, diag)
    if design.height < 60:
        cell.diagnostics["status"] = "DESIGN_TOO_SHORT" if design.height else "NO_DESIGN_HISTORY"
        return cell
    cell.diagnostics["status"] = "OK"

    _fit_forecasts(cell, clock)
    _fit_regimes(cell, clock)
    return cell


# ------------------------------------------------------- forecast arms ----


def _fit_forecasts(cell: Cell, clock: str) -> None:
    """Walk-forward OOS forecasts on DESIGN + frozen-model forecasts on CONFIRM."""
    d, c = cell.design, cell.confirm
    n = d.height
    start = _initial_fit_index(n)
    cell.diagnostics["initial_fit_n"] = start
    cell.diagnostics["oos_n_design"] = n - start

    ts = d["slot_end"].to_numpy()
    oos_mask = np.zeros(n, dtype=bool)
    oos_mask[start:] = True
    cell.design = _add_pred(d, "oos", oos_mask)
    if c.height:
        cell.confirm = _add_pred(c, "oos", np.ones(c.height, dtype=bool))

    specs: list[tuple[str, tuple[str, ...], str, float]] = []
    for tgt in TARGETS:
        specs.append((f"vlevel_ridge__{tgt}", V_LEVEL_FEATURES, tgt, RIDGE_ALPHA))
        specs.append((f"vlevel_ols__{tgt}", V_LEVEL_FEATURES, tgt, 0.0))
        specs.append((f"vpersist_har_ridge__{tgt}", HAR_FEATURES, tgt, RIDGE_ALPHA))
        specs.append((f"vpersist_har_ols__{tgt}", HAR_FEATURES, tgt, 0.0))
        for meas in MEASURES:
            specs.append((f"vmeasure_{meas}__{tgt}", (meas,), tgt, RIDGE_ALPHA))
    # V-CLOCK: calendar dummies stacked on the V-LEVEL design matrix -> incremental OOS R^2.
    specs.append(
        ("vclock_full__target_abs_oo",
         V_LEVEL_FEATURES + SESSION_DUMMIES + DOW_DUMMIES, "target_abs_oo", RIDGE_ALPHA)
    )
    specs.append(
        ("vclock_session__target_abs_oo",
         V_LEVEL_FEATURES + SESSION_DUMMIES, "target_abs_oo", RIDGE_ALPHA)
    )
    specs.append(
        ("vclock_dow__target_abs_oo",
         V_LEVEL_FEATURES + DOW_DUMMIES, "target_abs_oo", RIDGE_ALPHA)
    )

    for key, cols, tgt, alpha in specs:
        X = _matrix(cell.design, cols)
        y = cell.design[tgt].to_numpy()
        pred, base, final, fits = walk_forward_predict(X, y, ts, start, alpha=alpha)
        cell.design = cell.design.with_columns(
            pl.Series(f"pred__{key}", pred), pl.Series(f"base__{key}", base)
        )
        cell.models[key] = {
            "features": list(cols), "target": tgt, "alpha": alpha,
            "n_refits": len(fits),
            "final_n_fit": int(final.n_fit) if final else 0,
            "final_fit_end_ts": int(final.fit_end_ts) if final else 0,
        }
        if cell.confirm.height:
            Xc = _matrix(cell.confirm, cols)
            pc = final.predict(Xc) if final is not None else np.full(cell.confirm.height, np.nan)
            yd = y[np.isfinite(y)]
            bc = np.full(cell.confirm.height, float(yd.mean()) if yd.size else np.nan)
            cell.confirm = cell.confirm.with_columns(
                pl.Series(f"pred__{key}", pc), pl.Series(f"base__{key}", bc)
            )

    # EWMA (design §4 V-LEVEL): causal lambda=0.94 forecast used directly, no fit.
    # |move| scaling uses the parameter-free Gaussian factor E|X| = sigma*sqrt(2/pi); rank IC
    # is scale-free, and no fitted constant is introduced.
    abs_scale = 1e4 * float(np.sqrt(2.0 / np.pi))
    for frame_name in ("design", "confirm"):
        f = getattr(cell, frame_name)
        if f.height:
            setattr(cell, frame_name, f.with_columns(
                pl.col("ewma_vol").alias("pred__vlevel_ewma__rv_next"),
                (pl.col("ewma_vol") * abs_scale).alias("pred__vlevel_ewma__target_abs_oo"),
            ))
    cell.models["vlevel_ewma"] = {
        "lambda": EWMA_LAMBDA, "features": ["ewma_vol"], "fit": "none",
        "abs_scale": abs_scale,
    }


def _fit_regimes(cell: Cell, clock: str) -> None:
    """V-REGIME-HMM causal states on DESIGN (walk-forward) and CONFIRM (frozen params)."""
    d = cell.design
    n = d.height
    start = _initial_fit_index(n)
    r = d["r"].to_numpy()
    ts = d["slot_end"].to_numpy()
    mk = month_key(ts)
    prob, final, fits = walk_forward_states(r, ts, start, mk)
    cell.design = d.with_columns(
        pl.Series("hmm_high_prob", prob),
        pl.Series("hmm_state", np.where(np.isfinite(prob), (prob > 0.5).astype(np.int64), -1)),
    )
    cell.hmm_final = final
    cell.models["vregime_hmm"] = {
        "n_refits": len(fits),
        "final": final.to_dict() if final else None,
    }
    if cell.confirm.height and final is not None:
        joint = np.concatenate([r, cell.confirm["r"].to_numpy()])
        pr = filter_high_prob(joint, final)[n:]
        cell.confirm = cell.confirm.with_columns(
            pl.Series("hmm_high_prob", pr),
            pl.Series("hmm_state", np.where(np.isfinite(pr), (pr > 0.5).astype(np.int64), -1)),
        )
    elif cell.confirm.height:
        nan = np.full(cell.confirm.height, np.nan)
        cell.confirm = cell.confirm.with_columns(
            pl.Series("hmm_high_prob", nan),
            pl.Series("hmm_state", np.full(cell.confirm.height, -1, dtype=np.int64)),
        )
