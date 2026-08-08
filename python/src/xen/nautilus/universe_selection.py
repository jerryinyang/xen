"""Point-in-time universe membership (INFR-014 WP0).

Causal top-n selection on trailing volume (or declared metric) with rebalance
schedule, optional hysteresis, and rule_hash for universe manifests.

Causality: at asof_ts only bars with ts_event ≤ asof_ts − 1 ns enter the metric
window (last closed 1m bar strictly before asof). Future volume cannot affect rank.
All catalog reads go through xen.nautilus.catalog_fence (HOLDOUT refused).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Sequence

import polars as pl

from xen.nautilus.catalog_fence import FenceManifest, FenceViolation, assert_within_fence, band_bounds

NS = 1_000_000_000
# ε: strictly before asof (design §9.1)
_ASOF_EPS_NS = 1


@dataclass(frozen=True)
class SelectionRule:
    """Point-in-time membership rule — pin via :func:`rule_hash` into manifests."""

    n: int = 10
    metric: str = "trailing_volume"  # trailing sum of 1m volume over window_bars
    window_bars: int = 1440  # 24h at 1m
    rebalance: str = "1d"
    rebalance_tz: str = "UTC"
    rebalance_time: str = "00:00"
    hysteresis_rank: int = 0  # 0 = pure top-n; keep prior if rank ≤ n+h
    pool: str = "admitted_listed"  # or "admitted_pit_incl_delisted"
    causal: bool = True
    tie_break: str = "lexicographic_id"


class UniverseSelectionError(RuntimeError):
    """Integrity / API failure in universe selection."""


def rule_hash(rule: SelectionRule) -> str:
    """Canonical JSON sha256 of rule fields (key order independent)."""
    blob = json.dumps(asdict(rule), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _to_ns(ts: datetime | int | float) -> int:
    if isinstance(ts, (int, float)):
        return int(ts)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return int(ts.timestamp() * 1e9)


def _asof_cutoff_ns(asof_ts: datetime | int | float) -> int:
    """Last admissible event timestamp: strictly before asof (≤ asof − 1 ns)."""
    return _to_ns(asof_ts) - _ASOF_EPS_NS


def _parse_hhmm(s: str) -> tuple[int, int]:
    parts = s.split(":")
    if len(parts) != 2:
        raise UniverseSelectionError(f"rebalance_time must be HH:MM, got {s!r}")
    return int(parts[0]), int(parts[1])


def rebalance_schedule(
    start: datetime,
    end: datetime,
    rule: SelectionRule,
) -> list[datetime]:
    """UTC rebalance timestamps in [start, end] inclusive on the rebalance grid."""
    if rule.rebalance != "1d":
        raise UniverseSelectionError(f"unsupported rebalance cadence {rule.rebalance!r}")
    hh, mm = _parse_hhmm(rule.rebalance_time)
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    # first grid at or after start
    cur = start.astimezone(timezone.utc).replace(hour=hh, minute=mm, second=0, microsecond=0)
    if cur < start:
        cur = cur + timedelta(days=1)
    out: list[datetime] = []
    while cur <= end:
        out.append(cur)
        cur = cur + timedelta(days=1)
    return out


def rank_from_volume_panel(
    volume_panel: pl.DataFrame,
    rule: SelectionRule,
    *,
    asof_ts: datetime | int | float,
    prior_membership: Sequence[str] | None = None,
) -> pl.DataFrame:
    """Rank instruments by trailing volume ending ≤ asof−ε.

    Parameters
    ----------
    volume_panel :
        Columns ``instrument_id`` (Utf8), ``ts_event`` (Int64 ns), ``volume`` (Float64).
    rule :
        Selection rule (metric must be trailing_volume).
    asof_ts :
        Selection instant; metric uses only bars strictly before this timestamp.
    prior_membership :
        Previous membership (for hysteresis); optional.

    Returns
    -------
    pl.DataFrame
        Columns: rank, instrument_id, metric_value (exactly ``rule.n`` rows when pool ≥ n).
    """
    if rule.metric != "trailing_volume":
        raise UniverseSelectionError(f"unsupported metric {rule.metric!r}")
    if not rule.causal:
        raise UniverseSelectionError("causal=False is forbidden — PIT selection only")
    if rule.tie_break != "lexicographic_id":
        raise UniverseSelectionError(f"unsupported tie_break {rule.tie_break!r}")
    if volume_panel is None or volume_panel.height == 0:
        return pl.DataFrame(
            schema={"rank": pl.Int64, "instrument_id": pl.Utf8, "metric_value": pl.Float64}
        )

    cutoff = _asof_cutoff_ns(asof_ts)
    # window: last window_bars bars at 1m → window length = window_bars minutes
    window_ns = int(rule.window_bars) * 60 * NS
    window_start = cutoff - window_ns + 1  # inclusive lower bound on ts_event

    req = {"instrument_id", "ts_event", "volume"}
    missing = req - set(volume_panel.columns)
    if missing:
        raise UniverseSelectionError(f"volume_panel missing columns {sorted(missing)}")

    panel = volume_panel.filter(
        (pl.col("ts_event") >= window_start) & (pl.col("ts_event") <= cutoff)
    )
    if panel.height == 0:
        return pl.DataFrame(
            schema={"rank": pl.Int64, "instrument_id": pl.Utf8, "metric_value": pl.Float64}
        )

    agg = (
        panel.group_by("instrument_id")
        .agg(pl.col("volume").sum().alias("metric_value"))
        .sort(["metric_value", "instrument_id"], descending=[True, False])
    )
    # pure top-n
    if rule.hysteresis_rank <= 0 or not prior_membership:
        top = agg.head(rule.n)
        return top.with_columns(pl.arange(1, top.height + 1).alias("rank")).select(
            "rank", "instrument_id", "metric_value"
        )

    # hysteresis: keep prior members while their rank ≤ n + h; fill remainder by pure rank
    h = int(rule.hysteresis_rank)
    rank_map = {str(r["instrument_id"]): i + 1 for i, r in enumerate(agg.iter_rows(named=True))}
    keep: list[str] = []
    for cid in prior_membership:
        rnk = rank_map.get(str(cid))
        if rnk is not None and rnk <= rule.n + h:
            keep.append(str(cid))
        if len(keep) >= rule.n:
            break
    selected = list(keep)
    for row in agg.iter_rows(named=True):
        cid = str(row["instrument_id"])
        if cid in selected:
            continue
        selected.append(cid)
        if len(selected) >= rule.n:
            break
    # stable order: by metric among selected
    sel_set = set(selected)
    ordered = agg.filter(pl.col("instrument_id").is_in(list(sel_set))).head(rule.n)
    # preserve selection order for equal ranks via re-sort metric then id
    ordered = ordered.sort(["metric_value", "instrument_id"], descending=[True, False])
    return ordered.with_columns(pl.arange(1, ordered.height + 1).alias("rank")).select(
        "rank", "instrument_id", "metric_value"
    )


def select_membership(
    catalog: Any,
    rule: SelectionRule,
    *,
    asof_ts: datetime | int | float,
    fence: FenceManifest,
    band: str = "TRAIN",
    instrument_ids: Sequence[str] | None = None,
    bar_type_suffix: str = "1-MINUTE-LAST-EXTERNAL",
    prior_membership: Sequence[str] | None = None,
    volume_panel: pl.DataFrame | None = None,
) -> pl.DataFrame:
    """Return n rows: rank, instrument_id, metric_value at asof under fence.

    If ``volume_panel`` is provided (tests / pre-materialized), catalog is unused for bars.
    Otherwise loads 1m bars for ``instrument_ids`` through the fence for the metric window.
    """
    if band == "HOLDOUT":
        raise FenceViolation("HOLDOUT reads are refused unconditionally")
    # asof must lie inside band (selection instant on sanctioned calendar)
    asof_dt = (
        asof_ts
        if isinstance(asof_ts, datetime)
        else datetime.fromtimestamp(_to_ns(asof_ts) / 1e9, tz=timezone.utc)
    )
    if asof_dt.tzinfo is None:
        asof_dt = asof_dt.replace(tzinfo=timezone.utc)
    lo, hi = band_bounds(fence, band)
    if asof_dt < lo or asof_dt > hi:
        raise FenceViolation(
            f"asof {asof_dt} outside sanctioned {band} band [{lo} .. {hi}]"
        )

    if volume_panel is not None:
        return rank_from_volume_panel(
            volume_panel, rule, asof_ts=asof_ts, prior_membership=prior_membership
        )

    if instrument_ids is None:
        raise UniverseSelectionError(
            "instrument_ids required when volume_panel is not supplied"
        )
    cutoff = _asof_cutoff_ns(asof_ts)
    window_ns = int(rule.window_bars) * 60 * NS
    start_ns = cutoff - window_ns + 1
    start_dt = datetime.fromtimestamp(start_ns / 1e9, tz=timezone.utc)
    end_dt = datetime.fromtimestamp(cutoff / 1e9, tz=timezone.utc)
    assert_within_fence(fence, start_dt, end_dt, band=band)

    rows: list[dict[str, Any]] = []
    for iid in instrument_ids:
        bar_type = f"{iid}-{bar_type_suffix}" if not iid.endswith(bar_type_suffix) else iid
        # Prefer fenced path when catalog exposes bars()
        bars = catalog.bars(bar_types=[bar_type], start=start_dt, end=end_dt)
        for b in bars:
            ts = int(getattr(b, "ts_event", 0))
            if ts > cutoff:
                continue  # belt-and-suspenders causality
            vol = float(getattr(b, "volume", 0.0))
            if hasattr(vol, "as_double"):
                vol = float(vol.as_double())
            rows.append({"instrument_id": str(iid), "ts_event": ts, "volume": vol})
    panel = pl.DataFrame(rows) if rows else pl.DataFrame(
        schema={"instrument_id": pl.Utf8, "ts_event": pl.Int64, "volume": pl.Float64}
    )
    return rank_from_volume_panel(
        panel, rule, asof_ts=asof_ts, prior_membership=prior_membership
    )


def build_membership_series(
    catalog: Any,
    rule: SelectionRule,
    *,
    start: datetime,
    end: datetime,
    fence: FenceManifest,
    band: str = "TRAIN",
    instrument_ids: Sequence[str] | None = None,
    volume_panel: pl.DataFrame | None = None,
) -> pl.DataFrame:
    """Long membership.parquet rows: rebalance_ts, instrument_id, rank, metric_value, rule_hash.

    Hysteresis carries prior membership across rebalance timestamps.
    """
    rh = rule_hash(rule)
    schedule = rebalance_schedule(start, end, rule)
    prior: list[str] | None = None
    parts: list[pl.DataFrame] = []
    for ts in schedule:
        mem = select_membership(
            catalog,
            rule,
            asof_ts=ts,
            fence=fence,
            band=band,
            instrument_ids=instrument_ids,
            volume_panel=volume_panel,
            prior_membership=prior,
        )
        if mem.height == 0:
            prior = []
            continue
        prior = mem.get_column("instrument_id").to_list()
        parts.append(
            mem.with_columns(
                pl.lit(int(ts.timestamp() * 1e9)).cast(pl.Int64).alias("rebalance_ts"),
                pl.lit(rh).alias("rule_hash"),
            ).select("rebalance_ts", "instrument_id", "rank", "metric_value", "rule_hash")
        )
    if not parts:
        return pl.DataFrame(
            schema={
                "rebalance_ts": pl.Int64,
                "instrument_id": pl.Utf8,
                "rank": pl.Int64,
                "metric_value": pl.Float64,
                "rule_hash": pl.Utf8,
            }
        )
    return pl.concat(parts)
