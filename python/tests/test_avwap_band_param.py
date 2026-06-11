"""Regression tests for the Phase 011 band parameterization of ``xen.avwap``.

EXP-042 added ``band_multiplier`` and ``arm_at_adverse_band`` to
``generate_avwap_events`` (operator-ratified 2026-06-11). Because the shared
generator underpins all prior AVWAP experiments, these tests pin:

1. the default call reproduces the frozen Phase-004 baseline event population
   (a hash-anchored fixture; the multiplier must not affect baseline entry);
2. determinism (identical repeat output);
3. arm-at-adverse-band semantics on hand-crafted bull/bear cases;
4. monotone non-increasing event counts as the band widens.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta

import numpy as np
import polars as pl

from xen.avwap import generate_avwap_events

# Frozen baseline event-population anchor on the seeded fixture below.
# Pinned 2026-06-11 from the pre-parameterization behavior (default arguments
# reproduce the Phase-004 frozen entry rule: arm at AVWAP, trigger at AVWAP).
FIXTURE_SEED = 7
FIXTURE_BARS = 3000
BASELINE_EVENT_COUNT = 69


def seeded_fixture() -> pl.DataFrame:
    """Deterministic synthetic OHLCV domain frame (random walk, seeded)."""
    rng = np.random.default_rng(FIXTURE_SEED)
    close = 100.0 * np.exp(np.cumsum(rng.normal(0.0, 0.003, FIXTURE_BARS)))
    high = close * (1.0 + rng.uniform(0.0, 0.002, FIXTURE_BARS))
    low = close * (1.0 - rng.uniform(0.0, 0.002, FIXTURE_BARS))
    start = datetime(2024, 1, 1)
    return pl.DataFrame({
        "CloseTime": [start + timedelta(hours=i) for i in range(FIXTURE_BARS)],
        "Open": close,
        "High": high,
        "Low": low,
        "Close": close,
        "TickVolume": rng.integers(100, 1000, FIXTURE_BARS),
    })


def trend_frame(direction: int, dip_at: int, dip_depth: float, n: int = 220) -> pl.DataFrame:
    """Monotone trend with one pullback of ``dip_depth`` price units at ``dip_at``.

    ``direction`` +1 builds an uptrend (bullish regime), -1 a downtrend.
    Constant TickVolume keeps the AVWAP analytically simple.
    """
    base = 100.0 + direction * 0.1 * np.arange(n, dtype=float)
    close = base.copy()
    close[dip_at : dip_at + 3] -= direction * dip_depth
    start = datetime(2024, 1, 1)
    return pl.DataFrame({
        "CloseTime": [start + timedelta(hours=i) for i in range(n)],
        "Open": close,
        "High": close + 0.01,
        "Low": close - 0.01,
        "Close": close,
        "TickVolume": np.full(n, 500, dtype=np.int64),
    })


def events_digest(events: pl.DataFrame) -> str:
    """Stable digest of the event population (trigger times + directions)."""
    payload = "|".join(
        f"{t}:{d}" for t, d in zip(
            events.get_column("trigger_time").to_list(),
            events.get_column("direction").to_list(),
        )
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def test_default_reproduces_frozen_baseline() -> None:
    frame = seeded_fixture()
    result = generate_avwap_events(frame, instrument="T", domain="1h")
    assert result.events.height == BASELINE_EVENT_COUNT
    # The multiplier must not change the baseline event population (entry is
    # band-free when arm_at_adverse_band is False); only target columns move.
    wide = generate_avwap_events(
        frame, instrument="T", domain="1h", band_multiplier=5.0
    )
    assert wide.events.height == result.events.height
    assert events_digest(wide.events) == events_digest(result.events)


def test_default_is_deterministic() -> None:
    frame = seeded_fixture()
    a = generate_avwap_events(frame, instrument="T", domain="1h")
    b = generate_avwap_events(frame, instrument="T", domain="1h")
    assert a.events.equals(b.events)
    assert a.regimes.equals(b.regimes)


def test_event_count_monotone_in_band() -> None:
    frame = seeded_fixture()
    counts = [
        generate_avwap_events(
            frame, instrument="T", domain="1h",
            band_multiplier=b, arm_at_adverse_band=True,
        ).events.height
        for b in (1.0, 1.5, 2.0, 2.5, 3.0)
    ]
    assert counts == sorted(counts, reverse=True)
    assert counts[0] > 0


# A 10-unit pullback in the trend fixture crosses the AVWAP (arms the
# baseline) and the 1.0x adverse band, but stays inside the 3.0x band, and is
# shallow enough not to flip the MA(20,50) regime — verified empirically when
# the fixture was pinned (depth 30 flips the regime and kills the bounce).
MODERATE_DIP = 10.0


def test_arm_at_adverse_band_bull() -> None:
    frame = trend_frame(direction=1, dip_at=120, dip_depth=MODERATE_DIP)
    base = generate_avwap_events(frame, instrument="T", domain="1h")
    narrow = generate_avwap_events(
        frame, instrument="T", domain="1h",
        band_multiplier=1.0, arm_at_adverse_band=True,
    )
    wide = generate_avwap_events(
        frame, instrument="T", domain="1h",
        band_multiplier=3.0, arm_at_adverse_band=True,
    )
    assert base.events.height >= 1          # baseline arms at the AVWAP
    assert narrow.events.height >= 1        # dip crosses the 1.0x band
    assert (narrow.events.get_column("direction") == 1).all()
    assert wide.events.height == 0          # dip does NOT reach the 3.0x band


def test_arm_at_adverse_band_bear() -> None:
    frame = trend_frame(direction=-1, dip_at=120, dip_depth=MODERATE_DIP)
    narrow = generate_avwap_events(
        frame, instrument="T", domain="1h",
        band_multiplier=1.0, arm_at_adverse_band=True,
    )
    wide = generate_avwap_events(
        frame, instrument="T", domain="1h",
        band_multiplier=3.0, arm_at_adverse_band=True,
    )
    assert narrow.events.height >= 1
    assert (narrow.events.get_column("direction") == -1).all()
    assert wide.events.height == 0
