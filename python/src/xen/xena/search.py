"""XENA search stage — LAHC over the subset lattice with noise-aware acceptance (INFR-006 WS-3).

Implements `xena-model.md` §§4–8: bitmask representation, add/drop/swap/2-swap proposals,
Late Acceptance Hill Climbing with a stagnation kick, a block-bootstrap lower-quantile
objective, paired comparison on common data paths + common bootstrap indices, a soft
sign-stability gate on marginal deltas, and an append-only evaluation cache.

Load-bearing noise machinery (§6):
* Every subset in one restart is evaluated on the SAME segment and oracle seed, and every
  bootstrap uses the SAME block-start indices (common random numbers extended into the
  bootstrap) — so the paired per-resample delta ``Δ_b = F_b(S') − F_b(S)`` isolates the
  compositional difference.
* Common indices require a common index space: per-event equity increments are aggregated
  onto the UNIVERSE's fixed bar grid (union of all candidates' mark times), which is
  identical for every subset.
* The objective the walk maximizes is ``F̂(S) = quantile_q0(F_b)`` (default P25), where each
  ``F_b`` re-scores the recorded per-bar equity increments of ONE full simulation over
  resampled contiguous blocks (§7 approximation — discharged at deep validation, WS-4).

Parameter registry (spec §11) — all defaults fixed, none tuned:
L=150, c=5, kick 2–4 bits, proposal probs 0.25/0.25/0.45/0.05, B=150, quantile P25, q=0.6.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import numpy as np
import polars as pl

from xen.xena.oracle import CandidateStream, OracleConfig, OracleResult, evaluate

# spec §11 registry defaults — fix once, never tune
DEFAULT_L = 150
DEFAULT_STAG_MULT = 5
DEFAULT_KICK_BITS = (2, 4)
DEFAULT_MOVE_PROBS = {"add": 0.25, "drop": 0.25, "swap": 0.45, "2swap": 0.05}
DEFAULT_N_BOOT = 150
DEFAULT_QUANTILE = 0.25
DEFAULT_SIGN_Q = 0.6
DEFAULT_CLEAR_WIN_SDS = 2.0
DEFAULT_BLOCK_BARS = 64          # ~holding-horizon order; insensitivity verified at WS-6


# --------------------------------------------------------------------------- #
# Common-grid increments + bootstrap objective
# --------------------------------------------------------------------------- #
def universe_grid(streams: list[CandidateStream]) -> np.ndarray:
    """The fixed per-universe bar grid (sorted union of all candidates' mark times).
    Identical for every subset — the common index space for paired bootstrap."""
    times = np.unique(np.concatenate([s.marks.get_column("CloseTime").to_numpy()
                                      for s in streams]))
    if len(times) < 2:
        raise ValueError("universe grid needs >= 2 bar times")
    return times.astype(np.int64)


def clip_grid_covering(grid: np.ndarray, segment: tuple[int, int],
                       streams: list[CandidateStream] | None = None) -> np.ndarray:
    """Restrict ``grid`` to ``segment`` while guaranteeing the segment is COVERED:
    when the universe has within-segment trade events stamped AFTER the last interior
    bar-close (native m1 fills, XENA-003 Amendment 4), the first universe bar-close
    >= segment end is appended so those events have a grid bar to bin into.

    The append is event-driven (from the universe's own fill timestamps), so it is
    deterministic per universe AND identical across walk / certification / gate for
    that universe — bar-close-fill universes (XENA-001/002) reproduce the original
    clipped grid exactly, preserving lockstep with any in-flight walk."""
    clipped = grid[(grid >= segment[0]) & (grid < segment[1])]
    if len(clipped) >= 2 and streams is not None:
        seg_end = int(segment[1])
        last = int(clipped[-1])
        for s in streams:
            t = s.trades
            ev = np.concatenate([
                t.get_column("EntryTime").to_numpy(),
                t.filter(~t.get_column("Censored")).get_column("ExitTime").to_numpy()])
            ev = ev[(ev >= segment[0]) & (ev < seg_end)]
            if len(ev) and int(ev.max()) > last:
                tail = grid[grid >= seg_end]
                if len(tail):
                    clipped = np.append(clipped, tail[0])
                break
    if len(clipped) < 2:
        raise ValueError("search segment covers < 2 universe bars")
    return clipped


def grid_increments(result: OracleResult, grid: np.ndarray) -> np.ndarray:
    """Per-grid-bar equity increments of one simulation (money). Events are binned to the
    first grid time >= event time; increments telescope to the total equity delta.

    Events outside the grid raise: since the oracle censors positions at the segment end
    (finding 1), any out-of-grid event means the grid and the simulation segment disagree —
    silently clamping it into the terminal bar would distort tail blocks and the last
    decay window."""
    if len(result.equity) < 2:
        return np.zeros(len(grid))
    ev_t = result.equity_times[1:]
    ev_inc = np.diff(result.equity)
    if len(ev_t) and int(ev_t.max()) > int(grid[-1]):
        raise ValueError(
            f"equity event at {int(ev_t.max())} beyond grid end {int(grid[-1])} — "
            "grid does not cover the simulation segment")
    bins = np.searchsorted(grid, ev_t, side="left")
    out = np.zeros(len(grid))
    np.add.at(out, bins, ev_inc)
    return out


def bootstrap_block_starts(n_bars: int, *, block: int, n_boot: int,
                           seed: int) -> np.ndarray:
    """The common block-start matrix (n_boot × n_blocks), circular over ``[0, n)``.
    One matrix per restart — shared by every subset evaluation (common indices, §6.2).
    Follows the INFR-004/L-20 discipline: block capped to [1, n-1], full circular range."""
    eff_block = max(1, min(int(block), n_bars - 1))
    n_blocks = int(np.ceil(n_bars / eff_block))
    rng = np.random.default_rng(seed)
    return rng.integers(0, n_bars, size=(n_boot, n_blocks))


def bootstrap_F(increments: np.ndarray, starts: np.ndarray, *, block: int,
                initial_equity: float) -> np.ndarray:
    """F_b per resample: log-wealth of the increment series over resampled contiguous
    circular blocks. Vectorized via cumulative sums (a length-b block starting at s sums
    increments s..s+b-1 circularly)."""
    n = len(increments)
    eff_block = max(1, min(int(block), n - 1))
    n_boot, n_blocks = starts.shape
    # circular block sums via doubled cumsum: sum(inc[s:s+b]) on the doubled array
    doubled = np.concatenate([increments, increments])
    csum = np.concatenate([[0.0], np.cumsum(doubled)])
    block_sums = csum[starts + eff_block] - csum[starts]          # (n_boot, n_blocks)
    # truncate to exactly n bars: last block may be partial
    tail = n - eff_block * (n_blocks - 1)
    if tail != eff_block:
        last = starts[:, -1]
        block_sums[:, -1] = csum[last + tail] - csum[last]
    totals = block_sums.sum(axis=1)
    finals = np.maximum(initial_equity + totals, 1e-9)
    return np.log(finals / initial_equity)


# --------------------------------------------------------------------------- #
# Evaluation cache (spec §8)
# --------------------------------------------------------------------------- #
@dataclass
class EvalRecord:
    F_hat: float
    F_point: float
    boot: np.ndarray
    n_admitted: int
    n_rejected: int
    iteration: int
    restart_id: int


class EvalCache:
    """Append-only bitmask → evaluation cache. Consumers: de-duplication, cycle
    diagnostics (revisit counts), plateau certification (neighbor queries), and the
    §10.4 skepticism accounting (total evaluation count)."""

    def __init__(self) -> None:
        self._store: dict[frozenset[str], EvalRecord] = {}
        self._hits: dict[frozenset[str], int] = {}

    def key(self, subset: Iterable[str]) -> frozenset[str]:
        return frozenset(subset)

    def get(self, subset: Iterable[str]) -> EvalRecord | None:
        k = self.key(subset)
        rec = self._store.get(k)
        if rec is not None:
            self._hits[k] = self._hits.get(k, 0) + 1
        return rec

    def put(self, subset: Iterable[str], rec: EvalRecord) -> None:
        self._store.setdefault(self.key(subset), rec)   # append-only: first write wins

    def __len__(self) -> int:
        return len(self._store)

    @property
    def evaluation_count(self) -> int:
        return len(self._store)

    def subsets(self) -> set[frozenset[str]]:
        """All distinct evaluated subsets (selection-pressure accounting, §10.4)."""
        return set(self._store)

    def revisit_stats(self) -> dict[str, int]:
        hits = sorted(self._hits.values(), reverse=True)
        return {"n_unique": len(self._store), "n_cache_hits": int(sum(hits)),
                "max_revisits": int(hits[0]) if hits else 0}

    def neighbors(self, subset: Iterable[str], universe: list[str]) -> dict[str, EvalRecord]:
        """All cached Hamming-1/2 neighbors of ``subset`` (drops, adds, swaps) — the
        already-paid-for neighbor set used by plateau certification (§9)."""
        base = self.key(subset)
        out: dict[str, EvalRecord] = {}
        for k, rec in self._store.items():
            d = len(base.symmetric_difference(k))
            if 1 <= d <= 2:
                out[",".join(sorted(k))] = rec
        return out


# --------------------------------------------------------------------------- #
# Moves
# --------------------------------------------------------------------------- #
def propose_move(x: set[str], universe: list[str], rng: np.random.Generator,
                 probs: dict[str, float] = DEFAULT_MOVE_PROBS) -> set[str]:
    """One sampled move (first-improvement style; never a neighborhood scan). Infeasible
    moves (add on full, drop/swap on empty …) fall back to a feasible one."""
    outside = sorted(set(universe) - x)
    inside = sorted(x)
    names = list(probs)
    p = np.array([probs[m] for m in names], dtype=float)
    move = names[int(rng.choice(len(names), p=p / p.sum()))]
    if move == "2swap" and (len(inside) < 2 or len(outside) < 2):
        move = "swap"
    if move == "swap" and (not inside or not outside):
        move = "add" if outside else "drop"
    if move == "add" and not outside:
        move = "drop"
    if move == "drop" and not inside:
        move = "add"

    new = set(x)
    if move == "add":
        new.add(outside[int(rng.integers(len(outside)))])
    elif move == "drop":
        new.remove(inside[int(rng.integers(len(inside)))])
    elif move == "swap":
        new.remove(inside[int(rng.integers(len(inside)))])
        new.add(outside[int(rng.integers(len(outside)))])
    else:  # 2swap
        for i in rng.choice(len(inside), size=2, replace=False):
            new.remove(inside[int(i)])
        for i in rng.choice(len(outside), size=2, replace=False):
            new.add(outside[int(i)])
    return new


def kick(x: set[str], universe: list[str], rng: np.random.Generator,
         bits: tuple[int, int] = DEFAULT_KICK_BITS) -> set[str]:
    """Stagnation perturbation: flip 2–4 bits as drop+add PAIRS (swaps) where feasible,
    so |S| is preserved exactly for even bit counts; an odd remainder flips one random
    single bit. Falls back to single flips when one side is empty (spec §5)."""
    n_bits = int(rng.integers(bits[0], bits[1] + 1))

    def flip_one(s: set[str]) -> None:
        inside = sorted(s)
        outside = sorted(set(universe) - s)
        if inside and (not outside or rng.random() < 0.5):
            s.remove(inside[int(rng.integers(len(inside)))])
        elif outside:
            s.add(outside[int(rng.integers(len(outside)))])

    new = set(x)
    n_pairs, odd = divmod(n_bits, 2)
    for _ in range(n_pairs):
        inside = sorted(new)
        outside = sorted(set(universe) - new)
        if inside and outside:                       # a true swap pair
            new.remove(inside[int(rng.integers(len(inside)))])
            new.add(outside[int(rng.integers(len(outside)))])
        else:                                        # degenerate: two single flips
            flip_one(new)
            flip_one(new)
    if odd:
        flip_one(new)
    return new


# --------------------------------------------------------------------------- #
# The restart driver
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class SearchParams:
    """Spec §11 registry. Fixed at pre-registration; LOOSER/TIGHTER-tagged amendments
    only (L-23)."""
    L: int = DEFAULT_L
    stag_mult: int = DEFAULT_STAG_MULT
    kick_bits: tuple[int, int] = DEFAULT_KICK_BITS
    move_probs: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_MOVE_PROBS))
    n_boot: int = DEFAULT_N_BOOT
    block_bars: int = DEFAULT_BLOCK_BARS
    quantile: float = DEFAULT_QUANTILE
    sign_q: float = DEFAULT_SIGN_Q
    clear_win_sds: float = DEFAULT_CLEAR_WIN_SDS
    init_size: int = 5


@dataclass(frozen=True)
class RestartResult:
    best_subset: frozenset[str]
    best_F_hat: float
    restart_id: int
    n_iterations: int
    n_kicks: int
    acceptance_rate: float
    gate_rejection_rate: float   # LAHC-passed but sign-gate-blocked (walk-noise detector, §14)
    cache: EvalCache


def run_restart(streams: list[CandidateStream], config: OracleConfig, *, budget: int,
                restart_id: int, segment: tuple[int, int] | None = None,
                params: SearchParams = SearchParams(), oracle_seed: int = 0,
                cache: EvalCache | None = None) -> RestartResult:
    """One LAHC restart (spec §13 pseudocode). Deterministic given all arguments.

    ``restart_id`` seeds the walk rng AND offsets the bootstrap-start seed so different
    restarts explore differently, while WITHIN a restart every evaluation shares one
    block-start matrix (common indices) and one oracle seed (common data path).
    """
    universe = sorted(s.candidate_id for s in streams)
    grid = universe_grid(streams)
    if segment is not None:
        # restrict the bootstrap grid to the search segment: the oracle censors all P&L
        # inside the segment, so full-grid resampling would dilute blocks with
        # structurally-zero calendar and understate F̂'s dispersion relative to the gate
        # (which restricts its grid) — the frozen F_floor and search-gap baselines must
        # be on the same scale (review 2026-07-10, grid/segment consistency)
        grid = clip_grid_covering(grid, segment, streams)
    starts = bootstrap_block_starts(len(grid), block=params.block_bars,
                                    n_boot=params.n_boot, seed=1_000_003 * restart_id + 17)
    rng = np.random.default_rng(restart_id)
    cache = cache if cache is not None else EvalCache()
    it_counter = [0]

    def robust_eval(subset: set[str]) -> EvalRecord:
        rec = cache.get(subset)
        if rec is not None:
            return rec
        res = evaluate(subset, streams, config, segment=segment, seed=oracle_seed)
        inc = grid_increments(res, grid)
        boot = bootstrap_F(inc, starts, block=params.block_bars,
                           initial_equity=config.initial_equity)
        rec = EvalRecord(float(np.quantile(boot, params.quantile)), res.F_point, boot,
                         res.n_admitted, res.n_rejected, it_counter[0], restart_id)
        cache.put(subset, rec)
        return rec

    k0 = min(params.init_size, len(universe))
    x = set(str(c) for c in rng.choice(universe, size=k0, replace=False)) if k0 else set()
    cur = robust_eval(x)
    H = np.full(params.L, cur.F_hat)
    best_x, best_F = set(x), cur.F_hat
    stag = 0
    n_accept = n_gate_reject = n_kicks = 0

    for t in range(budget):
        it_counter[0] = t
        x_new = propose_move(x, universe, rng, params.move_probs)
        cand = robust_eval(x_new)

        if cand.F_hat >= H[t % params.L]:                     # LAHC criterion
            delta = cand.boot - cur.boot                      # paired, common indices
            spread = float(delta.std())
            # spec §6.2 says |ΔF_point|; we deliberately use ΔF̂ (the P25 the walk
            # optimizes) so the clear-win scale matches the acceptance scale — a
            # documented reinterpretation, not drift (review F06). spread == 0 means
            # the paired deltas are constant, i.e. the delta is exact: labelling it
            # "clear" is correct, there is no noise to chase.
            point_delta = cand.F_hat - cur.F_hat
            clear = abs(point_delta) >= params.clear_win_sds * spread
            stable = float((delta > 0).mean()) >= params.sign_q
            if clear or stable:
                x, cur = x_new, cand
                n_accept += 1
            else:
                n_gate_reject += 1                            # noise-chase blocked (§6.2)

        H[t % params.L] = cur.F_hat

        if cur.F_hat > best_F:
            best_x, best_F, stag = set(x), cur.F_hat, 0
        else:
            stag += 1
        if stag > params.stag_mult * params.L:
            x = kick(x, universe, rng, params.kick_bits)
            cur = robust_eval(x)
            stag = 0
            n_kicks += 1

    return RestartResult(frozenset(best_x), best_F, restart_id, budget, n_kicks,
                         n_accept / max(budget, 1), n_gate_reject / max(budget, 1), cache)
