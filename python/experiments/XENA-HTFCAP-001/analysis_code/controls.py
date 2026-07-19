#!/usr/bin/env python3
"""XENA-HTFCAP-001 integrity controls (design §7–§8) — analysis stage scripts.

NOT a price backtest. Operates on already-emitted cis_trades / gate schedules.

1. RAND-SIGN-BATTERY (design §7, L-19): same entry timestamps, sign ~ Rademacher,
   25 seeds; report finalist percentile vs battery (expected ≥P95 if H true).
2. GATE-DERANGEMENT tripwire (design §8, L-28/L-19, AMENDMENT-2): block-derange gate-ON
   schedule on the 15m open grid (blocks ≥ 64 LTF bars = max H); zero fixed points
   code-asserted; re-adjudicate matched-horizon open-to-open bps. Seed battery (≥15
   derangements); BTC battery-MEDIAN collapse < 0.5 → HARD REJECT.

Usage (from python/, after emissions exist for a finalist cell):
  uv run python experiments/XENA-HTFCAP-001/analysis_code/controls.py \\
      --candidate BTCUSDT__DI_VOL_HI__v1.25__adxna__H16 \\
      --out experiments/XENA-HTFCAP-001/results/controls_smoke.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

CODE = Path(__file__).resolve().parents[1] / "code"
ROOT = Path(__file__).resolve().parents[3]  # python/
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(CODE))

from xen.nautilus.adjudication_shim import emission_to_adjudication_frames  # noqa: E402

UNIVERSE_ID = "XENA-HTFCAP-001"
RUNS_ROOT = REPO / "data" / "nautilus_runs" / UNIVERSE_ID
N_BATTERY_SEEDS = 25
BATTERY_SEED0 = 1000  # SPDR-006 RAND_SEEDS start
MIN_BLOCK_LTF = 64  # design §8: ≥ max hold H
BTC_COLLAPSE_HARD = 0.5  # design §8 HARD
N_DERANGE_SEEDS = 15  # design §8 AMENDMENT-2 (L-19): battery percentile, not a single twin
DERANGE_SEED0 = 7000  # derangement battery base seed


def make_derangement(n: int, rng: np.random.Generator) -> np.ndarray:
    """L-28: permutation with zero fixed points; regenerate if any fixed point."""
    if n <= 1:
        return np.arange(n)
    for _ in range(10_000):
        p = rng.permutation(n)
        if not np.any(p == np.arange(n)):
            return p
    return (np.arange(n) + 1) % n  # cycle fallback


def load_legs(candidate_id: str) -> pl.DataFrame:
    emission_dir = RUNS_ROOT / candidate_id
    if not (emission_dir / "run_metadata.json").exists():
        raise FileNotFoundError(f"no emission for {candidate_id}")
    _pos, cis, _meta = emission_to_adjudication_frames(emission_dir)
    live = cis.filter(
        pl.col("Censored").cast(pl.Boolean).not_() & pl.col("RealizedBps").is_finite()
    ).sort("EntryTime")
    if live.height == 0:
        raise RuntimeError(f"{candidate_id}: no completed legs")
    return live


def rand_sign_battery(legs: pl.DataFrame, *, n_seeds: int = N_BATTERY_SEEDS) -> dict[str, Any]:
    """25-seed Rademacher sign battery on fixed entry schedule; percentile of raw g."""
    d = legs.get_column("Direction").to_numpy().astype(float)
    ep = legs.get_column("EntryFillPrice").to_numpy().astype(float)
    xp = legs.get_column("ExitFillPrice").to_numpy().astype(float)
    raw = d * (xp - ep) / ep * 1e4
    raw_med = float(np.median(raw))
    battery_meds: list[float] = []
    for i in range(n_seeds):
        seed = BATTERY_SEED0 + i
        signs = np.random.default_rng(seed).choice(np.array([-1.0, 1.0]), size=len(raw))
        # destroy direction content; keep entry schedule and |path| magnitude
        g = signs * (np.abs(xp - ep) / ep * 1e4)
        battery_meds.append(float(np.median(g)))
    arr = np.asarray(battery_meds, dtype=float)
    # percentile of raw among battery (higher better for long-edge claim)
    rank = float(np.mean(arr <= raw_med))  # empirical CDF at raw
    return {
        "n_legs": int(len(raw)),
        "n_seeds": n_seeds,
        "raw_median_gross_bps": raw_med,
        "battery_median_gross_bps": battery_meds,
        "battery_p50": float(np.median(arr)),
        "battery_p95": float(np.quantile(arr, 0.95)),
        "raw_percentile_vs_battery": rank,
        "at_or_above_p95": bool(raw_med >= np.quantile(arr, 0.95)),
        "collapse_fraction": float(np.median(arr) / raw_med) if raw_med != 0 else float("nan"),
        "expected_if_H_true": "raw ≥ battery P95",
        "form": "Rademacher sign scramble; schedule fixed (B-1)",
    }


LTF_NS = 15 * 60 * 1_000_000_000  # 15m in ns
NS_PER_MIN = 60 * 1_000_000_000


def _build_15m_open_grid(marks: pl.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Contiguous 15m OPEN grid (boundary_ns, RealOpen) from 1-minute bar_marks.

    A 15m bar opening at boundary B has RealOpen = RealOpen of the 1m bar opening at B
    (i.e. the 1m bar closing at B + 1m). Boundaries with no first-minute bar (gaps) are
    dropped. The grid is the space the gate schedule and the block derangement live on.
    """
    m = marks.sort("SourceCloseTime")
    close_ns = m.get_column("SourceCloseTime").cast(pl.Datetime("ns")).cast(pl.Int64).to_numpy()
    real_open = m.get_column("RealOpen").to_numpy().astype(float)
    open_by_close = {int(c): float(o) for c, o in zip(close_ns, real_open)}
    # 15m open boundaries spanning the data
    one_min_open = close_ns - NS_PER_MIN
    boundaries = np.unique((one_min_open // LTF_NS) * LTF_NS)
    grid_ns, grid_open = [], []
    for b in boundaries:
        o = open_by_close.get(int(b) + NS_PER_MIN)  # first 1m of the 15m window
        if o is not None and np.isfinite(o) and o > 0:
            grid_ns.append(int(b))
            grid_open.append(float(o))
    return np.asarray(grid_ns, dtype=np.int64), np.asarray(grid_open, dtype=float)


def _deranged_median(
    entry_idx: np.ndarray,
    block_id: np.ndarray,
    block_edges: np.ndarray,
    n_blocks: int,
    n_grid: int,
    grid_open: np.ndarray,
    d: np.ndarray,
    hold_bars: np.ndarray,
    rng: np.random.Generator,
) -> tuple[float, bool]:
    """One derangement seed: remap block b → perm[b], reprice open-to-open, return median.

    Returns (deranged_median_gross_bps, zero_fixed_points_ok). Grid/block structure is built
    once by the caller; only the block permutation + repricing vary per seed.
    """
    perm = make_derangement(n_blocks, rng)
    ok = not np.any(perm == np.arange(n_blocks))
    assert ok, "L-28 derangement has fixed points"

    # deranged entry index: preserve within-block offset, remap block b → perm[b]
    deranged_idx = entry_idx.copy()
    for i, b in enumerate(block_id):
        src_lo, src_hi = int(block_edges[b]), int(block_edges[b + 1])
        dst_b = int(perm[b])
        dst_lo, dst_hi = int(block_edges[dst_b]), int(block_edges[dst_b + 1])
        src_len = max(1, src_hi - src_lo)
        dst_len = max(1, dst_hi - dst_lo)
        off = int(entry_idx[i] - src_lo)
        deranged_idx[i] = min(dst_lo + int(off * dst_len / src_len), n_grid - 2)

    der_rets = []
    for i in range(len(deranged_idx)):
        j0 = int(deranged_idx[i])
        j1 = min(j0 + int(hold_bars[i]), n_grid - 1)  # hold in 15m steps → matched horizon
        o0, o1 = grid_open[j0], grid_open[j1]
        if o0 <= 0 or not np.isfinite(o0) or not np.isfinite(o1):
            continue
        der_rets.append(float(d[i] * (o1 - o0) / o0 * 1e4))
    der = np.asarray(der_rets, dtype=float)
    return (float(np.median(der)) if der.size else float("nan")), ok


def gate_derangement(
    legs: pl.DataFrame,
    marks: pl.DataFrame,
    *,
    n_seeds: int = N_DERANGE_SEEDS,
    seed0: int = DERANGE_SEED0,
    min_block: int = MIN_BLOCK_LTF,
) -> dict[str, Any]:
    """Block-derange gate-ON entries on the **15m LTF open grid**; battery collapse read.

    Construction (design §8, QA-2 #10): the mark parquet is 1-minute; build the 15m OPEN
    grid first. Partition it into contiguous blocks of ≥ ``min_block`` **15m** bars
    (= max hold H = 64 ⇒ 16h ≥ hold, so a deranged entry cannot overlap its own leg),
    derange the block assignment (zero fixed points), and price the deranged leg over
    ``hold_bars`` **15m** steps on the same grid — matched entry/exit horizon.

    AMENDMENT-2 (L-19): the collapse read is a **seed-battery percentile**, not a single
    deranged twin. Draw ``n_seeds`` (≥15) independent derangements (each zero-fixed-point,
    code-asserted); report the collapse-fraction distribution and read the HARD gate off the
    battery **median** collapse (< 0.5 on BTC binding → REJECT).
    """
    et = legs.get_column("EntryTime").cast(pl.Datetime("ns"))
    d = legs.get_column("Direction").to_numpy().astype(float)
    hold_ns = (
        legs.get_column("ExitTime").cast(pl.Datetime("ns")).cast(pl.Int64)
        - et.cast(pl.Int64)
    ).to_numpy()
    # hold in 15m bars (exact for fixed-hold legs)
    hold_bars = np.maximum(1, np.rint(hold_ns / LTF_NS).astype(int))

    grid_ns, grid_open = _build_15m_open_grid(marks)
    n_grid = len(grid_ns)
    if n_grid < min_block * 2:
        return {"ok": False, "reason": f"15m grid too short n={n_grid} (< 2·{min_block})"}

    # entry indices on the 15m grid (entries are 15m-aligned → exact match)
    entry_ns = et.cast(pl.Int64).to_numpy()
    entry_idx = np.searchsorted(grid_ns, entry_ns, side="left")
    entry_idx = np.clip(entry_idx, 0, n_grid - 1)
    for i, e in enumerate(entry_ns):
        j = int(entry_idx[i])
        if j > 0 and abs(grid_ns[j - 1] - e) < abs(grid_ns[j] - e):
            entry_idx[i] = j - 1

    # contiguous blocks of >= min_block 15m bars
    n_blocks = max(2, n_grid // min_block)
    block_edges = np.linspace(0, n_grid, n_blocks + 1, dtype=int)
    block_id = np.clip(np.searchsorted(block_edges[1:], entry_idx, side="right"), 0, n_blocks - 1)

    raw = d * (
        legs.get_column("ExitFillPrice").to_numpy().astype(float)
        - legs.get_column("EntryFillPrice").to_numpy().astype(float)
    ) / legs.get_column("EntryFillPrice").to_numpy().astype(float) * 1e4
    raw_med = float(np.median(raw))

    # seed battery: one derangement + repricing per seed (L-19 percentile read)
    der_meds: list[float] = []
    collapses: list[float] = []
    all_zero_fixed = True
    for s in range(n_seeds):
        rng = np.random.default_rng(seed0 + s)
        der_med, ok = _deranged_median(
            entry_idx, block_id, block_edges, n_blocks, n_grid, grid_open, d, hold_bars, rng
        )
        all_zero_fixed = all_zero_fixed and ok
        der_meds.append(der_med)
        c = (
            1.0 - (der_med / raw_med)
            if raw_med != 0 and np.isfinite(der_med)
            else float("nan")
        )
        collapses.append(c)

    carr = np.asarray([c for c in collapses if np.isfinite(c)], dtype=float)
    # design: collapse fraction ≈ (raw - deranged) / raw; expected 0.8+ BTC.
    # HARD gate reads the battery MEDIAN collapse (percentile read, not one twin).
    med_collapse = float(np.median(carr)) if carr.size else float("nan")
    hard_fail = bool(np.isfinite(med_collapse) and med_collapse < BTC_COLLAPSE_HARD)

    def _q(p: float) -> float:
        return float(np.quantile(carr, p)) if carr.size else float("nan")

    return {
        "ok": True,
        "n_legs": int(len(raw)),
        "n_grid_15m": int(n_grid),
        "n_blocks": int(n_blocks),
        "min_block_ltf": min_block,
        "block_hours": float(min_block * 15 / 60.0),
        "max_hold_bars": int(hold_bars.max()) if len(hold_bars) else 0,
        "n_derange_seeds": int(n_seeds),
        "derangement_zero_fixed_points": bool(all_zero_fixed),
        "raw_median_gross_bps": raw_med,
        "deranged_median_gross_bps_battery": der_meds,
        "collapse_fraction_battery": [c if np.isfinite(c) else None for c in collapses],
        "collapse_median": med_collapse if np.isfinite(med_collapse) else None,
        "collapse_p05": _q(0.05) if carr.size else None,
        "collapse_p25": _q(0.25) if carr.size else None,
        "collapse_p75": _q(0.75) if carr.size else None,
        "collapse_p95": _q(0.95) if carr.size else None,
        "hard_block_threshold": BTC_COLLAPSE_HARD,
        "hard_fail_leak": hard_fail,
        "note": "HARD: battery-MEDIAN collapse < 0.5 on BTC binding → REJECT (design §8, AMENDMENT-2)",
        "form": (
            f"{n_seeds}-seed block-derangement battery on 15m open grid; "
            "matched-horizon open-to-open; percentile collapse read (L-19)"
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--seed", type=int, default=DERANGE_SEED0, help="derangement battery base seed")
    ap.add_argument("--n-derange-seeds", type=int, default=N_DERANGE_SEEDS)
    args = ap.parse_args()

    legs = load_legs(args.candidate)
    emission_dir = RUNS_ROOT / args.candidate
    pos, _cis, _meta = emission_to_adjudication_frames(emission_dir)

    battery = rand_sign_battery(legs)
    derange = gate_derangement(legs, pos, n_seeds=args.n_derange_seeds, seed0=args.seed)

    # symbol from candidate_id
    symbol = args.candidate.split("__")[0]
    hard_block = bool(symbol.startswith("BTC") and derange.get("hard_fail_leak"))

    report = {
        "universe_id": UNIVERSE_ID,
        "candidate_id": args.candidate,
        "symbol": symbol,
        "generated_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "rand_sign_battery": battery,
        "gate_derangement": derange,
        "integrity": {
            "hard_block_btc_derangement": hard_block,
            "rand_sign_battery_seeds": N_BATTERY_SEEDS,
            "derange_battery_seeds": int(args.n_derange_seeds),
            "derangement_L28": True,
            "derange_battery_L19": True,
        },
    }
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(f"WROTE {args.out}")
    print(text)
    if hard_block:
        print("HARD FAIL: BTC derangement collapse < 0.5 — leak REJECT class", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
