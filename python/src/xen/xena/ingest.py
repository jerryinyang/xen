"""XENA universe ingestion + blocking candidate gate (INFR-006 WS-1).

Adapts engine-emitted run directories (`data/strategy_runs/...`, the standard strategy-host
emission contract) into oracle `CandidateStream`s, behind a **blocking per-candidate gate** —
the XENA analogue of `xen.estimand_validation`: no candidate enters a universe without a
passing gate artifact.

Universe manifest (`universe_manifest.json`, one per universe root):

```json
{
  "universe_id": "XENA-001",
  "candidates": [
    {"candidate_id": "donch20_USTEC_m15", "run_dir": "donchian_USTEC_m15",
     "symbol": "USTEC", "cost_bps": 2.1, "money_per_unit": 1.0}
  ]
}
```

`run_dir` is relative to the manifest's directory (absolute allowed). Every candidate's run
dir must contain the standard emission: `run_metadata.json` (with `AnalysisEndUtc`),
`positions.parquet` (per-bar real OHLC → the mark grid), `cis_trades.parquet` (per-leg fills
→ the trade-intent ledger).

XENA emission contract additions over the base contract:
* every non-censored leg carries finite `EntryFillPrice`, `ExitFillPrice`, `RealizedBps`;
* every leg carries a finite `SlPrice` != entry fill — the engine-declared stop level.
  `StopDistance = |EntryFillPrice - SlPrice|` is the sizing denominator (`R_i / stop`);
  a candidate without engine-declared stops cannot be risk-sized and is REJECTED here.

Gate checks (all blocking):
  files / schema / non-empty · holdout fence (every emitted timestamp < AnalysisEndUtc) ·
  causality (entry < exit, entries inside the mark grid, marks strictly monotone) ·
  stop contract · fill self-consistency (`RealizedBps` reconciles with the fills, L-18) ·
  oracle smoke (single-candidate `evaluate` runs and reconciles bit-deterministically).
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from xen.xena.oracle import CandidateStream, OracleConfig, evaluate

MANIFEST_NAME = "universe_manifest.json"
GATE_ARTIFACT_NAME = "xena_candidate_gate.json"

REQUIRED_CIS_COLS = ("EntryTime", "ExitTime", "Direction", "EntryFillPrice",
                     "ExitFillPrice", "RealizedBps", "Censored", "SlPrice")
REQUIRED_POS_COLS = ("SourceCloseTime", "RealOpen")

REALIZED_BPS_TOL = 1.0  # engine self-consistency: |RealizedBps - fills-derived| per leg


# --------------------------------------------------------------------------- #
# money_per_unit (USD account) — item 6, INFR-006
# --------------------------------------------------------------------------- #
# FTMO USD-quoted non-forex instruments in the Xen universe. NOT USD-quoted (rate must
# be pinned): JP225 (JPY), EU50/GER40 (EUR), UK100 (GBP), HK50 (HKD), AUS200 (AUD).
USD_QUOTED_CFDS = frozenset({"USTEC", "US500", "US2000", "US30",
                             "XAUUSD", "XAGUSD", "BTCUSD"})


def xena_money_per_unit(symbol: str, *, quote_usd_rate: float | None = None) -> float:
    """Account-currency (USD) value of a 1.0 price-unit move on 1 unit of ``symbol``.

    The oracle's sizing denominator is ``stop_distance · money_per_unit``; getting this
    factor wrong mis-sizes every position of the candidate (an L-21-class unit seam).

    * XXXUSD forex (EURUSD…) and USD-quoted CFDs (indices/metals/crypto at FTMO): a 1.0
      price move on 1 unit is 1 USD → **1.0**.
    * USD-base and cross forex (USDJPY, EURJPY…), or any non-USD-quoted CFD: a 1.0 move
      is 1 unit of the QUOTE currency → factor = quote→USD rate, which MUST be pinned
      explicitly (same discipline as ``spread_pips`` / ``base_usd_rate`` in
      ``xen.evaluation``). Raises when required and absent — never silently 1.0.
    """
    sym = symbol.upper()
    if len(sym) == 6 and sym.isalpha() and sym[3:] == "USD":     # XXXUSD forex
        return 1.0
    if sym in USD_QUOTED_CFDS:                                    # USD-quoted non-forex
        return 1.0
    if quote_usd_rate is None:
        raise ValueError(
            f"{symbol}: not USD-quoted — pin quote_usd_rate (quote-currency→USD) "
            "explicitly before universe assembly; a silent 1.0 mis-sizes every "
            "position (L-21-class unit seam)")
    return float(quote_usd_rate)


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def _to_ns(col: pl.Expr) -> pl.Expr:
    return col.dt.cast_time_unit("ns").cast(pl.Int64)


def load_candidate(run_dir: str | Path, *, candidate_id: str, symbol: str, cost_bps: float,
                   money_per_unit: float = 1.0) -> CandidateStream:
    """Adapt one emitted run directory into an oracle ``CandidateStream``.

    Loading is permissive only about extra columns; every required column and the stop
    contract are enforced here (and again, with artifacts, in :func:`gate_candidate`).
    """
    run_path = Path(run_dir)
    pos = pl.read_parquet(run_path / "positions.parquet")
    cis = pl.read_parquet(run_path / "cis_trades.parquet")
    missing = [c for c in REQUIRED_POS_COLS if c not in pos.columns]
    if missing:
        raise ValueError(f"{candidate_id}: positions.parquet missing {missing}")
    missing = [c for c in REQUIRED_CIS_COLS if c not in cis.columns]
    if missing:
        raise ValueError(f"{candidate_id}: cis_trades.parquet missing {missing}")

    marks = (pos.sort("SourceCloseTime")
             .select(_to_ns(pl.col("SourceCloseTime")).alias("CloseTime"),
                     pl.col("RealOpen").cast(pl.Float64).alias("Open")))
    trades = (cis.sort("EntryTime")
              .select(_to_ns(pl.col("EntryTime")).alias("EntryTime"),
                      _to_ns(pl.col("ExitTime")).alias("ExitTime"),
                      pl.col("Direction").cast(pl.Float64),
                      pl.col("EntryFillPrice").cast(pl.Float64).alias("EntryPrice"),
                      pl.col("ExitFillPrice").cast(pl.Float64).alias("ExitPrice"),
                      (pl.col("EntryFillPrice") - pl.col("SlPrice")).abs()
                      .cast(pl.Float64).alias("StopDistance"),
                      pl.col("Censored").cast(pl.Boolean)))
    return CandidateStream(candidate_id, symbol, trades, marks, float(cost_bps),
                           float(money_per_unit))


def _read_metadata(run_dir: Path) -> dict[str, Any]:
    p = run_dir / "run_metadata.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _analysis_end_ns(metadata: dict[str, Any]) -> int | None:
    raw = metadata.get("AnalysisEndUtc") or metadata.get("analysis_end_utc")
    if raw is None:
        return None
    ts = pl.Series([raw]).str.to_datetime(time_unit="ns", time_zone=None)
    return int(ts.cast(pl.Int64)[0])


# --------------------------------------------------------------------------- #
# The blocking gate
# --------------------------------------------------------------------------- #
def gate_candidate(run_dir: str | Path, *, candidate_id: str, symbol: str, cost_bps: float,
                   money_per_unit: float = 1.0) -> dict[str, Any]:
    """Blocking per-candidate validation. Returns a report dict with ``blocking_pass``.

    Never raises for a *failing* candidate — failures are reported so a universe gate can
    enumerate them; raises only on I/O-level absence of the run itself.
    """
    run_path = Path(run_dir)
    checks: dict[str, dict[str, Any]] = {}

    def check(name: str, ok: bool, detail: str = "") -> bool:
        checks[name] = {"pass": bool(ok), "detail": detail}
        return bool(ok)

    report: dict[str, Any] = {"candidate_id": candidate_id, "run_dir": str(run_path),
                              "symbol": symbol, "checks": checks, "blocking_pass": False}

    # files + schema
    files_ok = check("files", (run_path / "positions.parquet").exists()
                     and (run_path / "cis_trades.parquet").exists(),
                     "positions.parquet + cis_trades.parquet required")
    if not files_ok:
        return report
    try:
        stream = load_candidate(run_path, candidate_id=candidate_id, symbol=symbol,
                                cost_bps=cost_bps, money_per_unit=money_per_unit)
        check("schema", True)
    except ValueError as e:
        check("schema", False, str(e))
        return report

    trades, marks = stream.trades, stream.marks
    check("non_empty", trades.height > 0 and marks.height >= 2,
          f"trades={trades.height} marks={marks.height}")

    # holdout fence: every emitted timestamp strictly before AnalysisEndUtc
    meta = _read_metadata(run_path)
    end_ns = _analysis_end_ns(meta)
    if end_ns is None:
        check("fence", False, "run_metadata.json missing AnalysisEndUtc")
    else:
        latest = max(int(marks.get_column("CloseTime").max() or 0),
                     int(trades.get_column("EntryTime").max() or 0),
                     int(trades.filter(pl.col("Censored").not_())
                         .get_column("ExitTime").max() or 0))
        check("fence", latest < end_ns,
              f"latest emitted ts {latest} vs AnalysisEndUtc {end_ns}")

    # causality: monotone unique marks; entries within grid; entry <= exit
    mt = marks.get_column("CloseTime").to_numpy()
    mono = bool(np.all(np.diff(mt) > 0))
    et = trades.get_column("EntryTime").to_numpy()
    xt = trades.get_column("ExitTime").to_numpy()
    cz = trades.get_column("Censored").to_numpy().astype(bool)
    inside = bool(len(mt) > 0 and (et >= mt[0]).all() and (et <= mt[-1]).all())
    ordered = bool(((xt >= et) | cz).all())
    check("causality", mono and inside and ordered,
          f"marks_monotone={mono} entries_in_grid={inside} entry<=exit={ordered}")

    # stop contract: finite, strictly positive stop distance on every leg
    sd = trades.get_column("StopDistance").to_numpy()
    check("stop_contract", bool(np.isfinite(sd).all() and (sd > 0).all()),
          "every leg needs finite SlPrice != EntryFillPrice (sizing denominator)")

    # fill self-consistency (L-18): engine RealizedBps reconciles with its own fills
    cis = pl.read_parquet(run_path / "cis_trades.parquet")
    live = cis.filter(pl.col("Censored").cast(pl.Boolean).not_()
                      & pl.col("RealizedBps").is_finite())
    if live.height:
        d = live.get_column("Direction").to_numpy().astype(float)
        ep = live.get_column("EntryFillPrice").to_numpy().astype(float)
        xp = live.get_column("ExitFillPrice").to_numpy().astype(float)
        rb = live.get_column("RealizedBps").to_numpy().astype(float)
        derived = d * (xp - ep) / ep * 1e4
        worst = float(np.max(np.abs(derived - rb)))
        check("fill_consistency", worst <= REALIZED_BPS_TOL,
              f"max |RealizedBps - fills-derived| = {worst:.4f} bps (tol {REALIZED_BPS_TOL})")
    else:
        check("fill_consistency", True, "no completed legs")

    # oracle smoke: single-candidate evaluation runs, reconciles, and is deterministic
    if all(c["pass"] for c in checks.values()):
        try:
            r1 = evaluate({candidate_id}, [stream], OracleConfig())
            r2 = evaluate({candidate_id}, [stream], OracleConfig())
            det = bool(np.array_equal(r1.equity, r2.equity) and r1.F_point == r2.F_point)
            check("oracle_smoke", det and math.isfinite(r1.F_point),
                  f"n_admitted={r1.n_admitted} n_rejected={r1.n_rejected} "
                  f"F_point={r1.F_point:.6g} deterministic={det}")
        except (ValueError, AssertionError) as e:
            check("oracle_smoke", False, str(e))
    else:
        check("oracle_smoke", False, "skipped: earlier check failed")

    report["blocking_pass"] = all(c["pass"] for c in checks.values())
    return report


# --------------------------------------------------------------------------- #
# Universe-level gate + loading
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Universe:
    universe_id: str
    streams: list[CandidateStream]
    manifest_path: Path


def gate_universe(manifest_path: str | Path, *, write_artifact: bool = True) -> dict[str, Any]:
    """Gate every manifest candidate; write ``xena_candidate_gate.json`` next to the manifest.

    ``blocking_pass`` is true only if EVERY candidate passes — a universe with any failing
    candidate must be fixed (or the candidate removed from the manifest), never silently
    thinned at load time.
    """
    mpath = Path(manifest_path)
    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    root = mpath.parent
    reports = []
    for c in manifest["candidates"]:
        rd = Path(c["run_dir"])
        reports.append(gate_candidate(rd if rd.is_absolute() else root / rd,
                                      candidate_id=c["candidate_id"], symbol=c["symbol"],
                                      cost_bps=c["cost_bps"],
                                      money_per_unit=c.get("money_per_unit", 1.0)))
    ids = [c["candidate_id"] for c in manifest["candidates"]]
    artifact = {"universe_id": manifest.get("universe_id", mpath.parent.name),
                "n_candidates": len(reports),
                "n_pass": sum(r["blocking_pass"] for r in reports),
                "duplicate_ids": sorted({i for i in ids if ids.count(i) > 1}),
                "candidates": reports}
    artifact["blocking_pass"] = (artifact["n_pass"] == artifact["n_candidates"]
                                 and artifact["n_candidates"] > 0
                                 and not artifact["duplicate_ids"])
    if write_artifact:
        (root / GATE_ARTIFACT_NAME).write_text(json.dumps(artifact, indent=1),
                                               encoding="utf-8")
    return artifact


def load_universe(manifest_path: str | Path) -> Universe:
    """Load all candidate streams; refuses without a passing gate artifact.

    The gate artifact must exist next to the manifest and record ``blocking_pass: true``
    for the CURRENT candidate set — rerun :func:`gate_universe` after any manifest change.
    """
    mpath = Path(manifest_path)
    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    gpath = mpath.parent / GATE_ARTIFACT_NAME
    if not gpath.exists():
        raise RuntimeError(f"no {GATE_ARTIFACT_NAME} next to manifest — run gate_universe first")
    gate = json.loads(gpath.read_text(encoding="utf-8"))
    if not gate.get("blocking_pass"):
        raise RuntimeError("universe gate is FAILING — fix or remove failing candidates")
    gated_ids = {r["candidate_id"] for r in gate.get("candidates", [])}
    manifest_ids = {c["candidate_id"] for c in manifest["candidates"]}
    if gated_ids != manifest_ids:
        raise RuntimeError("gate artifact is stale (candidate set changed) — rerun gate_universe")
    root = mpath.parent
    streams = []
    for c in manifest["candidates"]:
        rd = Path(c["run_dir"])
        streams.append(load_candidate(rd if rd.is_absolute() else root / rd,
                                      candidate_id=c["candidate_id"], symbol=c["symbol"],
                                      cost_bps=c["cost_bps"],
                                      money_per_unit=c.get("money_per_unit", 1.0)))
    return Universe(manifest.get("universe_id", root.name), streams, mpath)
