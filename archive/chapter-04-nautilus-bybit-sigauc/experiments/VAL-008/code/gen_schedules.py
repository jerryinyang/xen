"""VAL-008 schedule generator — design.md §5 arms, fenced TRAIN reads only.

Regenerable byte-identically from (seed, bar calendar): deterministic numpy Generator per
seed; parquet written with fixed column order + zstd level pinned. QA regeneration check
diffs sha256 against schedules/manifest.json (L-19 D1 pattern).

Schedules (per symbol; ts_ns = decision-bar ts_event; target applied on that bar's close,
fill at next bar open):
  BASELINE-SHUF-s{0..4}: causal SMA(20/100) sig series, block-permuted (240-bar blocks),
                         emitted as target-change rows (flip occupancy preserved).
  LEAK:      at each BASELINE cross bar t: target=sign(Open[t+2]-Open[t+1]) for one bar.
  LEAK-SHUF-s{0..4}: LEAK slot directions block-permuted across slots (240-slot blocks).
  LEAK-LAG1: same slots, causalized direction sign(Open[t]-Open[t-1]).

DEVIATIONS: none.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[3]  # python/
sys.path.insert(0, str(ROOT / "src"))

from nautilus_trader.persistence.catalog import ParquetDataCatalog  # noqa: E402

from xen.nautilus.catalog_fence import fenced_bar_query, load_fence_manifest  # noqa: E402

SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
WIN_START = datetime(2023, 6, 1, tzinfo=timezone.utc)
FAST, SLOW = 20, 100
BLOCK = 240
SEEDS = (0, 1, 2, 3, 4)
OUT_DIR = Path(__file__).resolve().parent / "schedules"
CATALOG_PATH = ROOT.parent / "data" / "catalog"


def load_window_bars(symbol: str) -> pl.DataFrame:
    """Fenced TRAIN read → frame(ts_ns, open, close) sorted."""
    fence = load_fence_manifest()
    catalog = ParquetDataCatalog(str(CATALOG_PATH))
    bars = fenced_bar_query(
        catalog,
        [f"{symbol}-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL"],
        start=WIN_START,
        end=fence.train_end_utc,
        band="TRAIN",
    )
    return pl.DataFrame(
        {
            "ts_ns": [b.ts_event for b in bars],
            "open": [float(b.open) for b in bars],
            "close": [float(b.close) for b in bars],
        }
    ).sort("ts_ns")


def causal_sig(close: np.ndarray) -> np.ndarray:
    """SMA(20/100) sign per bar; 0 during warmup. Uses data <= t only."""
    n = len(close)
    sig = np.zeros(n, dtype=np.int8)
    csum = np.concatenate([[0.0], np.cumsum(close)])
    for t in range(SLOW - 1, n):
        fast = (csum[t + 1] - csum[t + 1 - FAST]) / FAST
        slow = (csum[t + 1] - csum[t + 1 - SLOW]) / SLOW
        sig[t] = 1 if fast > slow else -1
    return sig


def block_permute(values: np.ndarray, seed: int, block: int) -> np.ndarray:
    """Derangement block permute; deterministic per seed (AMENDMENT-4).

    A plain permutation keeps E[1] fixed block (~5.6% of slots at 18 blocks) of TRUE
    alignment, leaking plant signal into the destroy arm (observed collapse 0.87 on
    fixed-point seeds). Resample until no block maps to itself.
    """
    n = len(values)
    idx = np.arange(0, n, block)
    n_blocks = len(idx)
    rng = np.random.default_rng(seed)
    order = rng.permutation(n_blocks)
    while (order == np.arange(n_blocks)).any():
        order = rng.permutation(n_blocks)
    out = np.concatenate([values[idx[i]: idx[i] + block] for i in order])
    return out[:n]


def target_changes(ts_ns: np.ndarray, targets: np.ndarray) -> pl.DataFrame:
    """Compress a per-bar target series to change rows (ts_ns, target)."""
    prev = np.concatenate([[np.int8(0)], targets[:-1]])
    mask = targets != prev
    return pl.DataFrame(
        {"ts_ns": ts_ns[mask].astype(np.int64), "target": targets[mask].astype(np.int8)}
    )


def oneshot_rows(ts_ns: np.ndarray, slot_idx: np.ndarray, dirs: np.ndarray) -> pl.DataFrame:
    """Per-bar target series for 1-bar-hold slots (slot dir overrides the zero row)."""
    targets = np.zeros(len(ts_ns), dtype=np.int8)
    targets[slot_idx] = dirs  # active on the bar AFTER the decision bar close = fill bar
    # zero rows land automatically at slot_idx+1 via change compression unless the next
    # slot is adjacent (then its dir wins — targets already carries it).
    return target_changes(ts_ns, targets)


def write_parquet(df: pl.DataFrame, path: Path) -> str:
    df.write_parquet(path, compression="zstd", compression_level=3)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, dict] = {}
    for sym in SYMBOLS:
        bars = load_window_bars(sym)
        ts = bars.get_column("ts_ns").to_numpy()
        opens = bars.get_column("open").to_numpy()
        close = bars.get_column("close").to_numpy()
        sig = causal_sig(close)

        # BASELINE cross slots: first valid signal bar excluded; sign changes after warmup.
        valid = np.where(sig != 0)[0]
        first = valid[0]
        cross_idx = np.array(
            [t for t in valid[1:] if sig[t] != sig[t - 1]], dtype=np.int64
        )
        # 1-bar-hold slots need t+2 to exist for the oracle direction.
        cross_idx = cross_idx[cross_idx + 2 < len(ts)]

        oracle_dir = np.sign(opens[cross_idx + 2] - opens[cross_idx + 1]).astype(np.int8)
        oracle_dir[oracle_dir == 0] = 1  # flat next bar → long (deterministic tie rule)
        lag1_dir = np.sign(opens[cross_idx] - opens[cross_idx - 1]).astype(np.int8)
        lag1_dir[lag1_dir == 0] = 1

        entries: dict[str, pl.DataFrame] = {
            "LEAK": oneshot_rows(ts, cross_idx, oracle_dir),
            "LEAK-LAG1": oneshot_rows(ts, cross_idx, lag1_dir),
        }
        for s in SEEDS:
            entries[f"LEAK-SHUF-s{s}"] = oneshot_rows(
                ts, cross_idx, block_permute(oracle_dir, seed=1000 + s, block=BLOCK)
            )
            shuf_sig = sig.copy()
            shuf_sig[first:] = block_permute(sig[first:], seed=2000 + s, block=BLOCK)
            entries[f"BASELINE-SHUF-s{s}"] = target_changes(ts, shuf_sig)

        stats = {
            "n_bars": int(len(ts)),
            "n_cross_slots": int(len(cross_idx)),
            "first_signal_idx": int(first),
        }
        for arm, df in entries.items():
            path = OUT_DIR / f"{sym}__{arm}.parquet"
            sha = write_parquet(df, path)
            manifest[path.name] = {
                "sha256": sha,
                "rows": df.height,
                "symbol": sym,
                "arm": arm,
                **stats,
            }
        print(f"{sym}: bars={len(ts)} cross_slots={len(cross_idx)}")

    (OUT_DIR / "manifest.json").write_text(
        json.dumps(
            {
                "generator": "gen_schedules.py",
                "window_start_utc": WIN_START.isoformat(),
                "fast": FAST,
                "slow": SLOW,
                "block": BLOCK,
                "shuffle_seeds_leak": [1000 + s for s in SEEDS],
                "shuffle_seeds_baseline": [2000 + s for s in SEEDS],
                "files": manifest,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"manifest → {OUT_DIR / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
