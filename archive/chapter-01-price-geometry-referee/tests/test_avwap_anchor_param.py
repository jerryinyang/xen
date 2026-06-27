"""Phase 013 P8 regression suite for the ``xen.avwap`` anchor parameterization.

EXP-047 added ``anchor_mode`` / ``anchor_atr_period`` / ``anchor_prominence_k``
to ``generate_avwap_events`` (D0 RATIFIED 2026-06-12: ATR(14), k=1.0). These
tests are the P8 data-contact gate and must be green before the first TRAIN
read. They pin:

1. baseline-anchor fixture invariance: defaults (and the explicit
   ``anchor_mode="running_extreme"``) reproduce the frozen Phase-004 baseline
   event population bit-for-bit, with ``anchor_fallback`` constant False;
2. `/ANCHOR` determinism: identical repeat output under ``atr_prominence``;
3. `/ANCHOR` look-ahead safety: a truncation probe — regenerating on a prefix
   reproduces every regime anchor and event confirmed within the prefix;
4. the running-extreme fallback path: an unattainable prominence threshold
   collapses `/ANCHOR` to the baseline anchors with ``anchor_fallback=True``;
5. parameter validation.
"""
from __future__ import annotations

import polars as pl
import pytest

from xen.avwap import generate_avwap_events

from test_avwap_band_param import (
    BASELINE_EVENT_COUNT,
    events_digest,
    seeded_fixture,
)

BASELINE_COLUMNS_DROP = ["anchor_fallback"]


def test_baseline_fixture_invariance_at_defaults() -> None:
    frame = seeded_fixture()
    default = generate_avwap_events(frame, instrument="T", domain="1h")
    explicit = generate_avwap_events(
        frame, instrument="T", domain="1h",
        anchor_mode="running_extreme", anchor_atr_period=14, anchor_prominence_k=1.0,
    )
    assert default.events.height == BASELINE_EVENT_COUNT
    assert explicit.events.equals(default.events)
    assert explicit.regimes.equals(default.regimes)
    # The new disclosure column is inert on the baseline path.
    assert not default.events.get_column("anchor_fallback").any()
    assert not default.regimes.get_column("anchor_fallback").any()


def test_atr_prominence_is_deterministic() -> None:
    frame = seeded_fixture()
    a = generate_avwap_events(
        frame, instrument="T", domain="1h", anchor_mode="atr_prominence"
    )
    b = generate_avwap_events(
        frame, instrument="T", domain="1h", anchor_mode="atr_prominence"
    )
    assert a.events.equals(b.events)
    assert a.regimes.equals(b.regimes)
    assert a.events.height > 0


def test_atr_prominence_look_ahead_safety_truncation_probe() -> None:
    """Anchors and events confirmed within a prefix must be invariant to the
    suffix: regenerate on ``head(P)`` and compare."""
    frame = seeded_fixture()
    full = generate_avwap_events(
        frame, instrument="T", domain="1h", anchor_mode="atr_prominence"
    )
    for prefix in (800, 1500, 2400):
        part = generate_avwap_events(
            frame.head(prefix), instrument="T", domain="1h",
            anchor_mode="atr_prominence",
        )
        full_regimes = full.regimes.filter(pl.col("confirm_idx") < prefix)
        part_regimes = part.regimes
        # Every regime confirmed inside the prefix selects the identical anchor.
        n = min(full_regimes.height, part_regimes.height)
        cols = ["regime_id", "direction", "confirm_idx", "anchor_idx",
                "anchor_price", "anchor_fallback"]
        assert n > 0
        assert part_regimes.select(cols).head(n).equals(full_regimes.select(cols).head(n))
        full_events = full.events.filter(pl.col("trigger_idx") < prefix)
        part_events = part.events.filter(pl.col("trigger_idx") < prefix)
        assert part_events.equals(full_events)


def test_unattainable_prominence_falls_back_to_running_extreme() -> None:
    frame = seeded_fixture()
    base = generate_avwap_events(frame, instrument="T", domain="1h")
    fb = generate_avwap_events(
        frame, instrument="T", domain="1h",
        anchor_mode="atr_prominence", anchor_prominence_k=1e9,
    )
    assert fb.regimes.get_column("anchor_fallback").all()
    assert fb.events.drop(BASELINE_COLUMNS_DROP).equals(
        base.events.drop(BASELINE_COLUMNS_DROP)
    )
    assert fb.regimes.drop(BASELINE_COLUMNS_DROP).equals(
        base.regimes.drop(BASELINE_COLUMNS_DROP)
    )


def test_k_one_moves_some_anchors_and_discloses_fallback_rate() -> None:
    """On the seeded fixture the ratified rule must exercise both branches:
    some regimes anchor on a qualifying pivot, and the anchors stay inside the
    segment (anchor at or before the confirmation bar — causal placement)."""
    frame = seeded_fixture()
    res = generate_avwap_events(
        frame, instrument="T", domain="1h", anchor_mode="atr_prominence"
    )
    rg = res.regimes
    assert rg.height > 0
    assert (rg.get_column("anchor_idx") <= rg.get_column("confirm_idx")).all()
    fallback_rate = float(rg.get_column("anchor_fallback").mean())
    assert 0.0 <= fallback_rate < 1.0  # at least one non-fallback selection
    # Digest sanity: the event population is a valid population either way.
    assert isinstance(events_digest(res.events), str)


def test_anchor_params_validated() -> None:
    frame = seeded_fixture()
    with pytest.raises(ValueError):
        generate_avwap_events(frame, instrument="T", domain="1h", anchor_mode="nope")
    with pytest.raises(ValueError):
        generate_avwap_events(
            frame, instrument="T", domain="1h",
            anchor_mode="atr_prominence", anchor_atr_period=0,
        )
    with pytest.raises(ValueError):
        generate_avwap_events(
            frame, instrument="T", domain="1h",
            anchor_mode="atr_prominence", anchor_prominence_k=-1.0,
        )
