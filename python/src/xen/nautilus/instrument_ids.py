"""Archive-symbol ↔ Nautilus ``InstrumentId`` mapping (INFR-010 Phase B).

Convention (pinned, matches Nautilus Bybit adapter + census naming):

* Bybit trades-archive folder / raw symbol: ``BTCUSDT`` (INFR-011 census).
* Nautilus instrument id string: ``BTCUSDT-LINEAR.BYBIT``
  - symbol component: ``{archive_symbol}-LINEAR``
  - venue component: ``BYBIT``
* Product type is always USDT linear perpetual (design D3). Spot / inverse / USDC
  ``*PERP`` / dated futures are out of scope and rejected by the helpers.

Example::

    archive_symbol_to_instrument_id_str("BTCUSDT")
    # → "BTCUSDT-LINEAR.BYBIT"
    instrument_id_to_archive_symbol("BTCUSDT-LINEAR.BYBIT")
    # → "BTCUSDT"
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nautilus_trader.model.identifiers import InstrumentId

VENUE = "BYBIT"
PRODUCT_TYPE = "LINEAR"
_ARCHIVE_SYMBOL_RE = re.compile(r"^[A-Z0-9]+USDT$")
_INSTRUMENT_ID_RE = re.compile(r"^([A-Z0-9]+USDT)-LINEAR\.BYBIT$")


def archive_symbol_to_instrument_id_str(archive_symbol: str) -> str:
    """Map a Bybit trades-archive symbol (e.g. ``BTCUSDT``) to Nautilus id string.

    Parameters
    ----------
    archive_symbol :
        Uppercase archive folder name ending in ``USDT``.

    Returns
    -------
    str
        ``{archive_symbol}-LINEAR.BYBIT``.
    """
    sym = archive_symbol.strip().upper()
    if not _ARCHIVE_SYMBOL_RE.match(sym):
        raise ValueError(
            f"archive symbol must match *USDT linear perp pattern, got {archive_symbol!r}"
        )
    return f"{sym}-{PRODUCT_TYPE}.{VENUE}"


def archive_symbol_to_instrument_id(archive_symbol: str) -> InstrumentId:
    """Map archive symbol to a Nautilus ``InstrumentId`` instance."""
    from nautilus_trader.model.identifiers import InstrumentId

    return InstrumentId.from_str(archive_symbol_to_instrument_id_str(archive_symbol))


def parse_instrument_id_str(instrument_id: str) -> tuple[str, str, str]:
    """Parse ``BTCUSDT-LINEAR.BYBIT`` → ``(archive_symbol, product_type, venue)``."""
    m = _INSTRUMENT_ID_RE.match(instrument_id.strip().upper())
    if not m:
        raise ValueError(
            f"instrument id must match '{{SYM}}USDT-LINEAR.BYBIT', got {instrument_id!r}"
        )
    return m.group(1), PRODUCT_TYPE, VENUE


def instrument_id_to_archive_symbol(instrument_id: str) -> str:
    """Inverse of :func:`archive_symbol_to_instrument_id_str`."""
    archive, _, _ = parse_instrument_id_str(instrument_id)
    return archive
