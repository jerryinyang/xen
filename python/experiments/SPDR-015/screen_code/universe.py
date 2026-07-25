"""Universe recompute + pin assertion (AMENDMENT-U1)."""
from __future__ import annotations

import json

import numpy as np
import pyarrow.parquet as pq
from tqdm import tqdm

from catalog_io import _decode_i128, available_symbols, symbol_dir
from config import (
    NS,
    UNIVERSE_METRIC,
    UNIVERSE_N,
    UNIVERSE_PIN_FAMILY,
    UNIVERSE_PIN_RESULTS,
    UNIVERSE_WINDOW_END,
    UNIVERSE_WINDOW_START,
)
from xen.nautilus.catalog_fence import assert_within_fence


class UniversePinMismatch(RuntimeError):
    """Recomputed top-N differs from the frozen family pin."""


def dollar_volume(symbol: str, lo_ns: int, hi_ns: int) -> tuple[float, int]:
    d = symbol_dir(symbol)
    if not d.exists():
        return 0.0, 0
    total, n = 0.0, 0
    for f in sorted(d.glob("*.parquet")):
        tbl = pq.read_table(
            f, columns=["ts_event", "close", "volume"],
            filters=[("ts_event", ">=", lo_ns), ("ts_event", "<", hi_ns)],
        )
        if tbl.num_rows == 0:
            continue
        ts = tbl.column("ts_event").combine_chunks().to_numpy().astype(np.int64)
        keep = (ts >= lo_ns) & (ts < hi_ns)
        if not keep.any():
            continue
        c = _decode_i128(tbl.column("close").combine_chunks())[keep]
        v = _decode_i128(tbl.column("volume").combine_chunks())[keep]
        total += float(np.sum(c * v))
        n += int(keep.sum())
    return total, n


def recompute_universe(manifest, *, progress: bool = True) -> dict:
    assert_within_fence(manifest, UNIVERSE_WINDOW_START, UNIVERSE_WINDOW_END, band="TRAIN")
    lo = int(UNIVERSE_WINDOW_START.timestamp() * NS)
    hi = int(UNIVERSE_WINDOW_END.timestamp() * NS)

    syms = available_symbols()
    it = tqdm(syms, desc="universe rank", disable=not progress)
    dv: dict[str, float] = {}
    nb: dict[str, int] = {}
    for s in it:
        total, n = dollar_volume(s, lo, hi)
        if n > 0:
            dv[s] = total
            nb[s] = n
    ranked = sorted(dv.items(), key=lambda kv: (-kv[1], kv[0]))
    top = [s for s, _ in ranked[:UNIVERSE_N]]
    return {
        "ranking_metric": UNIVERSE_METRIC,
        "asof_exclusive": UNIVERSE_WINDOW_END.isoformat(),
        "window_start_inclusive": UNIVERSE_WINDOW_START.isoformat(),
        "band": "TRAIN",
        "top_n": UNIVERSE_N,
        "n_symbols_scanned": len(syms),
        "n_symbols_with_data": len(dv),
        "symbols": top,
        "dollar_volume": {s: dv[s] for s in top},
        "n_bars": {s: nb[s] for s in top},
    }


def assert_pin(recomputed: dict) -> dict:
    pins = {}
    for name, path in (("family", UNIVERSE_PIN_FAMILY), ("results", UNIVERSE_PIN_RESULTS)):
        pins[name] = json.loads(path.read_text())["symbols"]

    got = set(recomputed["symbols"])
    report = {"recomputed": recomputed["symbols"], "checks": {}}
    for name, syms in pins.items():
        want = set(syms)
        ok = got == want
        report["checks"][name] = {
            "path": str(UNIVERSE_PIN_FAMILY if name == "family" else UNIVERSE_PIN_RESULTS),
            "set_equal": ok,
            "missing_from_recompute": sorted(want - got),
            "extra_in_recompute": sorted(got - want),
        }
        if not ok:
            raise UniversePinMismatch(
                f"top-{UNIVERSE_N} recompute != {name} pin: "
                f"missing={sorted(want - got)} extra={sorted(got - want)}"
            )
    report["set_equal_all"] = True
    return report
