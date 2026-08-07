#!/usr/bin/env python3
"""SPDR-024 preflight: every number computed from TRAIN data, none recalled.

Design section 16 carries four items into implementation and this script discharges them:

* **P-1** per-cell planning floors from realised fill-based counts under all three variance
  treatments, compared to the R1 SIZE mechanism ceiling (AMENDMENT-7), marking cells
  DESCRIPTIVE for SIZE magnitude before execution when the floor sits above the ceiling.
* **P-2** H4 origin counts. The design assumes ~1/4 of H1; this measures it.
* **P-3** the CONVERSION-PIN divisor: ATR(20) on the signal-domain bar, lagged `[t-1]`, TRAIN
  median in bps, per instrument and per domain.
* **P-5** the two untested dependence axes.

AMENDMENT-7 R5: n basis is fills (domain-bar stop simulation) or explicitly labelled
provisional fill-rate-adjusted counts. Endpoint is the R1 mechanism ceiling — never
Step-3 0.022/0.150. No pure order-count "carries magnitude" pass.

Nothing here queries the TEST band or the global holdout: the same fenced TRAIN query the
runner uses is the only way bars enter this process.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PYTHON_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PYTHON_ROOT / "src"))

import numpy as np  # noqa: E402
import polars as pl  # noqa: E402
from nautilus_trader.persistence.catalog import ParquetDataCatalog  # noqa: E402

from xen.adaptive_management import runner  # noqa: E402
from xen.adaptive_management.contracts import SIGNAL_DOMAIN_HOURS  # noqa: E402
from xen.adaptive_management.entries import (  # noqa: E402
    FIXED_EXPIRY_BARS,
    FIXED_THRESHOLD_ATR,
    breakout_episodes,
    breakout_origins,
)
from xen.adaptive_management.features import (  # noqa: E402
    build_feature_panel,
    fit_calibration,
)
from xen.adaptive_management.spdr024 import regime_panel  # noqa: E402
from xen.adaptive_management.spdr024_analysis import (  # noqa: E402
    DEFAULT_PLANNING_GATE_RATE,
    MDE_Z,
    MIN_FILLS_FOR_PREFLIGHT,
    TIME_BLOCK_BARS,
    size_mechanism_ceiling,
)
from xen.nautilus.catalog_fence import (  # noqa: E402
    fenced_bar_query,
    load_fence_manifest,
)

# Frozen preflight descriptive vocabulary (design §10 PREFLIGHT M2). Not result bands.
LABEL_INSUFFICIENT = "INSUFFICIENT_FILLS_FOR_PREFLIGHT"
LABEL_DESCRIPTIVE = "DESCRIPTIVE_SIZE_MAGNITUDE_FLOOR_ABOVE_CEILING"
LABEL_CONTEXT = "CONTEXT_FLOOR_AT_OR_BELOW_MECHANISM_CEILING"


def _symbol_frames(universe: str, domain: str, symbol: str, manifest, config):
    catalog = ParquetDataCatalog(str(config.catalog_path))
    instrument_id = dict(zip(config.symbols, config.instrument_ids, strict=True))[symbol]
    bars = fenced_bar_query(
        catalog,
        [f"{instrument_id}-1-MINUTE-LAST-EXTERNAL"],
        manifest.analysis_start_utc,
        manifest.train_end_utc,
        band="TRAIN",
        manifest=manifest,
    )
    if not bars:
        raise RuntimeError(f"TRAIN query returned no bars for {instrument_id}")
    minute = runner._bars_frame(symbol, bars)
    domain_bars = runner._domain_frame(minute, domain)
    calibration = fit_calibration(domain_bars, domain_bars["ts"].min(), domain_bars["ts"].max())
    features = build_feature_panel(domain_bars, calibration)
    origins = breakout_origins(
        domain_bars.join(features.select("symbol", "ts", "atr20"), on=["symbol", "ts"])
    )
    episodes = breakout_episodes(
        origins,
        FIXED_THRESHOLD_ATR,
        FIXED_EXPIRY_BARS,
        experiment_id="SPDR-024",
        native_arm_id="FIXED_NATIVE_BREAKOUT",
    )
    return domain_bars, features, origins, episodes


def _planning_floor(n: int) -> float:
    """Preflight-only planning floor MDE_Z/√n (no bootstrap yet). Not a post-run row floor."""
    return float(MDE_Z / np.sqrt(n)) if n > 0 else float("nan")


def _simulate_domain_fills(orders: pl.DataFrame, domain_bars: pl.DataFrame) -> pl.DataFrame:
    """Domain-bar stop-hit + one-bar hold for baseline preflight fills.

    Minute-path engine fills are the production truth; this is the baseline-only micro-pass
    the design allows for preflight (no full arm lattice). Outcomes are gross one-domain-bar
    holds after a domain-bar stop touch.
    """
    if orders.is_empty():
        return pl.DataFrame(
            schema={
                "symbol": pl.Utf8,
                "decision_ts": pl.Datetime("ns", "UTC"),
                "side": pl.Int64,
                "fill_ts": pl.Datetime("ns", "UTC"),
                "outcome_bps": pl.Float64,
            }
        )
    bars = domain_bars.sort("ts")
    ts = bars["ts"].to_list()
    high = bars["high"].to_numpy().astype(float)
    low = bars["low"].to_numpy().astype(float)
    close = bars["close"].to_numpy().astype(float)
    index_by_ts = {t: i for i, t in enumerate(ts)}
    rows: list[dict] = []
    for order in orders.iter_rows(named=True):
        decision = order["decision_ts"]
        start = index_by_ts.get(decision)
        if start is None:
            # decision_ts may be the signal bar; actionable is often the next domain bar.
            # Fall back to first bar strictly after decision.
            start = next((i for i, t in enumerate(ts) if t > decision), None)
        if start is None:
            continue
        stop = float(order["stop_price"]) if order["stop_price"] is not None else float("nan")
        if not np.isfinite(stop):
            continue
        side = int(order["side"])
        expiry = int(order["expiry_bars"] or FIXED_EXPIRY_BARS)
        fill_i = None
        for offset in range(1, expiry + 1):
            i = start + offset
            if i >= len(ts):
                break
            if side > 0 and high[i] >= stop:
                fill_i = i
                break
            if side < 0 and low[i] <= stop:
                fill_i = i
                break
        if fill_i is None:
            continue
        # Hold = FIXED native one-domain-bar exit (the comparison arms keep the declared
        # one-bar hold when the cap is NOT_APPLICABLE — design §7 / implementation-notes §2).
        hold_bars = 1
        exit_i = fill_i + hold_bars
        if exit_i >= len(ts):
            continue
        exit_px = close[exit_i]
        outcome = side * (exit_px - stop) / stop * 1e4
        rows.append(
            {
                "symbol": order["symbol"],
                "decision_ts": decision,
                "side": side,
                "fill_ts": ts[fill_i],
                "outcome_bps": float(outcome),
                "hold_bars_sim": hold_bars,
            }
        )
    return pl.DataFrame(rows) if rows else pl.DataFrame(
        schema={
            "symbol": pl.Utf8,
            "decision_ts": pl.Datetime("ns", "UTC"),
            "side": pl.Int64,
            "fill_ts": pl.Datetime("ns", "UTC"),
            "outcome_bps": pl.Float64,
        }
    )


def descriptive_power_label(
    n_fills: int,
    planning_floor: float,
    mechanism_ceiling: float,
) -> str:
    """R1 endpoint: compare planning floor to mechanism ceiling (not historical Step-3 range)."""
    if n_fills < MIN_FILLS_FOR_PREFLIGHT:
        return LABEL_INSUFFICIENT
    if not np.isfinite(planning_floor) or not np.isfinite(mechanism_ceiling):
        return LABEL_INSUFFICIENT
    if planning_floor > mechanism_ceiling:
        return LABEL_DESCRIPTIVE
    return LABEL_CONTEXT


def _symbol_report(
    symbol: str,
    domain: str,
    domain_bars: pl.DataFrame,
    features: pl.DataFrame,
    origins: pl.DataFrame,
    episodes: pl.DataFrame,
) -> dict:
    ordered = episodes.filter(pl.col("state") == "ORDER_CREATED")
    fills = _simulate_domain_fills(ordered, domain_bars)
    n_orders = int(ordered.height)
    n_fills = int(fills.height)
    fill_rate = float(n_fills / n_orders) if n_orders else float("nan")

    regimes = regime_panel(features)
    if n_fills:
        fills = fills.with_columns(
            pl.col("decision_ts").cast(pl.Datetime("ns", "UTC")),
            pl.col("fill_ts").cast(pl.Datetime("ns", "UTC")),
        )
        filled_with_regime = fills.join(
            regimes.rename({"ts": "decision_ts"}), on=["symbol", "decision_ts"], how="left"
        )
        epochs = fills["decision_ts"].dt.epoch("ns").to_numpy()
        block_ns = TIME_BLOCK_BARS * SIGNAL_DOMAIN_HOURS[domain] * 3_600_000_000_000
        n_time_blocks = int(np.unique(epochs // block_ns).size)
        n_regime_blocks = int(
            filled_with_regime["regime_episode_id"].drop_nulls().n_unique()
        )
        outcomes = fills["outcome_bps"].to_numpy().astype(float)
        gross_mean = float(np.mean(outcomes)) if outcomes.size else float("nan")
        gross_sigma = (
            float(np.std(outcomes, ddof=1)) if outcomes.size > 1 else float("nan")
        )
    else:
        n_time_blocks = n_regime_blocks = 0
        gross_mean = gross_sigma = float("nan")

    ceiling = size_mechanism_ceiling(
        gross_mean, gross_sigma, gate_rate=DEFAULT_PLANNING_GATE_RATE
    )
    floors = {
        "V_A_UNCHUNKED": _planning_floor(n_fills),
        "V_B_TIME_BLOCK": _planning_floor(n_time_blocks),
        "V_C_REGIME_EPISODE": _planning_floor(n_regime_blocks),
    }
    finite = [value for value in floors.values() if np.isfinite(value)]
    conservative = max(finite) if finite else float("nan")

    atr_bps = (
        features.join(domain_bars.select("symbol", "ts", "close"), on=["symbol", "ts"])
        .select((pl.col("atr20") / pl.col("close") * 1e4).alias("atr20_bps"))
        .drop_nulls()["atr20_bps"]
    )
    return {
        "symbol": symbol,
        "domain_bars": int(domain_bars.height),
        "origins": int(origins.height),
        "fixed_arm_orders": n_orders,
        "fixed_arm_fills": n_fills,
        "fill_rate": fill_rate,
        "count_basis": "PROVISIONAL_DOMAIN_BAR_SIMULATED_FILLS",
        "order_rate_per_origin": (
            float(n_orders / origins.height) if origins.height else None
        ),
        "blocks": {
            "V_A_UNCHUNKED": n_fills,
            "V_B_TIME_BLOCK": n_time_blocks,
            "V_C_REGIME_EPISODE": n_regime_blocks,
        },
        "planning_mde_sigma": floors,
        "most_conservative_planning_mde_sigma": conservative,
        "baseline_gross_mean_bps": gross_mean,
        "baseline_gross_sigma_bps": gross_sigma,
        "planning_gate_rate": DEFAULT_PLANNING_GATE_RATE,
        "size_mechanism_ceiling_sigma": ceiling,
        "size_mechanism_ceiling_basis": (
            "PROVISIONAL_DOMAIN_BAR_SIM_ONE_BAR_HOLD_MATCHES_FIXED_NATIVE_HOLD"
        ),
        "power_label": descriptive_power_label(n_fills, conservative, ceiling),
        "power_label_endpoint": "R1_SIZE_MECHANISM_CEILING",
        "conversion_pin": {
            "divisor_object": "ATR(20) on the signal-domain bar, lagged [t-1]",
            "train_median_bps": float(atr_bps.median()) if atr_bps.len() else None,
            "train_p10_bps": float(atr_bps.quantile(0.10)) if atr_bps.len() else None,
            "train_p90_bps": float(atr_bps.quantile(0.90)) if atr_bps.len() else None,
            "rows": int(atr_bps.len()),
            "source": "COMPUTED_FROM_TRAIN_DATA_NEVER_RECALLED",
        },
        "regime_episodes": int(regime_panel(features)["regime_episode_id"].n_unique()),
    }


def _cross_symbol_correlation(closes: dict[str, pl.DataFrame]) -> dict:
    """P-5 (ii): contemporaneous cross-symbol correlation. No time blocking addresses it."""
    frames = [
        frame.select("ts", pl.col("close").log().diff().alias(symbol)).drop_nulls()
        for symbol, frame in closes.items()
    ]
    if len(frames) < 2:
        return {"pairs": 0, "note": "fewer than two symbols"}
    joined = frames[0]
    for frame in frames[1:]:
        joined = joined.join(frame, on="ts", how="inner")
    columns = [name for name in joined.columns if name != "ts"]
    values = joined.select(columns).to_numpy()
    if values.shape[0] < 30:
        return {"pairs": 0, "note": "too few overlapping bars"}
    matrix = np.corrcoef(values, rowvar=False)
    upper = matrix[np.triu_indices_from(matrix, k=1)]
    return {
        "symbols": columns,
        "overlapping_bars": int(values.shape[0]),
        "pairs": int(upper.size),
        "mean_correlation": float(np.mean(upper)),
        "median_correlation": float(np.median(upper)),
        "max_correlation": float(np.max(upper)),
        "min_correlation": float(np.min(upper)),
        "consequence": (
            "the interval stays symbol-clustered under every variance treatment (M1)"
        ),
    }


def _weight_series_dependence(weights: dict[str, np.ndarray]) -> dict:
    """P-5 (i), pre-execution half: dependence in the sizing weight series itself."""
    report = {}
    for symbol, series in weights.items():
        values = np.asarray(series, dtype=float)
        values = values[np.isfinite(values)]
        if values.size < 30 or np.std(values) == 0:
            report[symbol] = {"n": int(values.size), "autocorrelation": None}
            continue
        centred = values - values.mean()
        denominator = float(np.dot(centred, centred))
        acf = [
            float(np.dot(centred[:-lag], centred[lag:]) / denominator)
            for lag in range(1, min(21, values.size))
        ]
        report[symbol] = {
            "n": int(values.size),
            "max_abs_autocorrelation_lag_1_20": float(np.max(np.abs(acf))),
            "noise_band_95": float(1.96 / np.sqrt(values.size)),
        }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe", required=True, choices=("crypto", "ctrader"))
    parser.add_argument("--domain", required=True, choices=("H1", "H4"))
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--symbols", nargs="*", default=None)
    args = parser.parse_args(argv)

    config = runner.universe_config(args.universe)
    manifest = load_fence_manifest(config.manifest_path)
    symbols = args.symbols or list(config.symbols)

    reports = []
    closes: dict[str, pl.DataFrame] = {}
    weights: dict[str, np.ndarray] = {}
    for symbol in symbols:
        domain_bars, features, origins, episodes = _symbol_frames(
            args.universe, args.domain, symbol, manifest, config
        )
        reports.append(
            _symbol_report(symbol, args.domain, domain_bars, features, origins, episodes)
        )
        closes[symbol] = domain_bars.select("ts", "close")
        ordered = episodes.filter(pl.col("state") == "ORDER_CREATED")
        state = ordered.join(
            features.select("symbol", pl.col("ts").alias("decision_ts"), "tail_risk"),
            on=["symbol", "decision_ts"],
            how="left",
        )
        weights[symbol] = (
            state.with_columns(
                pl.when(pl.col("tail_risk") == "HIGH").then(0.5).otherwise(1.0).alias("w")
            )["w"]
            .to_numpy()
            .astype(float)
        )

    pooled_orders = int(sum(item["fixed_arm_orders"] for item in reports))
    pooled_fills = int(sum(item["fixed_arm_fills"] for item in reports))
    # Pool baseline moments by fill-weighted combination of per-symbol outcomes is not
    # available here without re-emitting fills; recompute ceiling from pooled moments when
    # every symbol reported them, else from fill-weighted means of symbol moments.
    means = [
        (item["baseline_gross_mean_bps"], item["fixed_arm_fills"])
        for item in reports
        if item["fixed_arm_fills"] > 0 and np.isfinite(item["baseline_gross_mean_bps"])
    ]
    sigmas = [
        (item["baseline_gross_sigma_bps"], item["fixed_arm_fills"])
        for item in reports
        if item["fixed_arm_fills"] > 1 and np.isfinite(item["baseline_gross_sigma_bps"])
    ]
    total_m = sum(n for _, n in means) or 1
    pooled_mean = float(sum(m * n for m, n in means) / total_m) if means else float("nan")
    # Conservative pooled σ: fill-weighted root-mean-square of symbol σ (not understating).
    total_s = sum(n for _, n in sigmas) or 1
    pooled_sigma = (
        float(np.sqrt(sum((s ** 2) * n for s, n in sigmas) / total_s)) if sigmas else float("nan")
    )
    ceiling = size_mechanism_ceiling(
        pooled_mean, pooled_sigma, gate_rate=DEFAULT_PLANNING_GATE_RATE
    )
    pooled = {
        "n_orders_created": pooled_orders,
        "n_fills": pooled_fills,
        "count_basis": "PROVISIONAL_DOMAIN_BAR_SIMULATED_FILLS",
        "fill_rate": float(pooled_fills / pooled_orders) if pooled_orders else float("nan"),
        "planning_mde_sigma_V_A_UNCHUNKED": _planning_floor(pooled_fills),
        "planning_mde_sigma_V_B_TIME_BLOCK": _planning_floor(
            sum(item["blocks"]["V_B_TIME_BLOCK"] for item in reports)
        ),
        "planning_mde_sigma_V_C_REGIME_EPISODE": _planning_floor(
            sum(item["blocks"]["V_C_REGIME_EPISODE"] for item in reports)
        ),
        "baseline_gross_mean_bps": pooled_mean,
        "baseline_gross_sigma_bps": pooled_sigma,
        "planning_gate_rate": DEFAULT_PLANNING_GATE_RATE,
        "size_mechanism_ceiling_sigma": ceiling,
    }
    floor_values = [
        value
        for key, value in pooled.items()
        if key.startswith("planning_mde_sigma") and np.isfinite(value)
    ]
    pooled["most_conservative_planning_mde_sigma"] = (
        max(floor_values) if floor_values else float("nan")
    )
    pooled["power_label"] = descriptive_power_label(
        pooled_fills,
        pooled["most_conservative_planning_mde_sigma"],
        ceiling,
    )
    pooled["power_label_endpoint"] = "R1_SIZE_MECHANISM_CEILING"
    pooled["power_label_basis"] = "FILLS_NOT_ORDERS"

    payload = {
        "experiment_id": "SPDR-024",
        "universe": args.universe,
        "signal_domain": args.domain,
        "band": "TRAIN",
        "amendment": "AMENDMENT-7",
        "manifest_sha256": manifest.sha256,
        "train_start_utc": manifest.analysis_start_utc.isoformat(),
        "train_end_utc": manifest.train_end_utc.isoformat(),
        "P1_per_symbol": reports,
        "P1_pooled": pooled,
        "P2_origin_counts": {
            item["symbol"]: {
                "origins": item["origins"],
                "orders": item["fixed_arm_orders"],
                "fills": item["fixed_arm_fills"],
            }
            for item in reports
        },
        "P3_conversion_pin": {
            item["symbol"]: item["conversion_pin"] for item in reports
        },
        "P5_cross_symbol_correlation": _cross_symbol_correlation(closes),
        "P5_weight_series_dependence": _weight_series_dependence(weights),
        "P5_paired_difference_dependence": {
            "status": "NOT_COMPUTABLE_BEFORE_EXECUTION",
            "reason": (
                "the paired arm-difference series is outcome x weight and no outcome exists "
                "before the run; the weight half is measured above"
            ),
            "scheduled": "first post-execution diagnostic, before any effect is read",
        },
        "interpretation": "OPERATIONAL_AND_POWER_CONTEXT_ONLY_NO_RESEARCH_VALUE",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")
    print(
        json.dumps(
            {
                "universe": args.universe,
                "domain": args.domain,
                "pooled": pooled,
                "per_symbol_power": {
                    item["symbol"]: item["power_label"] for item in reports
                },
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
