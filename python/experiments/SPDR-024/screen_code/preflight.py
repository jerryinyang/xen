#!/usr/bin/env python3
"""SPDR-024 preflight: every number computed from TRAIN data, none recalled.

Design section 16 carries four items into implementation and this script discharges them:

* **P-1** per-cell MDE from realised counts under all three variance treatments, taking the
  most conservative, and marking cells DESCRIPTIVE before execution (M2).
* **P-2** H4 origin counts. The design assumes ~1/4 of H1; this measures it.
* **P-3** the CONVERSION-PIN divisor: ATR(20) on the signal-domain bar, lagged `[t-1]`, TRAIN
  median in bps, per instrument and per domain. Asserting this from memory inflated a target
  4x once before (P-15 / L-21), so it is computed here or it does not exist.
* **P-5** the two untested dependence axes.

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
    MDE_Z,
    MIN_TRADES_FOR_POWER,
    STEP3_OBSERVED_EFFECT_SIGMA,
    TIME_BLOCK_BARS,
)
from xen.nautilus.catalog_fence import (  # noqa: E402
    fenced_bar_query,
    load_fence_manifest,
)


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


def _mde(n: int) -> float:
    return float(MDE_Z / np.sqrt(n)) if n > 0 else float("nan")


def _symbol_report(
    symbol: str,
    domain: str,
    domain_bars: pl.DataFrame,
    features: pl.DataFrame,
    origins: pl.DataFrame,
    episodes: pl.DataFrame,
) -> dict:
    ordered = episodes.filter(pl.col("state") == "ORDER_CREATED")
    regimes = regime_panel(features)
    ordered_with_regime = ordered.join(
        regimes.rename({"ts": "decision_ts"}), on=["symbol", "decision_ts"], how="left"
    )
    # V-A: one block per trade. V-B: fixed clock blocks of TIME_BLOCK_BARS domain bars.
    # V-C: one block per contiguous regime episode that actually contains an origin.
    n_trades = int(ordered.height)
    block_ns = TIME_BLOCK_BARS * SIGNAL_DOMAIN_HOURS[domain] * 3_600_000_000_000
    if n_trades:
        epochs = ordered["decision_ts"].cast(pl.Datetime("ns", "UTC")).dt.epoch("ns").to_numpy()
        n_time_blocks = int(np.unique(epochs // block_ns).size)
        n_regime_blocks = int(
            ordered_with_regime["regime_episode_id"].drop_nulls().n_unique()
        )
    else:
        n_time_blocks = n_regime_blocks = 0

    # P-3 CONVERSION-PIN: ATR(20) on the signal-domain bar, lagged [t-1], median in bps.
    atr_bps = (
        features.join(domain_bars.select("symbol", "ts", "close"), on=["symbol", "ts"])
        .select((pl.col("atr20") / pl.col("close") * 1e4).alias("atr20_bps"))
        .drop_nulls()["atr20_bps"]
    )
    mdes = {
        "V_A_UNCHUNKED": _mde(n_trades),
        "V_B_TIME_BLOCK": _mde(n_time_blocks),
        "V_C_REGIME_EPISODE": _mde(n_regime_blocks),
    }
    finite = [value for value in mdes.values() if np.isfinite(value)]
    conservative = max(finite) if finite else float("nan")
    return {
        "symbol": symbol,
        "domain_bars": int(domain_bars.height),
        "origins": int(origins.height),
        # STOP ORDERS CREATED, not trades. Not every order fills, so this is an upper bound
        # on the realised sample and must never be quoted as a trade count (rows-are-not-trades
        # applies to orders too).
        "fixed_arm_orders": n_trades,
        "count_basis": "STOP_ORDERS_CREATED_UPPER_BOUND_ON_FILLS",
        "order_rate_per_origin": (
            float(n_trades / origins.height) if origins.height else None
        ),
        "blocks": {
            "V_A_UNCHUNKED": n_trades,
            "V_B_TIME_BLOCK": n_time_blocks,
            "V_C_REGIME_EPISODE": n_regime_blocks,
        },
        "mde_sigma": mdes,
        "most_conservative_mde_sigma": conservative,
        "power_label": _power_label(n_trades, conservative),
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


def _power_label(n_trades: int, mde: float) -> str:
    """M2, applied BEFORE execution: a cell that cannot resolve is DESCRIPTIVE in advance."""
    if n_trades < MIN_TRADES_FOR_POWER:
        return "UNPOWERED_BELOW_MIN_TRADES"
    if not np.isfinite(mde):
        return "UNPOWERED_NO_ESTIMATE"
    if mde > STEP3_OBSERVED_EFFECT_SIGMA:
        return "DESCRIPTIVE_CANNOT_RESOLVE_STEP3_EFFECT"
    return "CARRIES_MAGNITUDE_QUESTION"


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
    """P-5 (i), pre-execution half: dependence in the sizing weight series itself.

    The paired arm-difference series is outcome x weight. The outcome half cannot be measured
    before the run exists, and is scheduled as the first post-execution diagnostic; the weight
    half is a deterministic function of causal features and is measured here.
    """
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

    pooled_trades = int(sum(item["fixed_arm_orders"] for item in reports))
    pooled = {
        "n_orders_created": pooled_trades,
        "count_basis": (
            "STOP ORDERS CREATED. Fills are a subset, so every MDE below is OPTIMISTIC "
            "against the realised sample; the realised MDE is recomputed post-execution "
            "from filled trades."
        ),
        "mde_sigma_V_A_UNCHUNKED": _mde(pooled_trades),
        "mde_sigma_V_B_TIME_BLOCK": _mde(
            sum(item["blocks"]["V_B_TIME_BLOCK"] for item in reports)
        ),
        "mde_sigma_V_C_REGIME_EPISODE": _mde(
            sum(item["blocks"]["V_C_REGIME_EPISODE"] for item in reports)
        ),
    }
    pooled["most_conservative_mde_sigma"] = max(
        value
        for key, value in pooled.items()
        if key.startswith("mde_sigma") and np.isfinite(value)
    )
    pooled["power_label"] = _power_label(pooled_trades, pooled["most_conservative_mde_sigma"])
    pooled["power_label_basis"] = "ORDERS_NOT_FILLS_TREAT_AS_UPPER_BOUND"

    payload = {
        "experiment_id": "SPDR-024",
        "universe": args.universe,
        "signal_domain": args.domain,
        "band": "TRAIN",
        "manifest_sha256": manifest.sha256,
        "train_start_utc": manifest.analysis_start_utc.isoformat(),
        "train_end_utc": manifest.train_end_utc.isoformat(),
        "P1_per_symbol": reports,
        "P1_pooled": pooled,
        "P2_origin_counts": {
            item["symbol"]: {"origins": item["origins"], "orders": item["fixed_arm_orders"]}
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
        "interpretation": "OPERATIONAL_AND_POWER_ONLY_NO_RESEARCH_VALUE",
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
