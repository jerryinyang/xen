"""XENA final gate — continuous walk-forward on the reserved gate segment (spec Appendix A).

Applied to the single certified portfolio from the selection stage. Per INFR-006 locked
decisions: the gate segment is the TEST band (Q1); gate runs are counted in a
**portfolio-level gate ledger, cap 2 per universe** (Q2) — the ledger check is blocking and
a failed gate still spends a slot (§A.5: the run terminates as a negative result; no
post-hoc threshold revision; no re-search on the gate segment).

Protocol (§A.4):
1. ONE continuous walk-forward simulation over the full gate segment — fixed subset, fresh
   account state, full shared-capital mechanics incl. rejected signals. No refitting or
   parameter change mid-walk (the oracle is a pure function, so this holds by construction).
2. Seed replication where stochastic elements exist (v1 oracle: none — spread reported 0).
3. Block-bootstrap of the walk-forward increments → P25/median/P75 of F, never one number.
4. Sequential-window decay inspection: per-window F over consecutive windows; reported,
   never smoothed.
5. Search-stage gap: gate bootstrap median vs the search/selection-stage F̂ claim.
6. Skepticism accounting: the caller's total evaluation count is embedded in the artifact.

Pass/fail: ``pass_threshold`` on the bootstrap P25 is PRE-REGISTERED before the run (L-23);
this module refuses to run without it and records it verbatim.

Gate cost regime (operator amendment A-4, 2026-07-10): the gate runs the §A.4 protocol
TWICE — a **GROSS run (binding)** validating the pure optimizer + walk-forward selection
machinery (selection also runs gross, so the search-gap diagnostic compares like scales),
and a **NET run (informational)** with full costs + its own DD read. `passed` comes from
the gross block only. Rationale (operator, 2026-07-10): the dual gate separates the
characterisation of model performance and signal quality (gross) from failure-by-cost
scenarios (net) — a portfolio that dies only under costs is a cost problem, not a
selection-machinery problem, and conflating the two in one binding number would hide
which failed. The net block stays strictly informational but important; the final
verdict is always the operator's. L-22 retained clause: **any deployability claim must cite the
`net_informational` block** — a gross gate pass is a selection-machinery verdict, never
a tradability claim. The pre-registered `pass_threshold` must be derived from GROSS null
gate P25s (v3 re-derivation).

Second-slot semantics (operator amendment 2026-07-10, resolving the Q2-vs-§A.5 tension —
the cap-2 ledger is a **LOOSER** amendment of spec invariant 10 and is tagged as such in
INFR-006 design §5): the second slot exists for a *materially different certified subset*
or for a re-run after new TEST data has accrued — never a free retry. Re-gating a subset
identical to a previously FAILED gate row is refused unless ``new_data_attestation`` (an
operator-signed reason string) is supplied; the attestation is recorded verbatim in the
ledger. One free retry of the same subset would be quiet α-inflation (threshold-shopping);
the WS-6 null-gate FPR is measured under this same protocol.
"""
from __future__ import annotations

import json
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from xen.xena.oracle import CandidateStream, OracleConfig, evaluate
from xen.xena.search import (SearchParams, bootstrap_F, bootstrap_block_starts,
                             grid_increments, universe_grid)

GATE_LEDGER_NAME = "xena_gate_ledger.json"
MAX_GATES_PER_UNIVERSE = 2   # INFR-006 Q2 (operator-locked 2026-07-10)


class GateBudgetExhausted(RuntimeError):
    """Both counted final gates for this universe are spent."""


class GateRetryRefused(RuntimeError):
    """Same subset already failed a gate; re-gating needs a new-data attestation."""


def _load_ledger(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def _enforce_registry(registry_path: str | Path, *, pass_threshold: float,
                      params: SearchParams,
                      threshold_override_attestation: str | None) -> str:
    """Hash-verify the frozen registry and refuse a gate whose threshold or search
    params drift from the pinned values (review F01: pre-registration must be enforced
    in code, not by convention). Returns the registry sha256 for the artifact/ledger.

    An override needs ``threshold_override_attestation`` — operator-only, same
    discipline as ``new_data_attestation``; recorded verbatim."""
    from xen.xena.calibration import verify_frozen_registry  # lazy: avoids import cycle
    artifact = json.loads(Path(registry_path).read_text(encoding="utf-8"))
    registry = verify_frozen_registry(registry_path)
    frozen_thr = float(registry["gate_pass_threshold"])
    if pass_threshold != frozen_thr and not threshold_override_attestation:
        raise ValueError(
            f"pass_threshold {pass_threshold} != frozen registry gate_pass_threshold "
            f"{frozen_thr} (sha256 {artifact['sha256'][:12]}…) — threshold-shopping is a "
            "governance violation; an operator-signed threshold_override_attestation is "
            "required to deviate")
    live_params = json.loads(json.dumps(asdict(params)))  # normalize tuples → lists
    if live_params != registry["search_params"] and not threshold_override_attestation:
        raise ValueError(
            "SearchParams differ from the frozen registry's search_params — the WS-6 "
            "calibration credential does not transfer; operator attestation required")
    return artifact["sha256"]


# FTMO-style account limits — hard constraints, kept OUT of F (design §7:
# constraint-as-gate). Defaults match the FTMO challenge rules.
DEFAULT_DAILY_DD_LIMIT = 0.05    # max intraday loss vs the day's starting equity
DEFAULT_TOTAL_DD_LIMIT = 0.10    # max loss vs initial equity, any time


def dd_feasibility(equity_times: np.ndarray, equity: np.ndarray, *,
                   initial_equity: float,
                   daily_limit: float = DEFAULT_DAILY_DD_LIMIT,
                   total_limit: float = DEFAULT_TOTAL_DD_LIMIT) -> dict:
    """Hard drawdown-limit feasibility over an equity event path.

    * total: any equity < initial_equity·(1 − total_limit) → breach.
    * daily: within each UTC day, any equity < day-start equity·(1 − daily_limit) →
      breach (day-start = last equity value before the day's first event).
    Marked-to-market event path — conservative in the FTMO sense (their DD is
    equity-based, not balance-based).
    """
    if len(equity) == 0:
        return {"feasible": True, "worst_total_dd": 0.0, "worst_daily_dd": 0.0,
                "daily_limit": daily_limit, "total_limit": total_limit}
    eq = np.asarray(equity, dtype=float)
    worst_total = float((initial_equity - eq.min()) / initial_equity)

    days = (np.asarray(equity_times, dtype=np.int64) // (86_400 * 1_000_000_000))
    worst_daily = 0.0
    day_start = initial_equity
    prev_day = None
    for i in range(len(eq)):
        if days[i] != prev_day:
            day_start = eq[i - 1] if i > 0 else initial_equity
            prev_day = days[i]
        if day_start > 0:
            worst_daily = max(worst_daily, (day_start - eq[i]) / day_start)
    return {"feasible": bool(worst_total <= total_limit and worst_daily <= daily_limit),
            "worst_total_dd": worst_total, "worst_daily_dd": float(worst_daily),
            "daily_limit": daily_limit, "total_limit": total_limit}


def run_final_gate(subset: frozenset[str] | set[str], streams: list[CandidateStream],
                   config: OracleConfig, *, gate_segment: tuple[int, int],
                   pass_threshold: float, search_F_claim: float,
                   universe_root: str | Path, universe_id: str,
                   evaluation_count: int, n_decay_windows: int = 4,
                   params: SearchParams = SearchParams(), oracle_seed: int = 0,
                   n_seeds: int = 1, boot_seed: int = 424243,
                   new_data_attestation: str | None = None,
                   registry_path: str | Path | None = None,
                   threshold_override_attestation: str | None = None) -> dict:
    """Execute one counted final gate. Blocking ledger checks FIRST; the slot is spent
    (ledger row appended) whether the gate passes or fails.

    ``search_F_claim``: the selection stage's F̂ (search-segment bootstrap-P25) for this
    subset — the §A.4.5 gap input. NOTE the gap diagnostic compares this P25-claim against
    the gate MEDIAN (deliberately not like-for-like; field names say so).
    ``pass_threshold``: pre-registered floor on the gate bootstrap P25 of log-wealth F.
    ``n_seeds``: seed replication — default 1 because the v1 oracle is deterministic;
    raise it only when the oracle gains stochastic elements (fill models, slippage draws).
    ``new_data_attestation``: required to re-gate a subset identical to a FAILED ledger
    row (see module docstring); recorded verbatim.
    ``registry_path``: the hash-pinned frozen registry. **Mandatory for live universes**
    (calibration runs pass None — thresholds are being derived there, not consumed);
    when given, `pass_threshold` and `params` must byte-match the pinned values or the
    gate refuses (review F01). ``threshold_override_attestation`` is the operator-only
    escape hatch, recorded verbatim.
    """
    root = Path(universe_root)
    ledger_path = root / GATE_LEDGER_NAME
    ledger = _load_ledger(ledger_path)
    spent = [r for r in ledger if r["universe_id"] == universe_id]
    if len(spent) >= MAX_GATES_PER_UNIVERSE:
        raise GateBudgetExhausted(
            f"{universe_id}: {len(spent)}/{MAX_GATES_PER_UNIVERSE} final gates already "
            f"spent ({[r['run_utc'] for r in spent]}) — a new attempt needs a new universe")

    registry_sha = (None if registry_path is None else
                    _enforce_registry(registry_path, pass_threshold=pass_threshold,
                                      params=params,
                                      threshold_override_attestation=
                                      threshold_override_attestation))

    # Gate cost policy (operator amendment A-4, 2026-07-10): the BINDING gate run is
    # GROSS (charge_costs=False) — it validates the pure optimizer + walk-forward
    # selection machinery. A COSTED run executes alongside as an INFORMATIONAL block.
    # L-22 retained clause: any DEPLOYABILITY claim must cite the costed block; a gross
    # gate pass is a selection-machinery verdict, never a deployability claim.
    config_gross = replace(config, charge_costs=False)
    config_net = replace(config, charge_costs=True)

    subset = frozenset(subset)
    failed_same = [r for r in spent
                   if not r["passed"] and frozenset(r["subset"]) == subset]
    if failed_same and not new_data_attestation:
        raise GateRetryRefused(
            f"{universe_id}: this exact subset already FAILED a gate "
            f"({failed_same[0]['run_utc']}); the second slot is for a materially "
            "different subset or new TEST data — pass new_data_attestation to override "
            "with an operator-signed reason")
    # Similarity to prior FAILED rows is REPORTED, never gating (operator decision
    # 2026-07-10 on review F03): candidate-removal responsibility belongs to the whole
    # portfolio referee, and only exact identity is refused. The Jaccard read lets the
    # operator see a near-retry for what it is before the slot is spent.
    failed_prior = [frozenset(r["subset"]) for r in spent if not r["passed"]]
    max_jaccard_vs_prior_failed = (
        max(len(subset & f) / len(subset | f) for f in failed_prior)
        if failed_prior else None)
    grid_all = universe_grid(streams)
    grid = grid_all[(grid_all >= gate_segment[0]) & (grid_all < gate_segment[1])]
    if len(grid) < 2:
        raise ValueError("gate segment covers < 2 universe bars")

    def walk_forward_block(cfg: OracleConfig) -> dict:
        """One full §A.4 protocol pass (walk-forward + bootstrap + decay + DD) under
        one cost regime. Called twice: gross (binding) and net (informational)."""
        results = [evaluate(subset, streams, cfg, segment=gate_segment,
                            seed=oracle_seed + s) for s in range(n_seeds)]
        F_seeds = np.array([r.F_point for r in results], dtype=float)
        res = results[0]

        inc = grid_increments(res, grid)
        starts = bootstrap_block_starts(len(grid), block=params.block_bars,
                                        n_boot=max(params.n_boot, 200), seed=boot_seed)
        boot = bootstrap_F(inc, starts, block=params.block_bars,
                           initial_equity=cfg.initial_equity)
        p25, p50, p75 = (float(np.quantile(boot, q)) for q in (0.25, 0.5, 0.75))

        edges = np.linspace(gate_segment[0], gate_segment[1],
                            n_decay_windows + 1).astype(np.int64)
        windows = []
        for i in range(n_decay_windows):
            w = (grid >= edges[i]) & (grid < edges[i + 1])
            windows.append({"start_ns": int(edges[i]), "end_ns": int(edges[i + 1]),
                            "net_money": float(inc[w].sum()), "n_bars": int(w.sum())})
        net_seq = [w["net_money"] for w in windows]
        monotone_decay = bool(all(a >= b for a, b in zip(net_seq, net_seq[1:]))
                              and net_seq[0] > net_seq[-1])
        # rank correlation of window net vs time: strict monotonicity under-fires at 4
        # windows; a negative trend correlation makes mild decay visible (finding 6)
        if len(net_seq) >= 3 and len(set(net_seq)) > 1:
            order = np.argsort(np.argsort(net_seq)).astype(float)
            idx = np.arange(len(net_seq), dtype=float)
            decay_rank_corr = float(np.corrcoef(idx, order)[0, 1])
        else:
            decay_rank_corr = float("nan")

        # hard account constraint (design §7: DD-as-gate, never inside F)
        dd = dd_feasibility(res.equity_times, res.equity,
                            initial_equity=cfg.initial_equity)
        return {
            "costs_charged": bool(cfg.charge_costs),
            "F_point": float(res.F_point),
            "F_boot": {"p25": p25, "median": p50, "p75": p75},
            "seed_replication": {"n_seeds": n_seeds, "F_min": float(F_seeds.min()),
                                 "F_max": float(F_seeds.max()),
                                 "spread": float(F_seeds.max() - F_seeds.min())},
            "dd_feasibility": dd,
            "decay_windows": windows,
            "monotone_decay_flag": monotone_decay,      # regime-dependence flag (§A.4.4)
            "decay_rank_corr": decay_rank_corr,
            "n_admitted": res.n_admitted, "n_rejected": res.n_rejected,
        }

    # A-4 dual gate run: GROSS = binding (pure selection machinery); NET = informational.
    gross = walk_forward_block(config_gross)
    net = walk_forward_block(config_net)

    passed = (gross["F_boot"]["p25"] >= pass_threshold
              and gross["dd_feasibility"]["feasible"])
    p25, p50 = gross["F_boot"]["p25"], gross["F_boot"]["median"]
    artifact = {
        "universe_id": universe_id,
        "subset": sorted(subset),
        "gate_segment_ns": list(gate_segment),
        "pass_threshold_preregistered": pass_threshold,
        "passed": bool(passed),                      # binding verdict = GROSS block
        "binding_block": "gross",                    # A-4: pure optimizer+walk-forward
        "gross": gross,
        # INFORMATIONAL ONLY — but any DEPLOYABILITY claim MUST cite this block (L-22
        # retained clause): a gross pass is a selection-machinery verdict, not tradability.
        "net_informational": net,
        # §A.4.5 selection-bias calibration. NOT like-for-like: the claim is the SEARCH
        # segment's bootstrap-P25; it is compared against the GATE segment's bootstrap
        # MEDIAN. Both gross (selection ran gross → comparable scales).
        "search_stage_gap_p25claim_minus_gate_median": float(search_F_claim - p50),
        "search_F_claim_search_segment_p25": float(search_F_claim),
        "new_data_attestation": new_data_attestation,
        # informational only (F03): overlap with previously FAILED subsets in this
        # universe; never gates — surfaced for the operator's second-slot judgement
        "max_jaccard_vs_prior_failed": max_jaccard_vs_prior_failed,
        "registry_sha256": registry_sha,             # F01: which pin this gate ran under
        "threshold_override_attestation": threshold_override_attestation,
        "evaluation_count": int(evaluation_count),   # §10.4 — travels with every number
        "run_utc": datetime.now(timezone.utc).isoformat(),
    }

    # spend the slot — pass or fail (§A.5)
    ledger.append({"universe_id": universe_id, "run_utc": artifact["run_utc"],
                   "subset": artifact["subset"], "passed": bool(passed),
                   "p25": p25, "pass_threshold": pass_threshold,
                   "new_data_attestation": new_data_attestation,
                   "registry_sha256": registry_sha,
                   "threshold_override_attestation": threshold_override_attestation})
    ledger_path.write_text(json.dumps(ledger, indent=1), encoding="utf-8")
    (root / f"xena_final_gate_{len(spent) + 1}.json").write_text(
        json.dumps(artifact, indent=1), encoding="utf-8")
    return artifact
