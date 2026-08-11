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
    StreamingEmissionSource,
    write_emission_v1,
    write_emission_v1_from_paths,
    load_emission_v1,
)
from xen.nautilus.streaming import (
    BoundedJsonlWriter,
    BoundedParquetWriter,
    MemoryBudgetExceeded,
    MemoryGuard,
    MemorySample,
    OversizedRowError,
)
from xen.nautilus.adjudication_shim import (
    emission_to_adjudication_frames,
    adjudicate_emission,
)
from xen.nautilus.universe_selection import (
    SelectionRule,
    build_membership_series,
    rank_from_volume_panel,
    rebalance_schedule,
    rule_hash,
    select_membership,
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
    "StreamingEmissionSource",
    "write_emission_v1",
    "write_emission_v1_from_paths",
    "load_emission_v1",
    "BoundedJsonlWriter",
    "BoundedParquetWriter",
    "MemoryBudgetExceeded",
    "MemoryGuard",
    "MemorySample",
    "OversizedRowError",
    "emission_to_adjudication_frames",
    "adjudicate_emission",
    "SelectionRule",
    "build_membership_series",
    "rank_from_volume_panel",
    "rebalance_schedule",
    "rule_hash",
    "select_membership",
]
