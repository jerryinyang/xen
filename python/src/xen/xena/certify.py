"""XENA shortlist evidence package (INFR-006 WS-4 base; **INFR-009 P1 redesign**).

The search stage is a selection-bias machine; post-search work builds an **evidence
package**, not a threshold conjunction that "certifies" tradability.

INFR-009 changes (consolidated-03 §4.3):
* Binding score is intensive ``g_gross`` (same definition as search).
* ``F_floor``, binding ``min_drop_ratio``, Hamming-as-similarity, and ``resim_divergence``
  as a pass criterion are **retired from the binding path**. Delete-one / keystone,
  Jaccard / core / spread, random-subset reference (+ S, percentile), ubiquity, and
  eval counts remain as **evidence only**.
* All distinct restart terminals enter the package and are ranked on disjoint folds by
  intensive edge — no absolute-F cliff screen gates inclusion.
* S (random-subset separation) is **never** a pass threshold (search bias; §3).

Retained machinery: fold ranking on disjoint contiguous purged folds (full re-sim);
skepticism accounting (eval count + distinct subsets); keystone attribution as evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any

import numpy as np

from xen.xena.oracle import CandidateStream, OracleConfig, evaluate
from xen.xena.score import g_gross_point, robust_g_hat
from xen.xena.search import (EvalCache, EvalRecord, RestartResult, SearchParams,
                             bootstrap_block_starts, clip_grid_covering, universe_grid)


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
    g_hat, g_point, boot = robust_g_hat(
        res, streams, grid, starts,
        block=params.block_bars, quantile=params.quantile)
    rec = EvalRecord(g_hat, g_point, boot, res.n_admitted, res.n_rejected, -1, -1,
                     score_kind="g_gross")
    cache.put(subset, rec)
    return rec


# --------------------------------------------------------------------------- #
# Plateau certification (§9)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class PlateauReport:
    """Delete-one / keystone **evidence** for one terminal (INFR-009: not a binder).

    ``passed`` is retained for backward-compatible tests/callers but is **not** used to
    gate shortlist inclusion under the redesign. Prefer reading ``keystone``,
    ``min_drop_ratio``, and ``drop_scores`` as attribution evidence.
    """
    subset: frozenset[str]
    F_hat: float                         # ĝ = P25(g_gross)
    drop_scores: dict[str, float]        # member -> ĝ(S \ {member})
    swap_floor: float                    # min over sampled swap neighbors (NaN if none)
    min_drop_ratio: float                # min_i ĝ(S\\{i}) / ĝ(S) — evidence, not binder
    threshold: float                     # legacy X (reported; not binding)
    f_floor: float                       # legacy floor (reported; not binding)
    passed: bool                         # legacy cliff flag; not a shortlist gate
    keystone: str | None                 # worst-drop member (attribution)
    n_topup_evals: int
    binding: bool = False                # INFR-009: always False on the binding path


def plateau_screen(subset: frozenset[str], streams: list[CandidateStream],
                   config: OracleConfig, *, threshold: float = 0.0, f_floor: float = float("-inf"),
                   restart_seed: int, params: SearchParams = SearchParams(),
                   segment: tuple[int, int] | None = None, oracle_seed: int = 0,
                   cache: EvalCache | None = None, n_swap_samples: int | None = None,
                   ) -> PlateauReport:
    """Delete-one / swap-neighbor **evidence** for one terminal candidate.

    INFR-009: ``threshold`` (legacy X) and ``f_floor`` are **not** binding. They may still
    be supplied so legacy diagnostics and tests can read the same ratios; shortlist
    inclusion ignores them. Coverage: all |S| single-drop neighbors (keystone), plus
    sampled swaps. ``restart_seed`` pairs bootstrap indices with the originating restart.
    """
    cache = cache if cache is not None else EvalCache()
    universe = sorted(s.candidate_id for s in streams)
    grid = universe_grid(streams)
    if segment is not None:
        grid = clip_grid_covering(grid, segment, streams)
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

    # Evidence ratios (legacy passed flag preserved for tests; not a shortlist gate)
    if drop_scores and np.isfinite(base.F_hat) and abs(base.F_hat) > 1e-15:
        ratios = {m: v / base.F_hat for m, v in drop_scores.items()}
        min_ratio = float(min(ratios.values()))
        keystone = min(ratios, key=ratios.get)  # type: ignore[arg-type]
        legacy_pass = (base.F_hat >= f_floor and base.F_hat > 0
                       and min_ratio >= threshold)
    else:
        min_ratio, keystone, legacy_pass = float("nan"), None, False
        if drop_scores:
            # still name the worst absolute drop for attribution
            keystone = min(drop_scores, key=drop_scores.get)  # type: ignore[arg-type]
    # Always surface keystone as attribution (worst-drop member); legacy_pass only
    # affects the retired cliff flag, not whether the name is recorded.
    return PlateauReport(subset, base.F_hat, drop_scores, swap_floor, min_ratio,
                         threshold, f_floor, legacy_pass, keystone,
                         cache.evaluation_count - before, binding=False)


# --------------------------------------------------------------------------- #
# Restart dispersion diagnostics (§10.2)
# --------------------------------------------------------------------------- #
def dispersion_report(finalists: list[RestartResult]) -> dict:
    """ĝ-dispersion + pairwise Hamming / Jaccard of terminal candidates — **evidence only**.

    Hamming is **not** a similarity binder (INFR-009 / D2). Tight score + tight Hamming =
    findable basin; wild dispersion = noise-dominated landscape. Operator judges.
    """
    F = np.array([r.best_F_hat for r in finalists], dtype=float)
    subsets = [r.best_subset for r in finalists]
    hd = [len(a.symmetric_difference(b)) for a, b in combinations(subsets, 2)]
    jacc = []
    for a, b in combinations(subsets, 2):
        union = a | b
        jacc.append(len(a & b) / len(union) if union else 1.0)
    return {
        "n_restarts": len(finalists),
        "score_kind": "g_gross",
        "F_hat": {"min": float(F.min()) if len(F) else float("nan"),
                  "median": float(np.median(F)) if len(F) else float("nan"),
                  "max": float(F.max()) if len(F) else float("nan"),
                  "spread": float(F.max() - F.min()) if len(F) else float("nan")},
        "hamming": {"min": int(min(hd)) if hd else 0,
                    "median": float(np.median(hd)) if hd else 0.0,
                    "max": int(max(hd)) if hd else 0,
                    "binding": False},
        "jaccard": {"min": float(min(jacc)) if jacc else 1.0,
                    "median": float(np.median(jacc)) if jacc else 1.0,
                    "max": float(max(jacc)) if jacc else 1.0,
                    "binding": False},
        "n_distinct_terminals": len(set(subsets)),
        "sizes": sorted(len(s) for s in subsets),
    }


def jaccard_core_spread(subsets: list[frozenset[str]]) -> dict[str, Any]:
    """Core-set / Jaccard / size-spread diagnostics (evidence; not a rejection conjunction)."""
    if not subsets:
        return {"n": 0}
    core = set.intersection(*(set(s) for s in subsets)) if subsets else set()
    union = set.union(*(set(s) for s in subsets)) if subsets else set()
    pairs = list(combinations(subsets, 2))
    jacc = [(len(a & b) / len(a | b) if (a | b) else 1.0) for a, b in pairs]
    sizes = [len(s) for s in subsets]
    return {
        "n_subsets": len(subsets),
        "core_set": sorted(core),
        "core_size": len(core),
        "union_size": len(union),
        "jaccard_median": float(np.median(jacc)) if jacc else 1.0,
        "jaccard_min": float(min(jacc)) if jacc else 1.0,
        "size_min": int(min(sizes)),
        "size_max": int(max(sizes)),
        "size_spread": int(max(sizes) - min(sizes)),
        "binding": False,
        "note": "identification diagnostic — not a falsity claim (consolidated-03 §4.3)",
    }


def random_subset_reference(
    live_subset: frozenset[str],
    streams: list[CandidateStream],
    config: OracleConfig,
    *,
    n_random: int = 64,
    seed: int = 0,
    segment: tuple[int, int] | None = None,
    oracle_seed: int = 0,
) -> dict[str, Any]:
    """Same-universe matched-size random-subset reference (+ S, percentile) — EVIDENCE ONLY.

    S = (g_live − median(g_random)) / IQR(g_random). Never a pass threshold (search bias).
    """
    universe = [s.candidate_id for s in streams]
    k = len(live_subset)
    if k == 0 or k > len(universe):
        return {"n_random": 0, "S": float("nan"), "binding": False}
    g_live = g_gross_point(
        evaluate(live_subset, streams, config, segment=segment, seed=oracle_seed),
        streams)
    rng = np.random.default_rng(seed)
    g_rand = []
    for _ in range(n_random):
        pick = frozenset(str(c) for c in rng.choice(universe, size=k, replace=False))
        g_rand.append(g_gross_point(
            evaluate(pick, streams, config, segment=segment, seed=oracle_seed),
            streams))
    arr = np.asarray(g_rand, dtype=float)
    finite = arr[np.isfinite(arr)]
    if len(finite) < 4:
        return {"n_random": len(finite), "g_live": g_live, "S": float("nan"),
                "percentile": float("nan"), "binding": False}
    med = float(np.median(finite))
    q75, q25 = float(np.quantile(finite, 0.75)), float(np.quantile(finite, 0.25))
    iqr = max(q75 - q25, 1e-12)
    S = (g_live - med) / iqr if np.isfinite(g_live) else float("nan")
    pct = float(np.mean(finite < g_live)) if np.isfinite(g_live) else float("nan")
    return {
        "n_random": int(len(finite)),
        "subset_size": k,
        "g_live": float(g_live) if np.isfinite(g_live) else None,
        "g_random_median": med,
        "g_random_iqr": float(iqr),
        "S": float(S) if np.isfinite(S) else None,
        "percentile": pct,
        "binding": False,
        "note": "EVIDENCE ONLY — S is not a pass threshold (consolidated-03 §3)",
    }


def ubiquity_enrichment(subsets: list[frozenset[str]],
                        streams: list[CandidateStream]) -> dict[str, Any]:
    """Universe membership frequency among finalists + crude domain/hold enrichment."""
    if not subsets:
        return {"n": 0}
    from collections import Counter
    cnt: Counter[str] = Counter()
    for s in subsets:
        cnt.update(s)
    n = len(subsets)
    top = cnt.most_common(20)
    # parse domain/hold tokens from candidate ids when present
    domain_c: Counter[str] = Counter()
    hold_c: Counter[str] = Counter()
    for cid, c in cnt.items():
        parts = cid.split("-")
        if len(parts) >= 5:
            domain_c[parts[2]] += c
            hold_c[parts[3]] += c
    return {
        "n_finalists": n,
        "top_members": [{"id": i, "count": c, "frac": c / n} for i, c in top],
        "domain_counts": dict(domain_c),
        "hold_counts": dict(hold_c),
        "binding": False,
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
    fold_F: list[float]           # full re-sim g_gross per fold, fresh account state
    median_F: float
    worst_F: float
    search_F_hat: float           # search-segment ĝ claim
    score_kind: str = "g_gross"


def rank_on_folds(candidates: list[tuple[frozenset[str], float]],
                  streams: list[CandidateStream], config: OracleConfig,
                  folds: list[tuple[int, int]], *, oracle_seed: int = 0,
                  rank_by: str = "median") -> tuple[list[FoldRanking], dict]:
    """Rank shortlist candidates by the DISTRIBUTION of full re-simulation **g_gross**
    across disjoint contiguous purged folds (median or worst — never best)."""
    if rank_by not in ("median", "worst"):
        raise ValueError("rank_by must be 'median' or 'worst'")
    rankings = []
    for subset, search_F in candidates:
        fF = []
        for f in folds:
            res = evaluate(subset, streams, config, segment=f, seed=oracle_seed)
            fF.append(g_gross_point(res, streams))
        finite = [x for x in fF if np.isfinite(x)]
        med = float(np.median(finite)) if finite else float("-inf")
        worst = float(min(finite)) if finite else float("-inf")
        rankings.append(FoldRanking(subset, fF, med, worst, search_F,
                                    score_kind="g_gross"))
    key = (lambda r: r.median_F) if rank_by == "median" else (lambda r: r.worst_F)
    ranked = sorted(rankings, key=key, reverse=True)

    pbo = float("nan")
    if len(rankings) >= 2:
        is_winner = max(rankings, key=lambda r: r.search_F_hat)
        n_folds = len(folds)
        under = 0
        for i in range(n_folds):
            vals = [r.fold_F[i] for r in rankings if np.isfinite(r.fold_F[i])]
            med = float(np.median(vals)) if vals else float("-inf")
            under += is_winner.fold_F[i] < med
        pbo = under / n_folds
    diag = {"rank_by": rank_by, "n_folds": len(folds), "pbo_like": pbo,
            "score_kind": "g_gross", "folds_ns": [list(f) for f in folds]}
    return ranked, diag


# --------------------------------------------------------------------------- #
# Full pipeline driver (spec §13 `full_pipeline`, search → certify → rank)
# --------------------------------------------------------------------------- #
def certify_and_rank(finalists: list[RestartResult], streams: list[CandidateStream],
                     config: OracleConfig, *, plateau_threshold: float = 0.0,
                     f_floor: float = float("-inf"), folds: list[tuple[int, int]],
                     params: SearchParams = SearchParams(),
                     search_segment: tuple[int, int] | None = None,
                     oracle_seed: int = 0, rank_by: str = "median",
                     registry_path: str | None = None,
                     n_random_ref: int = 64,
                     random_ref_seed: int = 0,
                     include_random_ref: bool = True,
                     include_fill_basis: bool = True) -> dict:
    """Build the shortlist **evidence package** over terminal restart candidates.

    INFR-009: every distinct restart terminal enters the package (no F_floor /
    min_drop_ratio gate). Ranked on intensive g_gross folds. Registry path may be
    supplied for legacy search-params check; **absolute F thresholds are not binding**
    and are recorded as retired. No verdict: operator judges.

    ``n_certified`` kept as alias of shortlist size for callers; it is NOT a cliff-pass count.
    """
    registry_sha = None
    retired_threshold_drift: dict[str, Any] | None = None
    if registry_path is not None:
        import json
        from dataclasses import asdict
        from pathlib import Path

        from xen.xena.calibration import verify_frozen_registry  # lazy: import cycle
        artifact = json.loads(Path(registry_path).read_text(encoding="utf-8"))
        registry = verify_frozen_registry(registry_path)
        # Search engine params still must match any pin the caller claims to use.
        if json.loads(json.dumps(asdict(params))) != registry["search_params"]:
            raise ValueError("SearchParams differ from the frozen registry's "
                             "search_params — calibration credential does not transfer")
        registry_sha = artifact["sha256"]
        # F_floor / plateau X are RETIRED binders (INFR-009 / consolidated-03):
        # record drift as evidence only — do not hard-raise (would force callers to
        # pass dead values verbatim).
        pin_x = float(registry["plateau_threshold"])
        pin_f = float(registry["f_floor"])
        if plateau_threshold != pin_x or f_floor != pin_f:
            retired_threshold_drift = {
                "binding": False,
                "note": "retired binders — drift recorded, not enforced",
                "plateau_threshold_arg": plateau_threshold,
                "plateau_threshold_pin": pin_x,
                "f_floor_arg": f_floor,
                "f_floor_pin": pin_f,
            }

    disp = dispersion_report(finalists)
    plateau_reports: list[PlateauReport] = []
    shortlist: list[tuple[frozenset[str], float]] = []
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
        # INFR-009: ALL distinct terminals enter ranking (evidence package, not cliff gate)
        shortlist.append((r.best_subset, r.best_F_hat))

    ranked, fold_diag = ([], {"rank_by": rank_by, "n_folds": len(folds),
                              "pbo_like": float("nan"), "score_kind": "g_gross"})
    if shortlist:
        ranked, fold_diag = rank_on_folds(shortlist, streams, config, folds,
                                          oracle_seed=oracle_seed, rank_by=rank_by)

    # resim_divergence: EVIDENCE only (retired as binder — A3 / INFR-009)
    boot_by_subset = {r.best_subset: r.cache.get(r.best_subset) for r in finalists}
    resim_divergence = []
    for fr in ranked:
        rec = boot_by_subset.get(fr.subset)
        if rec is None:
            continue
        finite_boot = rec.boot[np.isfinite(rec.boot)]
        search_p25 = (float(np.quantile(finite_boot, params.quantile))
                      if len(finite_boot) else float("nan"))
        resim_divergence.append({
            "subset": sorted(fr.subset),
            "search_band_boot_p25": search_p25,
            "search_band_boot_median": (float(np.median(finite_boot))
                                        if len(finite_boot) else float("nan")),
            "fold_median_F": fr.median_F,
            "fold_worst_F": fr.worst_F,
            "frac_folds_below_search_p25": float(np.mean(
                [f < search_p25 for f in fr.fold_F if np.isfinite(f)]))
            if np.isfinite(search_p25) else float("nan"),
            "binding": False,
            "score_kind": "g_gross",
        })

    subsets_list = [s for s, _ in shortlist]
    jcs = jaccard_core_spread(subsets_list)
    ubi = ubiquity_enrichment(subsets_list, streams)

    random_ref = None
    if include_random_ref and ranked:
        random_ref = random_subset_reference(
            ranked[0].subset, streams, config,
            n_random=n_random_ref, seed=random_ref_seed,
            segment=search_segment, oracle_seed=oracle_seed)

    # P2: mandatory print-vs-path fill-basis on shortlist members (evidence only)
    fill_basis = None
    if include_fill_basis and shortlist:
        from xen.xena.fill_basis import decompose_stream, summarize_decomposition
        by_id = {s.candidate_id: s for s in streams}
        union: set[str] = set()
        for s, _ in shortlist:
            union |= set(s)
        parts = []
        for cid in sorted(union):
            st = by_id.get(cid)
            if st is None:
                continue
            df = decompose_stream(st, segment=search_segment)
            if df is not None and df.height:
                parts.append(df)
        if parts:
            import polars as pl
            fill_basis = summarize_decomposition(pl.concat(parts))
            fill_basis["binding"] = False
            fill_basis["retired_replacement_for"] = "HARD_permutation_battery"
            fill_basis["n_shortlist_members_decomposed"] = len(parts)
        else:
            fill_basis = {"n_legs": 0, "empty": True, "binding": False}

    total_evals = sum(r.cache.evaluation_count for r in finalists)
    distinct: set[frozenset[str]] = set()
    for r in finalists:
        distinct.update(r.cache.subsets())

    # Net companion (evidence): one costed eval — ledger GrossMoney + NetMoney both present
    g_net_top = None
    if ranked:
        from dataclasses import replace
        from xen.xena.score import g_gross_point as _g
        net_cfg = replace(config, charge_costs=True)
        top_net = evaluate(ranked[0].subset, streams, net_cfg,
                           segment=search_segment, seed=oracle_seed)
        g_net_top = {
            "g_gross_point": _g(top_net, streams, net=False),
            "g_net_point": _g(top_net, streams, net=True),
            "binding": False,
            "note": "net companion evidence — deployability requires LCB(g_net)>0 after P3",
        }

    return {
        "package_kind": "evidence_package",
        "redesign": "INFR-009",
        "score_kind": "g_gross",
        "dispersion": disp,
        "plateau": plateau_reports,  # delete-one / keystone evidence
        "keystones": {str(sorted(p.subset)): p.keystone
                      for p in plateau_reports if p.keystone},
        "jaccard_core_spread": jcs,
        "ubiquity_enrichment": ubi,
        "random_subset_reference": random_ref,  # S, percentile — EVIDENCE ONLY
        "fill_basis": fill_basis,              # P2 print/path — EVIDENCE ONLY
        "net_companion": g_net_top,            # gross/net pair on top shortlist
        "ranked": ranked,
        "fold_diagnostics": fold_diag,
        "resim_divergence": resim_divergence,  # evidence only; retired binder
        "registry_sha256": registry_sha,
        "retired_threshold_drift": retired_threshold_drift,
        "n_certified": len(shortlist),         # alias: shortlist size (not cliff-pass)
        "n_shortlisted": len(shortlist),
        "n_finalists": len(finalists),
        "evaluation_count": total_evals,
        "distinct_subsets": len(distinct),
        "plateau_threshold": plateau_threshold,  # legacy field; not binding
        "f_floor": f_floor,                      # legacy field; not binding
        "retired_binders": [
            "F_floor", "gate_pass_threshold", "resim_divergence",
            "binding_min_drop_ratio", "Hamming_as_similarity",
            "S_as_pass_threshold",
        ],
        "binding_note": (
            "No absolute-F / Hamming / resim / S threshold binds this package. "
            "Counted TEST gate binder is LCB(g_gross)>0 after CAL (P3) — not active here."
        ),
        "hard_permutation_battery": "RETIRED (INFR-009 P2)",
    }
