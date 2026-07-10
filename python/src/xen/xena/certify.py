"""XENA selection / certification stage (INFR-006 WS-4; spec §§9–10).

The search stage is a selection-bias machine; nothing it produces is trusted until it
survives machinery the walk cannot influence:

* **Plateau certification (§9)** — composition-robustness as CLIFF-SCREENING, never
  flatness-maximization: screen on the worst single-drop neighbor (and a sampled-swap
  floor); never penalize neighbor variance. A failing candidate yields a keystone
  attribution (the member whose removal collapses F̂) routed to individual scrutiny.
* **Restart dispersion diagnostics (§10.2)** — terminal F̂-dispersion and pairwise Hamming
  distances across independent restarts; reported, never gating (operator judges).
* **Fold ranking (§10.1)** — finalists ranked on DISJOINT contiguous purged temporal folds,
  each simulated with fresh account state (full re-simulation, not ledger resampling);
  rank by median or worst fold, never best; PBO-style statistic reported. CPCV-style
  stitched paths are excluded (account-state path dependency, spec Appendix A).
* **Skepticism accounting (§10.4)** — the total evaluation count travels with every result.

All thresholds (plateau X, fold count) are pre-registered before results are seen (L-23);
this module takes them as arguments and records them in its artifacts.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

import numpy as np

from xen.xena.oracle import CandidateStream, OracleConfig, evaluate
from xen.xena.search import (EvalCache, EvalRecord, RestartResult, SearchParams,
                             bootstrap_F, bootstrap_block_starts, grid_increments,
                             universe_grid)


# --------------------------------------------------------------------------- #
# Shared: robust evaluation on the search segment (same machinery as the walk)
# --------------------------------------------------------------------------- #
def _robust_eval(subset: frozenset[str], streams: list[CandidateStream],
                 config: OracleConfig, grid: np.ndarray, starts: np.ndarray,
                 params: SearchParams, segment: tuple[int, int] | None,
                 oracle_seed: int, cache: EvalCache) -> EvalRecord:
    rec = cache.get(subset)
    if rec is not None:
        return rec
    res = evaluate(subset, streams, config, segment=segment, seed=oracle_seed)
    inc = grid_increments(res, grid)
    boot = bootstrap_F(inc, starts, block=params.block_bars,
                       initial_equity=config.initial_equity)
    rec = EvalRecord(float(np.quantile(boot, params.quantile)), res.F_point, boot,
                     res.n_admitted, res.n_rejected, -1, -1)
    cache.put(subset, rec)
    return rec


# --------------------------------------------------------------------------- #
# Plateau certification (§9)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class PlateauReport:
    subset: frozenset[str]
    F_hat: float
    drop_scores: dict[str, float]        # member -> F̂(S \ {member})
    swap_floor: float                    # min over sampled swap neighbors (NaN if none)
    min_drop_ratio: float                # min_i F̂(S\{i}) / F̂(S)  (the cliff score)
    threshold: float                     # pre-registered X
    f_floor: float                       # pre-registered minimum robust objective
    passed: bool
    keystone: str | None                 # worst-drop member when failing (attribution)
    n_topup_evals: int


def plateau_screen(subset: frozenset[str], streams: list[CandidateStream],
                   config: OracleConfig, *, threshold: float, f_floor: float,
                   restart_seed: int, params: SearchParams = SearchParams(),
                   segment: tuple[int, int] | None = None, oracle_seed: int = 0,
                   cache: EvalCache | None = None, n_swap_samples: int | None = None,
                   ) -> PlateauReport:
    """Cliff-screen one terminal candidate. ``threshold`` (X) is the pre-registered floor
    on ``min drop-neighbor F̂ ratio``; it must be set before any result is seen (L-23).

    ``f_floor`` (pre-registered, same discipline) is the minimum robust objective at which
    the ratio is meaningful: near F̂ ≈ 0 the drop ratio is scale-unstable — noise-level
    absolute differences produce extreme ratios in both directions (review finding 3). The
    screen is the conjunction ``F̂(S) >= f_floor AND min_drop_ratio >= X``.

    Coverage: ALL |S| single-drop neighbors (the keystone tests), plus ``n_swap_samples``
    random swap neighbors (default 2·|S|, spec §9). Cached walk evaluations are reused at
    zero cost (`cache`); only thin coverage is topped up.

    ``restart_seed`` must match the restart whose bootstrap-start matrix produced the
    candidate's F̂ so neighbor comparisons stay paired (common indices).
    """
    cache = cache if cache is not None else EvalCache()
    universe = sorted(s.candidate_id for s in streams)
    grid = universe_grid(streams)
    if segment is not None:
        # same segment-grid restriction as run_restart — MUST stay in lockstep with the
        # walk's convention or the plateau ratio's numerator (neighbor F̂, computed here)
        # and denominator (candidate F̂, from the walk's cache) decouple
        grid = grid[(grid >= segment[0]) & (grid < segment[1])]
        if len(grid) < 2:
            raise ValueError("segment covers < 2 universe bars")
    starts = bootstrap_block_starts(len(grid), block=params.block_bars,
                                    n_boot=params.n_boot,
                                    seed=1_000_003 * restart_seed + 17)
    before = cache.evaluation_count

    def ev(s: frozenset[str]) -> EvalRecord:
        return _robust_eval(s, streams, config, grid, starts, params, segment,
                            oracle_seed, cache)

    base = ev(subset)
    members = sorted(subset)
    drop_scores = {m: ev(subset - {m}).F_hat for m in members}

    rng = np.random.default_rng(restart_seed)
    outside = sorted(set(universe) - subset)
    n_swaps = (2 * len(members)) if n_swap_samples is None else n_swap_samples
    swap_scores: list[float] = []
    if members and outside:
        for _ in range(n_swaps):
            m = members[int(rng.integers(len(members)))]
            o = outside[int(rng.integers(len(outside)))]
            swap_scores.append(ev((subset - {m}) | {o}).F_hat)
    swap_floor = float(min(swap_scores)) if swap_scores else float("nan")

    if base.F_hat >= f_floor and base.F_hat > 0 and drop_scores:
        ratios = {m: v / base.F_hat for m, v in drop_scores.items()}
        min_ratio = float(min(ratios.values()))
        keystone = min(ratios, key=ratios.get)  # type: ignore[arg-type]
        passed = min_ratio >= threshold
    else:
        # a non-positive (or sub-floor) robust objective cannot certify: the ratio is
        # scale-unstable there and a barely-positive F̂ shouldn't reach the gate anyway
        min_ratio, keystone, passed = float("nan"), None, False
    return PlateauReport(subset, base.F_hat, drop_scores, swap_floor, min_ratio,
                         threshold, f_floor, passed, None if passed else keystone,
                         cache.evaluation_count - before)


# --------------------------------------------------------------------------- #
# Restart dispersion diagnostics (§10.2)
# --------------------------------------------------------------------------- #
def dispersion_report(finalists: list[RestartResult]) -> dict:
    """F̂-dispersion + pairwise Hamming distances of terminal candidates. Informative —
    tight F + tight Hamming = findable basin; wild dispersion = noise-dominated landscape
    (distrust the winner; expect certification to reject most candidates)."""
    F = np.array([r.best_F_hat for r in finalists], dtype=float)
    subsets = [r.best_subset for r in finalists]
    hd = [len(a.symmetric_difference(b)) for a, b in combinations(subsets, 2)]
    return {
        "n_restarts": len(finalists),
        "F_hat": {"min": float(F.min()), "median": float(np.median(F)),
                  "max": float(F.max()), "spread": float(F.max() - F.min())},
        "hamming": {"min": int(min(hd)) if hd else 0,
                    "median": float(np.median(hd)) if hd else 0.0,
                    "max": int(max(hd)) if hd else 0},
        "n_distinct_terminals": len(set(subsets)),
        "sizes": sorted(len(s) for s in subsets),
    }


# --------------------------------------------------------------------------- #
# Fold ranking on disjoint temporal segments (§10.1)
# --------------------------------------------------------------------------- #
def contiguous_purged_folds(start_ns: int, end_ns: int, *, n_folds: int,
                            purge_ns: int) -> list[tuple[int, int]]:
    """Split [start, end) into ``n_folds`` contiguous windows, shrinking each by
    ``purge_ns`` at BOTH edges (embargo around fold boundaries so positions spanning an
    edge don't couple folds). Contiguous only — stitched paths are excluded (Appendix A)."""
    edges = np.linspace(start_ns, end_ns, n_folds + 1).astype(np.int64)
    folds = []
    for i in range(n_folds):
        a, b = int(edges[i]) + purge_ns, int(edges[i + 1]) - purge_ns
        if b <= a:
            raise ValueError("purge too large for the fold width")
        folds.append((a, b))
    return folds


@dataclass(frozen=True)
class FoldRanking:
    subset: frozenset[str]
    fold_F: list[float]           # full re-simulation F_point per fold, fresh account state
    median_F: float
    worst_F: float
    search_F_hat: float           # the search-segment claim, for the §A.4.5 gap diagnostic


def rank_on_folds(candidates: list[tuple[frozenset[str], float]],
                  streams: list[CandidateStream], config: OracleConfig,
                  folds: list[tuple[int, int]], *, oracle_seed: int = 0,
                  rank_by: str = "median") -> tuple[list[FoldRanking], dict]:
    """Rank certified candidates by the DISTRIBUTION of full re-simulation scores across
    disjoint contiguous purged folds (median or worst fold — never best). Each fold is
    simulated with fresh account state. Returns rankings (best first) + a PBO-style stat:
    the fraction of folds where the search-stage winner (highest F̂) underperforms the
    median finalist."""
    if rank_by not in ("median", "worst"):
        raise ValueError("rank_by must be 'median' or 'worst'")
    rankings = []
    for subset, search_F in candidates:
        fF = [evaluate(subset, streams, config, segment=f, seed=oracle_seed).F_point
              for f in folds]
        rankings.append(FoldRanking(subset, fF, float(np.median(fF)), float(min(fF)),
                                    search_F))
    key = (lambda r: r.median_F) if rank_by == "median" else (lambda r: r.worst_F)
    ranked = sorted(rankings, key=key, reverse=True)

    pbo = float("nan")
    if len(rankings) >= 2:
        is_winner = max(rankings, key=lambda r: r.search_F_hat)
        n_folds = len(folds)
        under = 0
        for i in range(n_folds):
            med = float(np.median([r.fold_F[i] for r in rankings]))
            under += is_winner.fold_F[i] < med
        pbo = under / n_folds
    diag = {"rank_by": rank_by, "n_folds": len(folds), "pbo_like": pbo,
            "folds_ns": [list(f) for f in folds]}
    return ranked, diag


# --------------------------------------------------------------------------- #
# Full pipeline driver (spec §13 `full_pipeline`, search → certify → rank)
# --------------------------------------------------------------------------- #
def certify_and_rank(finalists: list[RestartResult], streams: list[CandidateStream],
                     config: OracleConfig, *, plateau_threshold: float,
                     f_floor: float, folds: list[tuple[int, int]],
                     params: SearchParams = SearchParams(),
                     search_segment: tuple[int, int] | None = None,
                     oracle_seed: int = 0, rank_by: str = "median",
                     registry_path: str | None = None) -> dict:
    """Selection stage over terminal restart candidates. Returns the full evidence
    package — ranked certified candidates, plateau reports (incl. keystone attributions
    for failures), dispersion diagnostics, and the §10.4 evaluation count. No verdict:
    the operator judges (pipeline-config: integrity gates hard, value reads informative).

    ``registry_path``: hash-pinned frozen registry — **mandatory for live universes**
    (calibration passes None while deriving thresholds); when given, ``plateau_threshold``,
    ``f_floor`` and ``params`` must match the pinned values or this raises (review F01:
    pre-registration enforced in code, not by convention)."""
    registry_sha = None
    if registry_path is not None:
        import json
        from dataclasses import asdict
        from pathlib import Path

        from xen.xena.calibration import verify_frozen_registry  # lazy: import cycle
        artifact = json.loads(Path(registry_path).read_text(encoding="utf-8"))
        registry = verify_frozen_registry(registry_path)
        if (plateau_threshold != float(registry["plateau_threshold"])
                or f_floor != float(registry["f_floor"])):
            raise ValueError(
                f"plateau_threshold/f_floor ({plateau_threshold}, {f_floor}) differ from "
                f"the frozen registry ({registry['plateau_threshold']}, "
                f"{registry['f_floor']}) — pinned thresholds are never re-derived")
        if json.loads(json.dumps(asdict(params))) != registry["search_params"]:
            raise ValueError("SearchParams differ from the frozen registry's "
                             "search_params — calibration credential does not transfer")
        registry_sha = artifact["sha256"]

    disp = dispersion_report(finalists)
    plateau_reports: list[PlateauReport] = []
    certified: list[tuple[frozenset[str], float]] = []
    seen: set[frozenset[str]] = set()
    for r in finalists:
        if r.best_subset in seen:
            continue
        seen.add(r.best_subset)
        rep = plateau_screen(r.best_subset, streams, config,
                             threshold=plateau_threshold, f_floor=f_floor,
                             restart_seed=r.restart_id,
                             params=params, segment=search_segment,
                             oracle_seed=oracle_seed, cache=r.cache)
        plateau_reports.append(rep)
        if rep.passed:
            certified.append((r.best_subset, r.best_F_hat))

    ranked, fold_diag = ([], {"rank_by": rank_by, "n_folds": len(folds),
                              "pbo_like": float("nan")})
    if certified:
        ranked, fold_diag = rank_on_folds(certified, streams, config, folds,
                                          oracle_seed=oracle_seed, rank_by=rank_by)

    # §14 "ledger-resampling approximation error" detector (review F04): per certified
    # finalist, the search-segment bootstrap claim vs the full re-simulation fold scores.
    # Evidence only, never gating. NOT like-for-like scales (search-band bootstrap of
    # log-wealth vs per-fold point log-wealth on the ranking band) — field names say so;
    # the informative read is frac_folds_below_search_p25 drifting toward 1.
    boot_by_subset = {r.best_subset: r.cache.get(r.best_subset) for r in finalists}
    resim_divergence = []
    for fr in ranked:
        rec = boot_by_subset.get(fr.subset)
        if rec is None:
            continue
        search_p25 = float(np.quantile(rec.boot, params.quantile))
        resim_divergence.append({
            "subset": sorted(fr.subset),
            "search_band_boot_p25": search_p25,
            "search_band_boot_median": float(np.median(rec.boot)),
            "fold_median_F": fr.median_F,
            "fold_worst_F": fr.worst_F,
            "frac_folds_below_search_p25": float(np.mean(
                [f < search_p25 for f in fr.fold_F])),
        })

    # §10.4 skepticism accounting — both readings (review finding 5): total oracle calls
    # (compute honesty) and distinct subsets examined (selection-pressure index)
    total_evals = sum(r.cache.evaluation_count for r in finalists)
    distinct: set[frozenset[str]] = set()
    for r in finalists:
        distinct.update(r.cache.subsets())
    return {
        "dispersion": disp,
        "plateau": plateau_reports,
        "keystones": {str(sorted(p.subset)): p.keystone
                      for p in plateau_reports if not p.passed and p.keystone},
        "ranked": ranked,
        "fold_diagnostics": fold_diag,
        "resim_divergence": resim_divergence,  # §14 detector, evidence only (F04)
        "registry_sha256": registry_sha,       # F01: which pin these thresholds came from
        "n_certified": len(certified),
        "n_finalists": len(finalists),
        "evaluation_count": total_evals,       # total oracle evaluations
        "distinct_subsets": len(distinct),     # distinct portfolios examined
        "plateau_threshold": plateau_threshold,
        "f_floor": f_floor,
    }
