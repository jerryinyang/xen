"""Config-as-code for the orderflow feature store (INFR-013, spec §2.3 / §10).

All extraction thresholds live here, consumed identically by the batch ingest
runtime and the (future) live Actor runtime. Any change to these values is a
`PIPELINE_VERSION` bump: every stored record carries the version, and
`config_hash()` pins the exact parameterization for audit.

Threshold VALUES below are v1 placeholders pending the collection INFR's
calibration pass on captured data — the contract (fields, stamping, hashing)
is what INFR-013 fixes.
"""

import hashlib
import json
from dataclasses import asdict, dataclass

# Bump on ANY change to extraction logic or the thresholds below.
PIPELINE_VERSION = "mbp-store-0.1.0"


@dataclass(frozen=True)
class SessionWindow:
    """A named UTC session window (crypto is 24/7 — sessions are config, spec §4.2)."""

    name: str
    start_utc: str  # "HH:MM"
    end_utc: str  # "HH:MM" (end-exclusive; may wrap midnight)


UTC_DAY = SessionWindow(name="UTC_DAY", start_utc="00:00", end_utc="00:00")


@dataclass(frozen=True)
class InstrumentOrderflowConfig:
    """Per-instrument extraction thresholds (spec §10 item 1)."""

    symbol: str
    tick_size: float
    # Family A — trade-size buckets: edges between small/medium/large (base units)
    size_bucket_edges: tuple[float, ...]
    # Family A — diagonal imbalance
    imbalance_ratio: float = 3.0
    imbalance_min_volume: float = 0.0
    # Family C — snapshot layer (the primary storage dial, spec §5.2)
    snapshot_interval_ms: int = 1000
    snapshot_depth_n: int = 50
    # Family D — detector thresholds (stubs in INFR-013; wired at collection INFR)
    absorption_min_volume: float = 0.0
    absorption_max_advance_ticks: int = 2
    sweep_min_levels: int = 3
    reload_min_added_size: float = 0.0
    pull_min_size: float = 0.0
    pull_max_distance_ticks: int = 5
    # Family B/E — session definitions
    session_windows: tuple[SessionWindow, ...] = (UTC_DAY,)


# v1 per-instrument registry (MBP trio, T2 confirm lane). Placeholder thresholds.
_CONFIGS: dict[str, InstrumentOrderflowConfig] = {
    cfg.symbol: cfg
    for cfg in (
        InstrumentOrderflowConfig(
            symbol="BTCUSDT",
            tick_size=0.1,
            size_bucket_edges=(0.1, 1.0),
        ),
        InstrumentOrderflowConfig(
            symbol="ETHUSDT",
            tick_size=0.01,
            size_bucket_edges=(1.0, 10.0),
        ),
        InstrumentOrderflowConfig(
            symbol="SOLUSDT",
            tick_size=0.001,
            size_bucket_edges=(10.0, 100.0),
        ),
    )
}


def get_config(symbol: str) -> InstrumentOrderflowConfig:
    """Return the registered config for `symbol` (raises KeyError if unregistered)."""
    return _CONFIGS[symbol]


def config_hash(cfg: InstrumentOrderflowConfig) -> str:
    """Deterministic sha256 over the full parameterization, for audit pinning."""
    payload = json.dumps(asdict(cfg), sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()
