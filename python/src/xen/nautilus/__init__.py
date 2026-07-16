"""NautilusTrader engine foundation (INFR-010 Phase B).

Hard-pinned package: ``nautilus_trader==1.230.0`` (see ``python/pyproject.toml``).
One-platform rule (INFR-007 caveat): pin recorded for the host that ran Phase B.
"""

from __future__ import annotations

from xen.nautilus.instrument_ids import (
    VENUE,
    PRODUCT_TYPE,
    archive_symbol_to_instrument_id,
    archive_symbol_to_instrument_id_str,
    instrument_id_to_archive_symbol,
    parse_instrument_id_str,
)
from xen.nautilus.emission import (
    EMISSION_CONTRACT_VERSION,
    EmissionPaths,
    write_emission_v1,
    load_emission_v1,
)
from xen.nautilus.adjudication_shim import (
    emission_to_adjudication_frames,
    adjudicate_emission,
)

__all__ = [
    "VENUE",
    "PRODUCT_TYPE",
    "archive_symbol_to_instrument_id",
    "archive_symbol_to_instrument_id_str",
    "instrument_id_to_archive_symbol",
    "parse_instrument_id_str",
    "EMISSION_CONTRACT_VERSION",
    "EmissionPaths",
    "write_emission_v1",
    "load_emission_v1",
    "emission_to_adjudication_frames",
    "adjudicate_emission",
]
