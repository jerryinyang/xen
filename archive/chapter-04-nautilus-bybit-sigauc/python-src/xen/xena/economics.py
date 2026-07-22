"""Q1 pre-search universe economics disclosure + cost-map integrity (INFR-009 P0).

Closes audit E3/E4. Emits an observation + routing record **before any search budget
starts**. Never drops a candidate on quality (XENA principle: no per-candidate gates).

Hard integrity precondition (E3 / L-22 teeth):
  every symbol/candidate must carry a finite **non-placeholder** round-trip cost pin
  and a valid money_per_unit. Missing / placeholder → ``INTEGRITY_INCOMPLETE``;
  search and any future gate are refused at the universe level.

Placeholder cost policy (programme convention for this redesign):
  * ``cost_bps`` missing / non-finite → incomplete
  * ``cost_bps == 0.0`` → incomplete (unpinned; fixtures XENA-001/002/003 ship 0.0)
  * ``money_per_unit`` missing / non-finite / ≤ 0 → incomplete

Gross economics are always disclosed (even when integrity fails) so the operator can
see day-one economics. Search refusal is separate from disclosure.
"""
from __future__ import annotations

import json
import math
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import polars as pl

from xen.xena.oracle import CandidateStream

ECONOMICS_ARTIFACT_NAME = "economics_disclosure.json"
INTEGRITY_INCOMPLETE = "INTEGRITY_INCOMPLETE"
ROUTING_PROCEED = "proceed_deployability_search"
ROUTING_CHAR = "characterisation_only"
ROUTING_STOP = "do_not_search"

# Programme: 0.0 is the historical "unpinned" sentinel in XENA-00x manifests.
PLACEHOLDER_COST_BPS = 0.0


@dataclass(frozen=True)
class CostMapStatus:
    """Universe-level cost-map integrity result."""
    complete: bool
    n_candidates: int
    n_incomplete: int
    incomplete: list[dict[str, Any]]
    reason: str


def is_placeholder_cost(cost_bps: float | None) -> bool:
    """True when the pin cannot support a net / survival statement."""
    if cost_bps is None:
        return True
    try:
        c = float(cost_bps)
    except (TypeError, ValueError):
        return True
    if not math.isfinite(c):
        return True
    # Strict: zero is the unpinned sentinel used by live XENA fixtures.
    return c == PLACEHOLDER_COST_BPS


def is_valid_money_per_unit(mpu: float | None) -> bool:
    if mpu is None:
        return False
    try:
        v = float(mpu)
    except (TypeError, ValueError):
        return False
    return math.isfinite(v) and v > 0.0


def check_cost_map_integrity(
    candidates: Sequence[Mapping[str, Any]] | Sequence[CandidateStream],
) -> CostMapStatus:
    """Inspect every candidate's cost_bps + money_per_unit pins.

    Accepts either manifest candidate dicts or loaded ``CandidateStream``s.
    """
    incomplete: list[dict[str, Any]] = []
    for c in candidates:
        if isinstance(c, CandidateStream):
            cid, cost, mpu, sym = c.candidate_id, c.cost_bps, c.money_per_unit, c.symbol
        else:
            cid = str(c.get("candidate_id", "?"))
            cost = c.get("cost_bps")
            mpu = c.get("money_per_unit", 1.0)
            sym = str(c.get("symbol", "?"))
        reasons = []
        if is_placeholder_cost(cost if cost is None else float(cost)):
            reasons.append("placeholder_or_missing_cost_bps")
        if not is_valid_money_per_unit(mpu if mpu is None else float(mpu)):
            reasons.append("invalid_money_per_unit")
        if reasons:
            incomplete.append({
                "candidate_id": cid, "symbol": sym,
                "cost_bps": cost, "money_per_unit": mpu,
                "reasons": reasons,
            })
    n = len(candidates)
    complete = n > 0 and len(incomplete) == 0
    reason = ("ok" if complete else
              (INTEGRITY_INCOMPLETE if n else "empty_universe"))
    return CostMapStatus(complete, n, len(incomplete), incomplete, reason)


class SearchRefusedIntegrity(RuntimeError):
    """Raised when search/gate is attempted without a complete cost map (E3)."""


def assert_cost_map_allows_search(status: CostMapStatus) -> None:
    """Hard precondition: incomplete cost map refuses search and gate."""
    if not status.complete:
        raise SearchRefusedIntegrity(
            f"{INTEGRITY_INCOMPLETE}: cost-map incomplete "
            f"({status.n_incomplete}/{status.n_candidates} candidates). "
            "Search and gate refused. Fix finite non-placeholder cost_bps + "
            "money_per_unit pins; economics disclosure may still be read."
        )


def _leg_gross_stats(run_dir: Path, *, segment: tuple[int, int] | None
                     ) -> dict[str, Any]:
    """Per-candidate raw-emission gross bps stats (engine RealizedBps)."""
    cis = pl.read_parquet(run_dir / "cis_trades.parquet")
    if "EntryTime" not in cis.columns:
        return {"n_legs": 0}
    et = cis.get_column("EntryTime")
    if et.dtype == pl.Datetime or str(et.dtype).startswith("Datetime"):
        et_ns = et.dt.cast_time_unit("ns").cast(pl.Int64).to_numpy()
    else:
        et_ns = et.cast(pl.Int64).to_numpy()
    mask = np.ones(len(et_ns), dtype=bool)
    if segment is not None:
        mask &= (et_ns >= segment[0]) & (et_ns < segment[1])
    if "Censored" in cis.columns:
        cz = cis.get_column("Censored").to_numpy()
        # bool or 0/1
        mask &= ~np.asarray(cz, dtype=bool)
    if not mask.any():
        return {"n_legs": 0}
    live = cis.filter(pl.Series(mask))
    r = live.get_column("RealizedBps").to_numpy().astype(float)
    r = r[np.isfinite(r)]
    if len(r) == 0:
        return {"n_legs": 0}
    return {
        "n_legs": int(len(r)),
        "gross_mean_bps": float(np.mean(r)),
        "gross_median_bps": float(np.median(r)),
        "gross_std_bps": float(np.std(r)),
        "win_rate": float(np.mean(r > 0)),
        "frac_positive_sum": float(np.sum(r) > 0),
    }


def _scan_one(payload: tuple[str, str, str, float, float, tuple[int, int] | None]
              ) -> dict[str, Any]:
    cid, run_dir, symbol, cost_bps, mpu, segment = payload
    out: dict[str, Any] = {
        "candidate_id": cid, "symbol": symbol,
        "cost_bps_pin": cost_bps, "money_per_unit": mpu,
    }
    stats = _leg_gross_stats(Path(run_dir), segment=segment)
    out.update(stats)
    return out


def _parse_slice_fields(candidate_id: str) -> dict[str, str]:
    """Best-effort parse of XENA candidate_id tokens: C#-SYM-DOMAIN-HOLD-VARIANT."""
    parts = candidate_id.split("-")
    out = {"domain": "", "hold": "", "variant": ""}
    if len(parts) >= 5:
        out["domain"] = parts[2]
        out["hold"] = parts[3]
        out["variant"] = parts[4]
    return out


def economics_disclosure(
    manifest_path: str | Path,
    *,
    segment: tuple[int, int] | None = None,
    max_workers: int = 8,
    write_artifact: bool = True,
    operator_routing: str | None = None,
    routing_reason: str = "",
    cost_floor_bps_draft: float | None = None,
) -> dict[str, Any]:
    """Build the Q1 economics_disclosure artifact for a universe.

    Parameters
    ----------
    manifest_path : universe_manifest.json path.
    segment : optional (start_ns, end_ns) — typically the TRAIN search band.
    cost_floor_bps_draft : optional DRAFT survival floor for disclosure context only
        (INFR-009 §6.4 formula is not frozen — do not treat as binding).
    operator_routing : optional override; default derived from integrity + gross p50.

    Returns
    -------
    dict
        Full disclosure artifact (also written next to the manifest when requested).
    """
    mpath = Path(manifest_path)
    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    root = mpath.parent
    cands = list(manifest["candidates"])
    integrity = check_cost_map_integrity(cands)

    payloads = []
    for c in cands:
        rd = Path(c["run_dir"])
        run = rd if rd.is_absolute() else root / rd
        payloads.append((
            c["candidate_id"], str(run), c["symbol"],
            float(c.get("cost_bps", 0.0)),
            float(c.get("money_per_unit", 1.0)),
            segment,
        ))

    rows: list[dict[str, Any]] = []
    if payloads:
        workers = max(1, min(max_workers, len(payloads)))
        if workers == 1 or len(payloads) < 8:
            rows = [_scan_one(p) for p in payloads]
        else:
            with ProcessPoolExecutor(max_workers=workers) as ex:
                rows = list(ex.map(_scan_one, payloads, chunksize=max(1, len(payloads) // (workers * 4))))

    for r in rows:
        r.update(_parse_slice_fields(r["candidate_id"]))

    means = np.array([r["gross_mean_bps"] for r in rows
                      if r.get("n_legs", 0) > 0], dtype=float)
    if len(means):
        quant = {
            "p05": float(np.quantile(means, 0.05)),
            "p25": float(np.quantile(means, 0.25)),
            "p50": float(np.quantile(means, 0.50)),
            "p75": float(np.quantile(means, 0.75)),
            "p95": float(np.quantile(means, 0.95)),
            "mean": float(np.mean(means)),
            "frac_mean_gt_0": float(np.mean(means > 0)),
            "n_with_legs": int(len(means)),
        }
    else:
        quant = {"p05": float("nan"), "p25": float("nan"), "p50": float("nan"),
                 "p75": float("nan"), "p95": float("nan"), "mean": float("nan"),
                 "frac_mean_gt_0": float("nan"), "n_with_legs": 0}

    # Descriptive slices: domain × hold × variant (no deletion)
    slices: dict[str, Any] = {}
    for key in ("domain", "hold", "variant", "symbol"):
        by: dict[str, list[float]] = {}
        for r in rows:
            if r.get("n_legs", 0) <= 0:
                continue
            k = str(r.get(key) or "?")
            by.setdefault(k, []).append(float(r["gross_mean_bps"]))
        slices[key] = {
            k: {"n": len(v), "median_gross_bps": float(np.median(v)),
                "mean_gross_bps": float(np.mean(v))}
            for k, v in sorted(by.items())
        }

    # Cost context (disclosure only — pins may be incomplete)
    cost_ctx: dict[str, Any] = {
        "cost_floor_bps_draft": cost_floor_bps_draft,
        "cost_floor_status": "DRAFT_UNFROZEN — §6.4 formula not frozen (INFR-009)",
        "pins_complete": integrity.complete,
    }
    if integrity.complete and len(means):
        # naive net = gross − pin (per-candidate mean); not a deploy claim
        nets = []
        for r in rows:
            if r.get("n_legs", 0) <= 0:
                continue
            nets.append(float(r["gross_mean_bps"]) - float(r["cost_bps_pin"]))
        if nets:
            na = np.array(nets)
            cost_ctx["net_of_pin_p50_bps"] = float(np.median(na))
            cost_ctx["frac_net_gt_0"] = float(np.mean(na > 0))

    if operator_routing is not None:
        routing = operator_routing
        reason = routing_reason or "operator_override"
    elif not integrity.complete:
        routing = ROUTING_STOP
        reason = (f"{INTEGRITY_INCOMPLETE}: {integrity.n_incomplete} candidates lack "
                  "finite non-placeholder cost pins — search/gate refused")
    else:
        # Default routing hint only (operator decides): sub-draft-floor → characterisation
        p50 = quant["p50"]
        if cost_floor_bps_draft is not None and math.isfinite(p50) and p50 < cost_floor_bps_draft:
            routing = ROUTING_CHAR
            reason = (f"universe p50 gross {p50:.3f} bps < draft floor "
                      f"{cost_floor_bps_draft:.3f} bps")
        else:
            routing = ROUTING_PROCEED
            reason = "cost map complete; no automatic quality filter applied"

    artifact: dict[str, Any] = {
        "schema": "xena.economics_disclosure.v1",
        "universe_id": manifest.get("universe_id", root.name),
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "segment_ns": list(segment) if segment is not None else None,
        "stage": "Q1_pre_search",
        "cost_map_integrity": {
            "complete": integrity.complete,
            "n_candidates": integrity.n_candidates,
            "n_incomplete": integrity.n_incomplete,
            "reason": integrity.reason,
            # Cap incomplete list in artifact (full count kept); avoid multi-MB dumps.
            "incomplete_sample": integrity.incomplete[:20],
            "status_label": ("OK" if integrity.complete else INTEGRITY_INCOMPLETE),
        },
        "gross_economics": quant,
        "slices": slices,
        "cost_context": cost_ctx,
        "execution_context": {
            "note": ("print-vs-path fill-basis is computed post-shortlist via "
                     "xen.xena.fill_basis; Q1 surfaces occupancy/n_legs only"),
            "median_n_legs": (float(np.median([r["n_legs"] for r in rows
                                               if r.get("n_legs", 0) > 0]))
                              if any(r.get("n_legs", 0) > 0 for r in rows) else float("nan")),
        },
        "operator_routing": {
            "decision": routing,
            "reason": reason,
            "allowed_values": [ROUTING_PROCEED, ROUTING_CHAR, ROUTING_STOP],
        },
        "search_allowed": bool(integrity.complete and routing != ROUTING_STOP),
        "n_candidates_disclosed": len(rows),
        "candidates_summary_only": True,  # per-candidate rows not embedded (size)
        "binding_note": (
            "Discloses only — removes NO candidate. Incomplete cost map refuses "
            "search+gate (integrity), never quality-filters the universe."
        ),
        "redesign": "INFR-009 P0 (consolidated-03 §4.1)",
    }

    # Per-candidate rows stay in-memory only (artifact size); disk write is slim once.
    artifact["_per_candidate_rows"] = rows
    if write_artifact:
        slim = {k: v for k, v in artifact.items() if not k.startswith("_")}
        (root / ECONOMICS_ARTIFACT_NAME).write_text(
            json.dumps(slim, indent=1, allow_nan=True), encoding="utf-8")

    return artifact


def require_economics_before_search(universe_root: str | Path) -> dict[str, Any]:
    """Load economics_disclosure.json and refuse search if not allowed.

    Call sites: any LAHC entry for a live universe. Missing artifact → refuse
    (forces Q1 to run first).
    """
    root = Path(universe_root)
    path = root / ECONOMICS_ARTIFACT_NAME
    if not path.exists():
        raise SearchRefusedIntegrity(
            f"missing {ECONOMICS_ARTIFACT_NAME} — run economics_disclosure (Q1) "
            "before search (INFR-009 P0 / E4)"
        )
    art = json.loads(path.read_text(encoding="utf-8"))
    if not art.get("search_allowed", False):
        raise SearchRefusedIntegrity(
            f"search refused by Q1 economics_disclosure: "
            f"{art.get('operator_routing', {})} / "
            f"{art.get('cost_map_integrity', {})}"
        )
    return art
