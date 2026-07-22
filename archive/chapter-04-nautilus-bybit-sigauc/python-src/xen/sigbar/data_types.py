"""The :class:`SignedBar` Nautilus data contract (INFR-017 W5).

Subclasses ``nautilus_trader.core.data.Data`` via ``@customdataclass``, which
generates dict/msgpack/arrow codecs and registers the type with the
serialization layer, so instances write into and read back from a
``ParquetDataCatalog`` and can be subscribed to by strategies like native data
(same mechanism as :mod:`xen.orderflow.data_types`, INFR-013).

Field semantics (source ``SIGNAL-SIGNED.md`` Part 1):

- ``buy_volume`` / ``sell_volume`` — taker-side split. Bybit's archive ``side``
  column is the **aggressor** side; this is tested at INFR-017 W1 and the
  evidence is emitted to ``results/a8_provenance_audit.json`` under
  ``aggressor_side_convention`` (side-vs-tickDirection cross-tab). Cite that
  artifact, not this docstring. ``buy_volume + sell_volume == volume`` by
  construction.
- ``delta`` = ``buy_volume - sell_volume`` — **P2: a measurement, not an
  estimate**. Exact as a *bar aggregate* only; per-level attribution is barred
  (A3 / Part 5) and no field here supports it.
- ``spread_feature`` — the W2-pinned liquidity feature. Carries its own
  ``spread_status`` because the INFR-011 ``SpreadBps`` column was found not to
  be a spread (negative in 32.4% of BTC and 39.9% of ETH TRAIN minutes — see
  ``results/column_pins.json`` for the measured per-symbol rates). Consumers
  must branch on the status rather than assume the number is a spread.

Causality: ``ts_event`` is the bar **close** (the instant every field becomes
known). Consumers apply the programme's ``<= t-1`` rule; nothing in this record
is forward-looking.
"""

from nautilus_trader.core.data import Data
from nautilus_trader.model.custom import customdataclass
from nautilus_trader.model.identifiers import InstrumentId

# Bump on ANY change to field semantics or the derivation pipeline.
SIGBAR_PIPELINE_VERSION = "sigbar-0.1.0"

_NULL_INSTRUMENT = InstrumentId.from_str("NULL-LINEAR.BYBIT")

# spread_feature status values (W2 pin).
SPREAD_OK = "OK"  # a validated spread estimate in bps
SPREAD_UNUSABLE = "UNUSABLE"  # stored column is not a spread; do not cost with it
SPREAD_MISSING = "MISSING"  # one-sided minute or absent input


@customdataclass
class SignedBar(Data):
    """One minute of signed auction data (INFR-017 W5, source Part 1 P1-P4/P6)."""

    instrument_id: InstrumentId = _NULL_INSTRUMENT
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0
    buy_volume: float = 0.0  # taker-buy (aggressor lifted the ask)
    sell_volume: float = 0.0  # taker-sell (aggressor hit the bid)
    delta: float = 0.0  # buy_volume - sell_volume (exact, bar-aggregate only)
    n_trades: int = 0  # participation count; avg trade size = volume / n_trades
    spread_feature: float = 0.0  # W2-pinned liquidity feature, bps
    spread_status: str = SPREAD_MISSING
    pipeline_version: str = SIGBAR_PIPELINE_VERSION
    config_hash: str = ""  # sha256 of the W2 column pin this record was built under
