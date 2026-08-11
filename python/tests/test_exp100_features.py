from __future__ import annotations

from xen.exp100.features import CausalVolatilityRegime, CausalWilderATR, StreamingOHLC
from xen.exp100.types import BarRecord

MINUTE_NS = 60_000_000_000
BASE_NS = 1_800_000_000_000_000_000


def _bar(ts: int, value: float) -> BarRecord:
    return BarRecord(
        ts_event_ns=ts,
        open=value,
        high=value + 1.0,
        low=value - 1.0,
        close=value,
        volume=1.0,
        source_bars=1,
    )


def test_streaming_ohlc_emits_only_complete_fixed_windows() -> None:
    aggregator = StreamingOHLC(period_minutes=2)

    assert aggregator.update(_bar(BASE_NS, 10.0)) is None
    completed = aggregator.update(_bar(BASE_NS + MINUTE_NS, 11.0))

    assert completed is not None
    assert completed.source_bars == 2
    assert completed.open == 10.0
    assert completed.high == 12.0
    assert completed.low == 9.0
    assert completed.close == 11.0


def test_streaming_ohlc_drops_incomplete_bucket_at_rollover() -> None:
    aggregator = StreamingOHLC(period_minutes=3)

    assert aggregator.update(_bar(BASE_NS, 10.0)) is None
    assert aggregator.update(_bar(BASE_NS + MINUTE_NS, 11.0)) is None
    assert aggregator.update(_bar(BASE_NS + 3 * MINUTE_NS, 12.0)) is None


def test_wilder_atr_has_explicit_warmup_and_then_updates_causally() -> None:
    atr = CausalWilderATR(period=2)

    assert atr.update(_bar(BASE_NS, 10.0)) is None
    assert atr.update(_bar(BASE_NS + MINUTE_NS, 11.0)) is None
    first = atr.update(_bar(BASE_NS + 2 * MINUTE_NS, 12.0))
    second = atr.update(_bar(BASE_NS + 3 * MINUTE_NS, 13.0))

    assert first == 2.0
    assert second == 2.0


def test_regime_labels_at_existing_events_do_not_change_after_future_values() -> None:
    initial = CausalVolatilityRegime(window=3)
    labels_initial = [initial.update(value) for value in (1.0, 2.0, 3.0)]

    extended = CausalVolatilityRegime(window=3)
    labels_extended = [extended.update(value) for value in (1.0, 2.0, 3.0, 100.0, 200.0)]

    assert labels_extended[:3] == labels_initial
    assert labels_initial[0] == "REGIME_WARMUP"


def test_regime_window_cannot_exceed_approved_bound() -> None:
    import pytest

    with pytest.raises(ValueError, match="1..252"):
        CausalVolatilityRegime(window=253)
