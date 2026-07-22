"""Signed 1-minute bar tier (INFR-017, CF-SIGAUC-001).

The **bar tier** of aggressor-side flow: 1-minute OHLCV plus the exact taker
buy/sell volume split from Bybit trade archives, plus a trade count and the
legacy mean-price-skew storage field. The latter is never a spread input.

Deliberately separate from :mod:`xen.orderflow`, which is the **MBP/L2** feature
store (INFR-013 spec). Conflating the two would mix a bar-aggregate tier whose
defining property is *per-bar delta is exact, intra-bar is inferred* with a
book tier that resolves inside the bar.

Contents
--------
``data_types``
    :class:`SignedBar` — the byte-compatible custom Nautilus storage contract.
``access``
    Verified analytical access that exposes the legacy field only as
    ``MeanPriceSkewBps`` with status ``UNUSABLE_AS_SPREAD``.
``baselines``
    A5 seasonal baselines: minute-of-day x day-of-week residual normalisation.

INFR-018 instrument-build apparatus (imported directly, not re-exported here,
so importing the tier does not pull in the whole calibration stack):

``fences``
    Band fences, frozen-input hash verification, the online universe rule.
``sessions``
    A7 anchor candidates, IB windows, breaks, excursions, pseudo-anchor controls.
``acceptance``
    A6 discriminator candidates, outcome labels, separation.
``profile``
    §2.1 volume-profile kernels and their calibration against trade-level truth.
``classes``
    §2.3 signed effort-vs-result classes and the structural-clustering test.
"""

from xen.sigbar.baselines import (
    BASELINE_METRICS,
    fit_seasonal_baseline,
    residualise,
)
from xen.sigbar.access import (
    MEAN_PRICE_SKEW_COLUMN,
    UNUSABLE_AS_SPREAD,
    quarantine_mean_price_skew,
)
from xen.sigbar.data_types import SIGBAR_PIPELINE_VERSION, SignedBar

__all__ = [
    "BASELINE_METRICS",
    "MEAN_PRICE_SKEW_COLUMN",
    "SIGBAR_PIPELINE_VERSION",
    "SignedBar",
    "UNUSABLE_AS_SPREAD",
    "fit_seasonal_baseline",
    "quarantine_mean_price_skew",
    "residualise",
]
