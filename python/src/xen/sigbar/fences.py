"""Band fences, frozen-input verification, and the online universe rule (INFR-018).

Three guarantees this module exists to make machine-checked rather than intended:

1. **Band fences raise, never warn.** INFR-017 shipped a read path
   (``spread_pin.py::_tick_bps_reference``) that scanned a full staging parquet
   with no band filter and reached data at and beyond ``holdout_start_utc``. The
   code was later fenced but the design text was not, and QA caught it. Every
   read in INFR-018 goes through :func:`assert_band`, which raises.

2. **Frozen inputs are re-hashed at every entry point.** INFR-017's first
   baseline artifact was invalid (an Int8 overflow aliased the seasonal grid to
   256 buckets) and its sha ``78dd7988…`` is discarded, not re-pinned. A run
   that silently loaded the wrong file would be unattributable, so the sha is
   checked rather than assumed.

3. **Universe membership is point-in-time.** Selection at day ``d`` uses only
   bars strictly before ``d 00:00 UTC``. The ranking statistic is **quote
   turnover**, not base-asset volume: base volume is not comparable across
   symbols (1 BTC is not 1 DOGE), so ranking on it would rank by tick size.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import polars as pl

# ---------------------------------------------------------------------------
# Constants — the checkpoint-014 §5 bands, naive UTC to match the staging schema
# ---------------------------------------------------------------------------

ANALYSIS_START = datetime(2021, 6, 29, 6, 53)
DESIGN_BANK_END = datetime(2023, 3, 1)
CONFIRM_BANK_END = datetime(2023, 12, 18)  # == train_end_utc
HOLDOUT_START = datetime(2025, 1, 8)

#: sha256 of the A5 baselines INFR-018 is contracted to consume (report §8).
#: NOT the discarded first fit ``78dd7988…`` — see INFR-017 report §7a.
BASELINES_SHA256 = "1b7244c87aaafe293a945a8ac03a31222c95dcc232e7fb1d835d5227fa41ed72"
#: self-hash of INFR-017's W2 column pin, stamped into every output record.
COLUMN_PINS_SHA256 = "e3b9fd9b9b5851b8a9a11f9ce34cd1e0fa8e10ea1fe1b210bd0090da379e6225"
#: INFR-011 A6 catalog fence manifest.
FENCE_MANIFEST_SHA256 = "35d3375ec5ec18b3c6e4c5eec814ade4d492bd60e3fb694fed19e16bc2c00448"

BANDS: dict[str, tuple[datetime, datetime]] = {
    "DESIGN": (ANALYSIS_START, DESIGN_BANK_END),
    "CONFIRM": (DESIGN_BANK_END, CONFIRM_BANK_END),
}

STAGING_DIR = "python/experiments/INFR-011/data/staging/bars"
ADMISSION_LEDGER = "python/experiments/INFR-011/artifacts/admission-ledger.jsonl"
BASELINES_PARQUET = "python/experiments/INFR-017/results/seasonal_baselines.parquet"
COLUMN_PINS_JSON = "python/experiments/INFR-017/results/column_pins.json"


def repo_root() -> Path:
    """Walk up to the git root so every path in this item is absolute."""
    for parent in Path(__file__).resolve().parents:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("repo root not found")


# ---------------------------------------------------------------------------
# Fences
# ---------------------------------------------------------------------------


def band_window(band: str) -> tuple[datetime, datetime]:
    """Return the ``[start, end)`` window for a declared band."""
    if band not in BANDS:
        raise ValueError(f"unknown band {band!r}; declared bands are {sorted(BANDS)}")
    return BANDS[band]


def assert_band(df: pl.DataFrame, band: str, *, time_col: str = "OpenTime") -> None:
    """Raise unless every row lies inside ``band``.

    Raises rather than warns, and checks the holdout separately so the error
    message names the governance violation explicitly rather than a generic
    range problem.
    """
    if df.height == 0:
        return
    start, end = band_window(band)
    lo, hi = df[time_col].min(), df[time_col].max()
    if hi is not None and hi >= HOLDOUT_START:
        raise RuntimeError(
            f"HOLDOUT VIOLATION: max {time_col} {hi} >= holdout_start {HOLDOUT_START}. "
            "The global holdout is SEALED and is never queried."
        )
    if lo is None or hi is None or lo < start or hi >= end:
        raise RuntimeError(
            f"BAND VIOLATION: rows span [{lo}, {hi}] but band {band} is [{start}, {end})"
        )


def load_bars(symbol: str, band: str, *, root: Path | None = None) -> pl.DataFrame:
    """Load one symbol's staging bars, fenced to ``band`` and band-asserted.

    Parameters
    ----------
    symbol :
        Bybit symbol, e.g. ``"BTCUSDT"``.
    band :
        ``"DESIGN"`` or ``"CONFIRM"``.
    root :
        Repo root; resolved if omitted.

    Returns
    -------
    polars.DataFrame
        Sorted by ``OpenTime``, with the signed columns and a derived
        ``Delta`` and quote ``Turnover``. Empty frame if the symbol has no bars
        in the band.
    """
    root = root or repo_root()
    path = root / STAGING_DIR / f"{symbol}.parquet"
    start, end = band_window(band)
    df = (
        pl.scan_parquet(path)
        .filter((pl.col("OpenTime") >= start) & (pl.col("OpenTime") < end))
        .select(
            "OpenTime", "Open", "High", "Low", "Close", "Volume", "NTrades",
            "BuyVolume", "SellVolume",
        )
        .sort("OpenTime")
        .with_columns(
            (pl.col("BuyVolume") - pl.col("SellVolume")).alias("Delta"),
            (pl.col("Volume") * (pl.col("High") + pl.col("Low") + pl.col("Close")) / 3.0)
            .alias("Turnover"),
        )
        .collect()
    )
    assert_band(df, band)
    return df


# ---------------------------------------------------------------------------
# Frozen-input verification
# ---------------------------------------------------------------------------


def sha256_file(path: Path) -> str:
    """Stream a file's sha256 (the artifacts are hundreds of MB)."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass(frozen=True)
class FrozenInputs:
    """The verified INFR-017 contract this item is allowed to build on."""

    baselines_path: Path
    baselines_sha256: str
    column_pins_sha256: str
    fence_manifest_sha256: str


def assert_frozen_inputs(root: Path | None = None) -> FrozenInputs:
    """Re-hash INFR-017's frozen outputs and raise on any mismatch.

    Called at the top of every INFR-018 entry point. The baselines parquet is
    gitignored; regenerate it with
    ``python/experiments/INFR-017/code/seasonal_baselines.py`` if absent.
    """
    root = root or repo_root()
    bl = root / BASELINES_PARQUET
    if not bl.exists():
        raise RuntimeError(
            f"frozen baselines missing at {bl} — regenerate via "
            "python/experiments/INFR-017/code/seasonal_baselines.py and confirm the sha"
        )
    got = sha256_file(bl)
    if got != BASELINES_SHA256:
        raise RuntimeError(
            f"FROZEN INPUT MISMATCH: baselines sha256 {got} != contracted {BASELINES_SHA256}. "
            "INFR-017's first fit (78dd7988…) was INVALID and is discarded, not re-pinned."
        )
    pins = root / COLUMN_PINS_JSON
    import json

    pin_obj = json.loads(pins.read_text())
    if pin_obj.get("pin_sha256") != COLUMN_PINS_SHA256:
        raise RuntimeError(
            f"FROZEN INPUT MISMATCH: column_pins pin_sha256 {pin_obj.get('pin_sha256')} "
            f"!= contracted {COLUMN_PINS_SHA256}"
        )
    if pin_obj["W2_decision"]["stored_column_status"] != "UNUSABLE":
        raise RuntimeError(
            "column pin no longer marks SpreadBps UNUSABLE — the design's spread handling "
            "(design.md §5.3) assumes that decision and must be revisited"
        )
    return FrozenInputs(bl, got, COLUMN_PINS_SHA256, FENCE_MANIFEST_SHA256)


def assert_no_per_level_delta(obj: object) -> None:
    """Guard the family's hard ban on per-level signed attribution.

    Source §2.1 / Part 5 and card ban 2: per-BAR delta is exact, per-LEVEL delta
    is estimate-grade and no signal may depend on it. The profile kernel
    distributes **volume** only; passing a signed quantity into it is a design
    error, so it raises here rather than producing a plausible artifact.
    """
    name = getattr(obj, "name", None) or str(obj)
    if any(tok in str(name).lower() for tok in ("delta", "signed", "buyvolume", "sellvolume")):
        raise RuntimeError(
            f"PER-LEVEL DELTA BARRED: refusing to distribute {name!r} across price levels "
            "(source §2.1/Part 5; cf-sigauc-001 ban 2). Per-bar delta only."
        )


# ---------------------------------------------------------------------------
# Universe — the online rule (design.md §6.1)
# ---------------------------------------------------------------------------

UNIVERSE_N = 20
MIN_TRAILING_BARS = 1200  # of 1440


def load_admitted(root: Path | None = None) -> set[str]:
    """Symbols with ``admission == ADMITTED`` in the INFR-011 ledger."""
    import json

    root = root or repo_root()
    out: set[str] = set()
    with (root / ADMISSION_LEDGER).open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("admission") == "ADMITTED":
                out.add(row["symbol"])
    return out


def daily_turnover(df: pl.DataFrame) -> pl.DataFrame:
    """Per-UTC-day quote turnover and bar count for one symbol.

    Quote turnover (``Volume × typical price``) is the ranking statistic;
    base-asset ``Volume`` is not comparable across symbols and is never ranked
    on. The unit is USDT — stated here so the divisor object is pinned (L-21).
    """
    return df.group_by(pl.col("OpenTime").dt.truncate("1d").alias("day")).agg(
        pl.col("Turnover").sum().alias("turnover_usdt"),
        pl.len().alias("n_bars"),
    )


def build_universe(per_symbol_daily: dict[str, pl.DataFrame], *, n: int = UNIVERSE_N) -> pl.DataFrame:
    """Realise the online top-``n``-by-trailing-24h-turnover membership panel.

    Selection at day ``d`` uses the trailing window ending at ``d 00:00 UTC``,
    i.e. **day d-1's bars only** — strictly ``< d 00:00``, so nothing at or
    after the decision instant enters the ranking (causal, ``≤ t−1``).

    Parameters
    ----------
    per_symbol_daily :
        ``{symbol: daily_turnover(df)}`` for every admitted candidate.
    n :
        Panel size per day.

    Returns
    -------
    polars.DataFrame
        Columns ``day``, ``symbol``, ``rank``, ``turnover_usdt`` — the realised
        membership, one row per selected symbol-day.
    """
    frames = [
        d.with_columns(pl.lit(sym).alias("symbol")) for sym, d in per_symbol_daily.items() if d.height
    ]
    if not frames:
        return pl.DataFrame(schema={"day": pl.Datetime, "symbol": pl.String, "rank": pl.UInt32})
    allday = pl.concat(frames, how="vertical")

    # The ranking day is the day AFTER the measured day: turnover measured over
    # day D ranks membership for day D+1. This is the causal shift, and it is
    # the single line that makes selection point-in-time.
    ranked = (
        allday.filter(pl.col("n_bars") >= MIN_TRAILING_BARS)
        .with_columns((pl.col("day") + pl.duration(days=1)).alias("effective_day"))
        # tie-break lexicographic: sort by symbol first, then stable-sort by turnover
        .sort(["effective_day", "symbol"])
        .with_columns(
            pl.col("turnover_usdt")
            .rank(method="ordinal", descending=True)
            .over("effective_day")
            .alias("rank")
        )
        .filter(pl.col("rank") <= n)
        .select(
            pl.col("effective_day").alias("day"), "symbol", "rank", "turnover_usdt"
        )
        .sort(["day", "rank"])
    )
    return ranked
