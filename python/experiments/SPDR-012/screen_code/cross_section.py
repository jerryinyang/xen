"""V-XS — same-timestamp cross-sectional relative volatility (design §4).

Rank ``rv20`` across ALL universe symbols carrying a complete bar at that stamp (lexical
tie-break), cut into terciles, and read the next-bar ``|move|`` by own tercile plus the
top-minus-bottom gap. Pooled figures are disclosure-only (SPDR lane / L-03); the per-symbol
rows are the binding stratum.
"""
from __future__ import annotations

import numpy as np
import polars as pl

from stats_core import (
    band_gap,
    band_gap_detected,
    boot_group_mean_diff,
    boot_rank_corr,
    mde_from_se,
    mde_ic,
)

_COLS = ("slot_start", "rv20", "target_abs_oo", "target_date")


def build_panel(frames_by_symbol: dict) -> pl.DataFrame:
    """Stack the origin rows of every symbol for one clock x band into a ranked panel."""
    frames = [
        df.select(_COLS).with_columns(pl.lit(symbol).alias("symbol"))
        for symbol, df in sorted(frames_by_symbol.items())
        if df.height
    ]
    if not frames:
        return pl.DataFrame()
    panel = pl.concat(frames).drop_nulls(["rv20", "target_abs_oo"]).sort(["slot_start", "symbol"])
    panel = panel.with_columns(
        pl.col("rv20").rank("ordinal").over("slot_start").alias("xs_rank"),
        pl.len().over("slot_start").alias("xs_n"),
    )
    panel = panel.filter(pl.col("xs_n") >= 3)
    if panel.height == 0:
        return panel
    return panel.with_columns(
        ((pl.col("xs_rank") - 1) / (pl.col("xs_n") - 1)).alias("xs_pct"),
        (((pl.col("xs_rank") - 1) * 3) // pl.col("xs_n")).clip(0, 2).alias("xs_tercile"),
    )


def _row(symbol: str, clock: str, band: str, metric: str, value, **kw) -> dict:
    out = {
        "symbol": symbol, "clock": clock, "band": band, "arm": "V-XS", "metric": metric,
        "model": kw.pop("model", ""), "target": "target_abs_oo",
        "value": float(value) if value is not None and np.isfinite(value) else None,
        "ci_low": None, "ci_high": None, "se": None, "se_median": None,
        "n_obs": kw.pop("n_obs", None), "n_dates": kw.pop("n_dates", None),
        "mde": None, "band_label": kw.pop("band_label", ""),
        "band_label_detected": kw.pop("band_label_detected", ""),
        "target_overlaps_feature": False,
        "note": kw.pop("note", ""),
    }
    boot = kw.pop("boot", None)
    if boot is not None:
        for k in ("ci_low", "ci_high", "se", "se_median"):
            v = getattr(boot, k)
            out[k] = float(v) if np.isfinite(v) else None
        out["n_obs"], out["n_dates"] = boot.n_obs, boot.n_dates
        out["_ci_grid"] = boot.grid          # stripped into results/ci_grid.json (QA F-6)
    if "mde" in kw:
        v = kw.pop("mde")
        out["mde"] = float(v) if v is not None and np.isfinite(v) else None
    if kw:
        raise TypeError(f"unexpected fields {sorted(kw)}")
    return out


def _gap_rows(sub: pl.DataFrame, symbol: str, clock: str, band: str) -> list[dict]:
    y = sub["target_abs_oo"].to_numpy()
    ter = sub["xs_tercile"].to_numpy()
    dates = sub["target_date"].to_numpy()
    rows: list[dict] = []
    for t in (0, 1, 2):
        m = ter == t
        if m.sum() >= 5:
            rows.append(_row(symbol, clock, band, f"mean_abs_oo_tercile_{t}",
                             float(y[m].mean()), n_obs=int(m.sum()),
                             note="0 = lowest cross-sectional rv20 tercile"))
    m = ter != 1
    if m.sum() >= 10:
        b = boot_group_mean_diff(y[m], (ter[m] == 2).astype(float), dates[m])
        rows.append(_row(symbol, clock, band, "xs_gap_top_minus_bottom_bps", b.point, boot=b,
                         mde=mde_from_se(b.se),
                         band_label=band_gap(b.point, b.ci_low, b.ci_high, b.n_dates, b.se),
                         band_label_detected=band_gap_detected(
                             b.point, b.ci_low, b.ci_high, b.n_dates, b.se)))
    bi = boot_rank_corr(sub["xs_pct"].to_numpy(), y, dates)
    rows.append(_row(symbol, clock, band, "xs_ic_rank_vs_target", bi.point, boot=bi,
                     mde=mde_ic(bi.n_dates)))
    return rows


def xs_rows(frames_by_symbol: dict, clock: str, band: str) -> tuple[list[dict], pl.DataFrame]:
    """Per-symbol (binding) + POOLED (disclosure-only) V-XS metric rows."""
    panel = build_panel(frames_by_symbol)
    if panel.height == 0:
        return [], panel
    rows = _gap_rows(panel, "POOLED", clock, band)
    for r in rows:
        r["note"] = (r["note"] + "; POOLED = disclosure-only (L-03)").strip("; ")
    for symbol in sorted(panel["symbol"].unique().to_list()):
        sub = panel.filter(pl.col("symbol") == symbol)
        if sub.height >= 20:
            rows += _gap_rows(sub, symbol, clock, band)
    return rows, panel
