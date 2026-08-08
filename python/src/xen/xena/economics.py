"""Q1 pre-search universe economics disclosure + zero-cost compliance (INFR-009 P0; INFR-022).

Emits an observation + routing record **before any search budget starts**. Never drops a
candidate on quality (XENA principle: no per-candidate gates).

Zero-cost compliance contract (INFR-022 §3.3 — replaces the retired cost-map integrity):
* Default cost model: ``NO_COST_CHARGED`` — nothing is charged. ``cost_bps == 0`` is a
  **compliant** zero-cost pin (the old "0.0 is an unpinned placeholder" refusal is gone).
* ``cost_bps`` missing is allowed when the candidate declares the zero-cost model
  (``cost_model``/``cost_scope`` ∈ {``NO_COST_CHARGED``, ``ZERO_COST_MODEL``}); otherwise
  missing/non-finite → non-compliant.
* ``cost_bps`` non-zero **without an operator cost directive** (``operator_cost_directive``
  dict, or ``operator_cost_directive.json`` next to the manifest) → non-compliant: search
  and gate are refused.
* ``cost_scope`` must be absent, ``NO_COST_CHARGED``, or ``ZERO_COST_MODEL``; any
  fees/funding/spread scope (e.g. the retired ``PARTIAL_FEES_FUNDING_ONLY``) is refused
  without a directive.
* ``money_per_unit`` remains required finite > 0 (position sizing / capital units — NOT a
  cost).
* Gross economics are always disclosed (even when compliance fails) so the operator can
  see day-one economics. Search refusal is separate from disclosure. Every artifact
  carries the zero-cost caveat (INFR-022 §3.1) verbatim.
"""
from __future__ import annotations

import json
import math
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import polars as pl

from xen.xena.oracle import CandidateStream

ECONOMICS_ARTIFACT_NAME = "economics_disclosure.json"
INTEGRITY_INCOMPLETE = "INTEGRITY_INCOMPLETE"
ROUTING_PROCEED = "proceed_search"
ROUTING_CHAR = "characterisation_only"
ROUTING_STOP = "do_not_search"

# INFR-022 zero-cost model labels (§3.3). "Zero" is a MODEL, never a measurement: absence
# of cost is disclosed via the caveat text, never asserted as "measured zero cost".
NO_COST_CHARGED = "NO_COST_CHARGED"
ZERO_COST_MODEL = "ZERO_COST_MODEL"
VALID_ZERO_COST_SCOPES = frozenset({NO_COST_CHARGED, ZERO_COST_MODEL})

COST_DIRECTIVE_FILE = "operator_cost_directive.json"


@dataclass(frozen=True)
class ZeroCostStatus:
    """Universe-level zero-cost compliance result (INFR-022 §3.3)."""
    complete: bool
    n_candidates: int
    n_incomplete: int
    incomplete: list[dict[str, Any]]
    reason: str
    cost_model: str  # NO_COST_CHARGED | DIRECTIVE_BACKED


def _cost_scope_of(c: Mapping[str, Any]) -> Any:
    return c.get("cost_scope") if isinstance(c, Mapping) else None


def _cost_model_of(c: Mapping[str, Any]) -> Any:
    return c.get("cost_model") if isinstance(c, Mapping) else None


def _has_directive(operator_cost_directive: Any) -> bool:
    """True when a usable operator cost directive is present (dict or JSON file)."""
    if operator_cost_directive is None:
        return False
    if isinstance(operator_cost_directive, (str, Path)):
        path = Path(operator_cost_directive)
        if not path.exists():
            return False
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return False
    else:
        payload = dict(operator_cost_directive)
    return bool(payload.get("reason") and payload.get("scope"))


def is_zero_cost_compliant(cost_bps: Any, *, cost_model: Any = None,
                           cost_scope: Any = None, has_directive: bool = False,
                           ) -> tuple[bool, str | None]:
    """Per-candidate zero-cost compliance (INFR-022 §3.3).

    Returns ``(ok, reason)``. ``cost_bps == 0`` is compliant; missing is allowed only
    under an explicit zero-cost model/scope; non-zero requires a directive.
    """
    scope = _normalize_scope(cost_scope)
    model = _normalize_scope(cost_model)
    declared_zero = scope in VALID_ZERO_COST_SCOPES or model in VALID_ZERO_COST_SCOPES
    if scope is not None and scope not in VALID_ZERO_COST_SCOPES and not has_directive:
        return False, f"cost_scope_charges_costs:{scope}"
    if cost_bps is None:
        if declared_zero:
            return True, None
        return False, "missing_cost_bps_without_zero_cost_model"
    try:
        c = float(cost_bps)
    except (TypeError, ValueError):
        return False, "non_finite_cost_bps"
    if not math.isfinite(c):
        return False, "non_finite_cost_bps"
    if c != 0.0 and not has_directive:
        return False, "non_zero_cost_bps_without_directive"
    return True, None


def _normalize_scope(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s or None


def is_valid_money_per_unit(mpu: float | None) -> bool:
    if mpu is None:
        return False
    try:
        v = float(mpu)
    except (TypeError, ValueError):
        return False
    return math.isfinite(v) and v > 0.0


def check_zero_cost_compliance(
    candidates: Sequence[Mapping[str, Any]] | Sequence[CandidateStream],
    *,
    operator_cost_directive: Any = None,
) -> ZeroCostStatus:
    """Inspect every candidate's cost pins under the INFR-022 zero-cost model.

    Accepts manifest candidate dicts or loaded ``CandidateStream``s. ``has_directive``
    is evaluated once from ``operator_cost_directive`` (dict, or path to
    ``operator_cost_directive.json`` next to the manifest).
    """
    directive = _has_directive(operator_cost_directive)
    incomplete: list[dict[str, Any]] = []
    for c in candidates:
        if isinstance(c, CandidateStream):
            cid, cost, mpu, sym = c.candidate_id, c.cost_bps, c.money_per_unit, c.symbol
            scope = model = None  # streams carry no scope/model; costs come pre-pinned
        else:
            cid = str(c.get("candidate_id", "?"))
            cost = c.get("cost_bps")
            mpu = c.get("money_per_unit", 1.0)
            sym = str(c.get("symbol", "?"))
            scope = _cost_scope_of(c)
            model = _cost_model_of(c)
        reasons = []
        ok, reason = is_zero_cost_compliant(cost, cost_model=model, cost_scope=scope,
                                            has_directive=directive)
        if not ok:
            reasons.append(reason)
        if not is_valid_money_per_unit(mpu if mpu is None else float(mpu)):
            reasons.append("invalid_money_per_unit")
        if reasons:
            incomplete.append({
                "candidate_id": cid, "symbol": sym,
                "cost_bps": cost, "money_per_unit": mpu,
                "cost_scope": scope, "cost_model": model,
                "reasons": reasons,
            })
    n = len(candidates)
    complete = n > 0 and len(incomplete) == 0
    reason = ("ok" if complete else
              (INTEGRITY_INCOMPLETE if n else "empty_universe"))
    cost_model = "DIRECTIVE_BACKED" if (complete and directive) else NO_COST_CHARGED
    return ZeroCostStatus(complete, n, len(incomplete), incomplete, reason, cost_model)


def check_cost_map_integrity(
    candidates: Sequence[Mapping[str, Any]] | Sequence[CandidateStream],
    *,
    operator_cost_directive: Any = None,
) -> ZeroCostStatus:
    """Backward-compatible alias for :func:`check_zero_cost_compliance` (INFR-022 §3.3)."""
    return check_zero_cost_compliance(candidates,
                                      operator_cost_directive=operator_cost_directive)


class SearchRefusedIntegrity(RuntimeError):
    """Raised when search/gate is attempted without zero-cost compliance (INFR-022)."""


def assert_zero_cost_allows_search(status: ZeroCostStatus) -> None:
    """Hard precondition: non-compliant cost pins refuse search and gate."""
    if not status.complete:
        raise SearchRefusedIntegrity(
            f"{INTEGRITY_INCOMPLETE}: zero-cost compliance failed "
            f"({status.n_incomplete}/{status.n_candidates} candidates, {status.reason}). "
            "Search and gate refused. Fix cost pins to the zero-cost model "
            "(cost_bps=0 / cost_model=NO_COST_CHARGED) or record an operator cost "
            "directive; economics disclosure may still be read."
        )


def assert_cost_map_allows_search(status: ZeroCostStatus) -> None:
    """Backward-compatible alias for :func:`assert_zero_cost_allows_search`."""
    assert_zero_cost_allows_search(status)


def _leg_gross_stats(run_dir: Path, *, segment: tuple[int, int] | None
                     ) -> dict[str, Any]:
    """Per-candidate raw-emission gross bps stats (engine RealizedBps) + PSR pairing."""
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
    # PSR on the SAME per-trade series as gross_mean_bps (INFR-022 §4.2 pairing rule)
    from xen.evaluation import psr_row
    psr = psr_row(r)
    return {
        "n_legs": int(len(r)),
        "gross_mean_bps": float(np.mean(r)),
        "gross_median_bps": float(np.median(r)),
        "gross_std_bps": float(np.std(r)),
        "win_rate": float(np.mean(r > 0)),
        "frac_positive_sum": float(np.sum(r) > 0),
        **psr,
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
) -> dict[str, Any]:
    """Build the Q1 economics_disclosure artifact for a universe.

    Parameters
    ----------
    manifest_path : universe_manifest.json path.
    segment : optional (start_ns, end_ns) — typically the TRAIN search band.
    operator_routing : optional override; default derived from zero-cost compliance.
        Allowed values: ``proceed_search`` / ``characterisation_only`` / ``do_not_search``
        (no deployability language, INFR-022 §3.3).

    Returns
    -------
    dict
        Full disclosure artifact (also written next to the manifest when requested).
        Carries ``cost_model: NO_COST_CHARGED`` (or ``DIRECTIVE_BACKED``) + the zero-cost
        caveat text (§3.1) verbatim.
    """
    mpath = Path(manifest_path)
    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    root = mpath.parent
    cands = list(manifest["candidates"])
    directive_path = root / COST_DIRECTIVE_FILE
    integrity = check_zero_cost_compliance(
        cands, operator_cost_directive=directive_path if directive_path.exists() else None
    )

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

    from xen.evaluation import zero_cost_caveat

    if operator_routing is not None:
        routing = operator_routing
        reason = routing_reason or "operator_override"
    elif not integrity.complete:
        routing = ROUTING_STOP
        reason = (f"{INTEGRITY_INCOMPLETE}: {integrity.n_incomplete} candidates "
                  "fail zero-cost compliance — search/gate refused")
    else:
        routing = ROUTING_PROCEED
        reason = "zero-cost compliant; no automatic quality filter applied"

    artifact: dict[str, Any] = {
        "schema": "xena.economics_disclosure.v2",
        "universe_id": manifest.get("universe_id", root.name),
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "segment_ns": list(segment) if segment is not None else None,
        "stage": "Q1_pre_search",
        "zero_cost": {
            "cost_model": integrity.cost_model,
            "compliance_complete": integrity.complete,
            "n_candidates": integrity.n_candidates,
            "n_non_compliant": integrity.n_incomplete,
            "reason": integrity.reason,
            # Cap incomplete list in artifact (full count kept); avoid multi-MB dumps.
            "non_compliant_sample": integrity.incomplete[:20],
            "status_label": ("OK" if integrity.complete else INTEGRITY_INCOMPLETE),
            "caveat": zero_cost_caveat(),
        },
        "gross_economics": quant,
        "slices": slices,
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
            "Discloses only — removes NO candidate. Zero-cost non-compliance refuses "
            "search+gate (integrity), never quality-filters the universe."
        ),
        "redesign": "INFR-009 P0 (consolidated-03 §4.1); INFR-022 zero-cost §3.3",
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
            f"{art.get('zero_cost', {})}"
        )
    return art
