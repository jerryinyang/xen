"""XENA calibration & self-falsification machinery (INFR-006 WS-6; L-12 governance clause).

Before XENA may adjudicate any live universe, the whole pipeline (search → certification →
final gate) must be characterised on universes with KNOWN truth:

* **Dogfood-negative battery** — synthetic universes of zero-edge candidates (random
  per-trade outcomes on realistic trade calendars, seed batteries per L-19, realistic
  round-trip costs). Requirement: certification certifies ~nothing AND the measured
  null final-gate pass rate ≈ the pre-registered α. Zero-cost nulls are friendlier than
  live (they center on zero instead of below it), so any zero-cost FPR figure is an
  upper bound under a friendlier null — the default here charges costs.
* **Synthetic-positive battery** — planted-edge candidates (known bps/trade, reported
  NET of the charged cost) mixed into zero-edge noise. Sweeping the planted edge size
  yields the framework's end-to-end MDE curve.

**Segment layout (review finding 2).** Calibration mirrors the live Q1 partition — the
data span is partitioned into a SEARCH band, a disjoint RANKING band (selection folds),
and a disjoint GATE band. The walk never touches the ranking or gate bands; fold ranking
never touches the search band; the gate runs through the real `run_final_gate` code path
(ledger included) so the null gate pass rate is MEASURED, not derived.

Both batteries run the REAL pipeline code paths — no shortcuts — so a calibration result
certifies the machinery actually used on live universes. After operator sign-off the
parameter registry + thresholds are hash-pinned (`freeze_registry`); tuning any XENA
parameter after seeing a live universe's outcome is a governance violation.
"""
from __future__ import annotations

import hashlib
import json
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl

from xen.xena.certify import certify_and_rank, contiguous_purged_folds
from xen.xena.final_gate import run_final_gate
from xen.xena.oracle import CandidateStream, OracleConfig
from xen.xena.search import SearchParams, run_restart

NS = 1_000_000_000
DEFAULT_COST_BPS = 2.0   # realistic round-trip; zero-cost nulls are anti-conservative
#                          for the MDE curve (review finding — design item 4)


# --------------------------------------------------------------------------- #
# Segment layout (mirrors the live Q1 partition)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class SegmentLayout:
    """Disjoint search / ranking / gate bands. Boundaries are pre-registered quantities.

    Default split of ``[start, end)``: 50% search, 30% ranking, 20% gate — chronological,
    contiguous, disjoint. The walk sees only ``search``; selection folds are carved from
    ``ranking``; the final gate runs on ``gate``.
    """
    search: tuple[int, int]
    ranking: tuple[int, int]
    gate: tuple[int, int]

    @classmethod
    def from_span(cls, start_ns: int, end_ns: int, *, search_frac: float = 0.5,
                  ranking_frac: float = 0.3) -> "SegmentLayout":
        if not (0 < search_frac and 0 < ranking_frac
                and search_frac + ranking_frac < 1):
            raise ValueError("fractions must be positive and sum to < 1")
        a = int(start_ns + (end_ns - start_ns) * search_frac)
        b = int(start_ns + (end_ns - start_ns) * (search_frac + ranking_frac))
        return cls((int(start_ns), a), (a, b), (b, int(end_ns)))


# --------------------------------------------------------------------------- #
# Synthetic universe generators (regenerable from seed — L-19 D1 discipline)
# --------------------------------------------------------------------------- #
def synthetic_candidate(cid: str, *, edge_bps: float, noise_bps: float, n_trades: int,
                        n_bars: int, bar_seconds: int, seed: int,
                        hold_bars: int = 20,
                        cost_bps: float = DEFAULT_COST_BPS) -> CandidateStream:
    """One synthetic candidate: flat price grid, trades on a jittered calendar, per-trade
    GROSS outcome = ``edge_bps + N(0, noise_bps)``; the oracle charges ``cost_bps`` per
    round trip, so the planted NET edge is ``edge_bps - cost_bps``. Fully regenerable
    from ``seed``."""
    rng = np.random.default_rng(seed)
    t = np.arange(n_bars, dtype=np.int64) * bar_seconds * NS
    marks = pl.DataFrame({"CloseTime": t, "Open": np.full(n_bars, 100.0)})
    entries = np.sort(rng.choice(np.arange(10, n_bars - hold_bars - 2), size=n_trades,
                                 replace=False))
    rows = []
    for ei in entries:
        ep = 100.0
        outcome_bps = edge_bps + rng.normal(0.0, noise_bps)
        rows.append({"EntryTime": int(t[ei]), "ExitTime": int(t[ei + hold_bars]),
                     "Direction": 1.0, "EntryPrice": ep,
                     "ExitPrice": ep * (1.0 + outcome_bps / 1e4),
                     "StopDistance": 1.0, "Censored": False})
    trades = pl.DataFrame(rows, schema={"EntryTime": pl.Int64, "ExitTime": pl.Int64,
                                        "Direction": pl.Float64, "EntryPrice": pl.Float64,
                                        "ExitPrice": pl.Float64, "StopDistance": pl.Float64,
                                        "Censored": pl.Boolean})
    return CandidateStream(cid, "SYNTH", trades, marks, cost_bps=cost_bps)


def dogfood_universe(*, n_candidates: int, seed: int, n_trades: int = 60,
                     noise_bps: float = 30.0, n_bars: int = 4000,
                     bar_seconds: int = 60,
                     cost_bps: float = DEFAULT_COST_BPS) -> list[CandidateStream]:
    """Zero-GROSS-edge universe (the global null). With costs charged, every candidate's
    expected NET P&L is −cost_bps/trade — the live-realistic null."""
    return [synthetic_candidate(f"null{i}", edge_bps=0.0, noise_bps=noise_bps,
                                n_trades=n_trades, n_bars=n_bars, bar_seconds=bar_seconds,
                                seed=seed * 10_007 + i, cost_bps=cost_bps)
            for i in range(n_candidates)]


def planted_universe(*, n_planted: int, n_null: int, edge_bps: float, seed: int,
                     n_trades: int = 60, noise_bps: float = 30.0, n_bars: int = 4000,
                     bar_seconds: int = 60,
                     cost_bps: float = DEFAULT_COST_BPS) -> list[CandidateStream]:
    """``n_planted`` known-GROSS-edge candidates hidden among ``n_null`` zero-edge ones.
    The battery reports the planted edge NET of ``cost_bps`` (L-21 money honesty)."""
    planted = [synthetic_candidate(f"plant{i}", edge_bps=edge_bps, noise_bps=noise_bps,
                                   n_trades=n_trades, n_bars=n_bars,
                                   bar_seconds=bar_seconds, seed=seed * 20_011 + i,
                                   cost_bps=cost_bps)
               for i in range(n_planted)]
    nulls = dogfood_universe(n_candidates=n_null, seed=seed + 500, n_trades=n_trades,
                             noise_bps=noise_bps, n_bars=n_bars, bar_seconds=bar_seconds,
                             cost_bps=cost_bps)
    return planted + nulls


# --------------------------------------------------------------------------- #
# v2 generators — realistic-null battery (2026-07-10 upgrade)
#
# The calibration contract needs only KNOWN TRUTH + real code paths + seed
# regenerability; nothing requires a flat price grid. v2 upgrades the null's realism on
# the three axes the flat grid missed, while keeping truth exact:
#   * regime-switching GBM price path → real intra-trade MTM variation + vol episodes;
#   * ONE shared path per universe → cross-candidate correlated noise (the harder null:
#     lucky candidates rise together);
#   * vol-clustered entries → admission contention + regime concentration (L-24/F02
#     failure shape becomes testable).
# Null exactness: trade direction is a COIN FLIP independent of the future, so
# E[dir · Δprice] = 0 on any path, drift or not (EXP-019 analytic-null pattern).
# Planted truth: the exit fill is shifted favourably by exactly edge_bps.
# --------------------------------------------------------------------------- #
def regime_gbm_path(*, n_bars: int, seed: int, base_vol_bps: float = 8.0,
                    high_vol_mult: float = 3.0, p_enter_high: float = 0.01,
                    p_exit_high: float = 0.05, drift_bps: float = 0.0,
                    price0: float = 100.0) -> tuple[np.ndarray, np.ndarray]:
    """(opens, high_vol_state) — two-state Markov regime-switching GBM, seeded."""
    rng = np.random.default_rng(seed)
    state = np.empty(n_bars, dtype=bool)
    s = False
    for i in range(n_bars):
        s = (rng.random() < p_enter_high) if not s else (rng.random() >= p_exit_high)
        state[i] = s
    vol = base_vol_bps * np.where(state, high_vol_mult, 1.0) / 1e4
    rets = drift_bps / 1e4 + vol * rng.standard_normal(n_bars)
    opens = price0 * np.exp(np.cumsum(rets))
    return opens, state


def path_candidate(cid: str, *, opens: np.ndarray, high_vol: np.ndarray,
                   edge_bps: float, n_trades: int, seed: int,
                   bar_seconds: int = 60, hold_bars: int = 20,
                   cost_bps: float = DEFAULT_COST_BPS,
                   vol_cluster_weight: float = 3.0) -> CandidateStream:
    """One candidate on a SHARED price path. Coin-flip direction (E[gross]=0 exactly);
    planted ``edge_bps`` applied as a favourable exit-fill shift. Entries are sampled
    with ``vol_cluster_weight``× preference for high-vol bars (clustering + contention);
    stop distance scales with the local regime vol."""
    rng = np.random.default_rng(seed)
    n_bars = len(opens)
    t = np.arange(n_bars, dtype=np.int64) * bar_seconds * NS
    marks = pl.DataFrame({"CloseTime": t, "Open": opens})
    eligible = np.arange(10, n_bars - hold_bars - 2)
    w = np.where(high_vol[eligible], vol_cluster_weight, 1.0)
    entries = np.sort(rng.choice(eligible, size=n_trades, replace=False, p=w / w.sum()))
    base_vol = 8.0 / 1e4
    rows = []
    for ei in entries:
        d = 1.0 if rng.random() < 0.5 else -1.0            # coin flip → E[dir·Δ]=0
        ep = float(opens[ei])
        raw_exit = float(opens[ei + hold_bars])
        exit_px = raw_exit * (1.0 + d * edge_bps / 1e4)    # known planted truth
        stop = ep * base_vol * (3.0 if high_vol[ei] else 1.0) * 5.0
        rows.append({"EntryTime": int(t[ei]), "ExitTime": int(t[ei + hold_bars]),
                     "Direction": d, "EntryPrice": ep, "ExitPrice": exit_px,
                     "StopDistance": stop, "Censored": False})
    trades = pl.DataFrame(rows, schema={"EntryTime": pl.Int64, "ExitTime": pl.Int64,
                                        "Direction": pl.Float64, "EntryPrice": pl.Float64,
                                        "ExitPrice": pl.Float64, "StopDistance": pl.Float64,
                                        "Censored": pl.Boolean})
    return CandidateStream(cid, "SYNTH", trades, marks, cost_bps=cost_bps)


def path_universe(*, n_planted: int, n_null: int, edge_bps: float, seed: int,
                  n_trades: int = 60, n_bars: int = 4000, bar_seconds: int = 60,
                  cost_bps: float = DEFAULT_COST_BPS) -> list[CandidateStream]:
    """v2 universe: one shared regime-GBM path; ``n_planted`` known-edge + ``n_null``
    coin-flip candidates, all correlated through the common path. ``n_planted=0`` is
    the v2 null universe."""
    opens, hv = regime_gbm_path(n_bars=n_bars, seed=seed * 7_919)
    out = []
    for i in range(n_planted):
        out.append(path_candidate(f"plant{i}", opens=opens, high_vol=hv,
                                  edge_bps=edge_bps, n_trades=n_trades,
                                  seed=seed * 20_011 + i, bar_seconds=bar_seconds,
                                  cost_bps=cost_bps))
    for i in range(n_null):
        out.append(path_candidate(f"null{i}", opens=opens, high_vol=hv, edge_bps=0.0,
                                  n_trades=n_trades, seed=seed * 10_007 + 500 + i,
                                  bar_seconds=bar_seconds, cost_bps=cost_bps))
    return out


# --------------------------------------------------------------------------- #
# Pipeline-under-test driver
# --------------------------------------------------------------------------- #
def run_pipeline_once(streams: list[CandidateStream], config: OracleConfig, *,
                      n_restarts: int, budget: int, plateau_threshold: float,
                      f_floor: float, n_folds: int, params: SearchParams,
                      layout: SegmentLayout, purge_ns: int,
                      gate_pass_threshold: float | None = None,
                      gate_workdir: str | Path | None = None,
                      universe_id: str = "CALIB") -> dict:
    """Search + certification + (optionally) the real final gate, on the disjoint
    layout bands, exactly as a live run would execute them.

    Search on ``layout.search`` only; folds carved from ``layout.ranking``; when
    ``gate_pass_threshold`` is given, the top certified portfolio goes through
    ``run_final_gate`` on ``layout.gate`` (real ledger, in ``gate_workdir``), so gate
    pass rates are measured through the real code path.
    """
    finalists = [run_restart(streams, config, budget=budget, restart_id=r + 1,
                             params=params, segment=layout.search)
                 for r in range(n_restarts)]
    folds = contiguous_purged_folds(layout.ranking[0], layout.ranking[1],
                                    n_folds=n_folds, purge_ns=purge_ns)
    out = certify_and_rank(finalists, streams, config,
                           plateau_threshold=plateau_threshold, f_floor=f_floor,
                           folds=folds, params=params, search_segment=layout.search)
    out["gate"] = None
    if gate_pass_threshold is not None and out["ranked"]:
        top = out["ranked"][0]
        workdir = Path(gate_workdir) if gate_workdir else Path(tempfile.mkdtemp(
            prefix="xena-calib-gate-"))
        workdir.mkdir(parents=True, exist_ok=True)
        out["gate"] = run_final_gate(
            top.subset, streams, config, gate_segment=layout.gate,
            pass_threshold=gate_pass_threshold, search_F_claim=top.search_F_hat,
            universe_root=workdir, universe_id=universe_id,
            evaluation_count=out["evaluation_count"], params=params)
    return out


def calibration_battery(*, universes: int, make_universe, config: OracleConfig,
                        n_restarts: int, budget: int, plateau_threshold: float,
                        f_floor: float, n_folds: int, params: SearchParams,
                        layout: SegmentLayout, purge_ns: int,
                        gate_pass_threshold: float | None = None,
                        gate_workdir: str | Path | None = None) -> dict:
    """Run the pipeline over ``universes`` independent synthetic universes
    (``make_universe(seed) -> list[CandidateStream]``). Aggregates:

    * ``certification_rate`` — FPR when the generator is the null, power when planted.
    * ``gate_pass_rate`` — fraction of universes whose top certified portfolio PASSES the
      real final gate (measured, not analytic; None when no gate threshold given). For a
      null battery this is the null gate pass rate to compare against pre-registered α.
    """
    outcomes = []
    for u in range(universes):
        streams = make_universe(u + 1)
        wd = (Path(gate_workdir) / f"u{u + 1}") if gate_workdir else None
        out = run_pipeline_once(streams, config, n_restarts=n_restarts, budget=budget,
                                plateau_threshold=plateau_threshold, f_floor=f_floor,
                                n_folds=n_folds, params=params, layout=layout,
                                purge_ns=purge_ns,
                                gate_pass_threshold=gate_pass_threshold,
                                gate_workdir=wd, universe_id=f"CALIB-u{u + 1}")
        top = sorted(out["ranked"][0].subset) if out["ranked"] else []
        outcomes.append({"universe_seed": u + 1, "n_certified": out["n_certified"],
                         "top_subset": top,
                         "gate_passed": (out["gate"]["passed"] if out["gate"] else None),
                         "evaluation_count": out["evaluation_count"],
                         "distinct_subsets": out["distinct_subsets"],
                         "dispersion": out["dispersion"]["F_hat"]})
    n_certifying = sum(1 for o in outcomes if o["n_certified"] > 0)
    gated = [o for o in outcomes if o["gate_passed"] is not None]
    return {"n_universes": universes,
            "n_certifying": n_certifying,
            "certification_rate": n_certifying / universes,
            "n_gated": len(gated),
            "n_gate_passed": sum(1 for o in gated if o["gate_passed"]),
            "gate_pass_rate": (sum(1 for o in gated if o["gate_passed"]) / universes
                               if gate_pass_threshold is not None else None),
            "outcomes": outcomes}


def planted_recovery_stats(battery: dict, planted_prefix: str = "plant") -> dict:
    """How much of each certifying universe's top portfolio is planted candidates —
    the power/selection-purity read for a planted battery."""
    fracs = []
    for o in battery["outcomes"]:
        if o["top_subset"]:
            top = o["top_subset"]
            fracs.append(sum(1 for c in top if c.startswith(planted_prefix)) / len(top))
    return {"n_with_winner": len(fracs),
            "planted_fraction_mean": float(np.mean(fracs)) if fracs else float("nan"),
            "planted_fraction_min": float(np.min(fracs)) if fracs else float("nan")}


# --------------------------------------------------------------------------- #
# §11 insensitivity smoke sweeps ("verify once, never tune")
# --------------------------------------------------------------------------- #
def insensitivity_sweep(streams: list[CandidateStream], config: OracleConfig, *,
                        budget: int, layout: SegmentLayout,
                        base: SearchParams = SearchParams(),
                        L_values: tuple[int, ...] = (50, 150, 500),
                        block_values: tuple[int, ...] = (32, 64, 128),
                        move_prob_variants: tuple[dict, ...] = (
                            {"add": 0.25, "drop": 0.25, "swap": 0.45, "2swap": 0.05},
                            {"add": 0.3, "drop": 0.3, "swap": 0.35, "2swap": 0.05},
                            {"add": 0.2, "drop": 0.2, "swap": 0.55, "2swap": 0.05}),
                        n_seeds: int = 3) -> dict:
    """One-time §11 insensitivity verification: terminal best-F̂ across L / block-length /
    move-prob variants, several restart seeds each. Evidence for the registry's
    "insensitivity verified" annotations — a large spread on any axis is a red flag to
    resolve BEFORE freeze, not a knob to tune."""
    def runs(params: SearchParams) -> list[float]:
        return [run_restart(streams, config, budget=budget, restart_id=s + 1,
                            params=params, segment=layout.search).best_F_hat
                for s in range(n_seeds)]

    def stats(values: list[float]) -> dict:
        return {"median": float(np.median(values)), "min": float(np.min(values)),
                "max": float(np.max(values))}

    from dataclasses import replace
    out: dict = {"L": {}, "block_bars": {}, "move_probs": {}}
    for L in L_values:
        out["L"][str(L)] = stats(runs(replace(base, L=L)))
    for b in block_values:
        out["block_bars"][str(b)] = stats(runs(replace(base, block_bars=b)))
    for i, mp in enumerate(move_prob_variants):
        out["move_probs"][f"variant{i}"] = {"probs": mp,
                                            **stats(runs(replace(base, move_probs=dict(mp))))}
    return out


# --------------------------------------------------------------------------- #
# Freeze: hash-pin the registry at WS-6 sign-off
# --------------------------------------------------------------------------- #
def freeze_registry(*, params: SearchParams, plateau_threshold: float, f_floor: float,
                    gate_pass_threshold: float, layout: SegmentLayout,
                    battery_summary: dict, out_path: str | Path,
                    operator_signoff: str) -> dict:
    """Write the frozen XENA parameter registry + thresholds with a SHA-256 pin.

    Produced AT WS-6 sign-off (the pinning is part of the freeze, not after it). Any
    post-freeze change to a pinned value is a new, predeclared calibration — never an
    in-place edit. The hash covers the registry content, so tampering is detectable."""
    registry = {
        "search_params": asdict(params),
        "plateau_threshold": plateau_threshold,
        "f_floor": f_floor,
        "gate_pass_threshold": gate_pass_threshold,
        "segment_layout": asdict(layout),
        "battery_summary": battery_summary,
        "operator_signoff": operator_signoff,
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
    }
    blob = json.dumps(registry, sort_keys=True).encode("utf-8")
    artifact = {"registry": registry, "sha256": hashlib.sha256(blob).hexdigest()}
    Path(out_path).write_text(json.dumps(artifact, indent=1), encoding="utf-8")
    return artifact


def verify_frozen_registry(path: str | Path) -> dict:
    """Re-hash and verify a frozen registry artifact; raises on mismatch."""
    artifact = json.loads(Path(path).read_text(encoding="utf-8"))
    blob = json.dumps(artifact["registry"], sort_keys=True).encode("utf-8")
    digest = hashlib.sha256(blob).hexdigest()
    if digest != artifact["sha256"]:
        raise RuntimeError(f"frozen registry hash mismatch: {digest} != {artifact['sha256']}")
    return artifact["registry"]
