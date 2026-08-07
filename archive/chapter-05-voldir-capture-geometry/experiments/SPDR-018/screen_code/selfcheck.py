"""Stage-2 integrity self-check (design §12), asserted IN CODE.

The SPDR lane replaces the fresh-context QA subagent with a code-asserted self-check
(`docs/references/spdr-lane.md`), so this module IS the gate. Two severities:

  HARD         blocks execution / invalidates the emission — raises
  INFORMATIVE  the operator judges; no auto-verdict, no ``pass`` field

HARD: TRIPWIRE-1, TRIPWIRE-2, TRAIN fence, holdout, universe pin, identity reconstruction,
parent parity, derangement fixed-point count, golden traces, determinism.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

import golden
import parents
import parity
from config import (
    CTRADER_FENCE_PATH,
    CTRADER_FENCE_SHA256,
    CTRADER_HOLDOUT_START_NS,
    CTRADER_TRAIN_END_NS,
    HOLDOUT_START_NS,
    IDENTITY_RECONSTRUCTION_TOL_BPS,
    MDE_SOURCE_FOR_BANDS,
    NO_PASS_FIELD,
    SCREEN_CODE_DIR,
    SPREAD_COST_DISCLOSURE,
    TRAIN_END_NS,
    UNIVERSE_N,
    UNIVERSE_PIN_FAMILY,
)


class IntegrityViolation(RuntimeError):
    """A HARD check failed. The emission is invalid."""


def _hard(checks: list, name: str, held: bool, detail) -> None:
    checks.append({"check": name, "severity": "HARD", "held": bool(held), "detail": detail})


def _info(checks: list, name: str, value) -> None:
    checks.append({"check": name, "severity": "INFORMATIVE", "detail": value})


# --------------------------------------------------------------------------- fence
def fence_checks(panels: dict[str, pd.DataFrame], checks: list) -> None:
    """TRAIN fence + holdout. Every timestamp column of every panel actually used."""
    worst = {}
    for name, df in panels.items():
        cols = [c for c in df.columns
                if c.endswith(("_ts", "_ts_ns")) or c in ("slot_start", "slot_end",
                                                          "confirm_slot_end")]
        for c in cols:
            v = df[c].to_numpy(dtype="int64", na_value=0)
            v = v[v > 0]
            if v.size:
                worst[f"{name}.{c}"] = int(v.max())
    over_train = {k: v for k, v in worst.items() if v >= TRAIN_END_NS}
    over_holdout = {k: v for k, v in worst.items() if v >= HOLDOUT_START_NS}
    _hard(checks, "TRAIN fence — max(exit_ts) < 2023-12-18T00:00Z",
          not over_train, {"max_ts_per_column": worst, "violations": over_train,
                           "train_end_ns": TRAIN_END_NS})
    _hard(checks, "Global holdout — zero rows at or after 2025-01-08T00:00Z",
          not over_holdout, {"violations": over_holdout,
                             "holdout_start_ns": HOLDOUT_START_NS})


def ctrader_fence_checks(ctrader_max_ts: int | None, checks: list) -> None:
    """cTrader has its OWN fence — never the Bybit default (design §10 / AMENDMENT-C1)."""
    blob = Path(CTRADER_FENCE_PATH).read_bytes()
    sha = hashlib.sha256(blob).hexdigest()
    _hard(checks, "cTrader fence provenance — sha256 matches the design's pin",
          sha == CTRADER_FENCE_SHA256,
          {"expected": CTRADER_FENCE_SHA256, "measured": sha, "path": str(CTRADER_FENCE_PATH)})
    if ctrader_max_ts is None:
        _info(checks, "cTrader holdout", "no cTrader rows were read in this run")
        return
    _hard(checks, "cTrader TRAIN fence — max ts < 2023-11-22T00:00Z",
          ctrader_max_ts < CTRADER_TRAIN_END_NS,
          {"max_ts": ctrader_max_ts, "train_end_ns": CTRADER_TRAIN_END_NS})
    _hard(checks, "cTrader holdout — zero rows at or after 2024-12-13T00:00Z",
          ctrader_max_ts < CTRADER_HOLDOUT_START_NS,
          {"max_ts": ctrader_max_ts, "holdout_start_ns": CTRADER_HOLDOUT_START_NS})


# --------------------------------------------------------------------------- universe
def universe_check(checks: list, *, recompute: bool = True) -> None:
    """Top-25 recompute == the pinned family universe, by SET EQUALITY (AMENDMENT-U1)."""
    pin = json.loads(Path(UNIVERSE_PIN_FAMILY).read_text())
    pinned = set(pin.get("symbols") or pin.get("universe") or [])
    detail = {"pin_path": str(UNIVERSE_PIN_FAMILY), "n_pinned": len(pinned),
              "universe_n_required": UNIVERSE_N}
    if not recompute:
        _info(checks, "Universe pin — recompute skipped by flag", detail)
        return
    try:
        from xen.nautilus.catalog_fence import load_fence_manifest
        uni = parents.load("SPDR-014")["universe"]
        rec = uni.recompute_universe(load_fence_manifest(), progress=False)
        got = set(rec["symbols"] if isinstance(rec, dict) else rec)
        detail.update({"n_recomputed": len(got),
                       "missing_from_recompute": sorted(pinned - got),
                       "extra_in_recompute": sorted(got - pinned)})
        _hard(checks, "Universe pin — top-25 recompute equals the pin (set equality)",
              got == pinned and len(pinned) == UNIVERSE_N, detail)
    except Exception as e:                                    # noqa: BLE001
        detail["error"] = repr(e)
        _hard(checks, "Universe pin — top-25 recompute equals the pin (set equality)",
              False, detail)


# --------------------------------------------------------------------------- identity
def identity_check(cell_frames: dict[str, pd.DataFrame], checks: list) -> None:
    """HARD: ``|p*W - (1-p)*L - mean| < 0.01 bps`` on EVERY signed cell (§4.1 / §12)."""
    worst = {}
    n_checked = 0
    bad_rows = []
    for arm, df in cell_frames.items():
        if df.empty or "identity_residual_bps" not in df.columns:
            continue
        r = df["identity_residual_bps"].to_numpy(dtype=float)
        fin = np.isfinite(r)
        n_checked += int(fin.sum())
        if fin.any():
            worst[arm] = float(r[fin].max())
            over = np.where(fin & (r >= IDENTITY_RECONSTRUCTION_TOL_BPS))[0]
            for i in over[:20]:
                bad_rows.append({"arm": arm, "row": int(i), "residual_bps": float(r[i])})
    _hard(checks, "Identity reconstruction — |p*W - (1-p)*L - mean| < 0.01 bps on every signed cell",
          not bad_rows,
          {"n_signed_cells_checked": n_checked, "max_residual_by_arm": worst,
           "tolerance_bps": IDENTITY_RECONSTRUCTION_TOL_BPS,
           "cells_outside_tolerance": bad_rows})


# --------------------------------------------------------------------------- M-1 / M-2
def mde_and_span_checks(cell_frames: dict[str, pd.DataFrame], checks: list) -> None:
    """M-1: the band-driving MDE column is the BLOCK one. M-2: spans disclosed on horizon cells."""
    srcs = set()
    iid_present = {}
    for arm, df in cell_frames.items():
        if "mde_source_for_bands" in df.columns:
            srcs |= set(pd.unique(df["mde_source_for_bands"].dropna()))
        iid_present[arm] = bool([c for c in df.columns if "COMPANION_ONLY" in c])
    _hard(checks, "M-1 — every band label is driven by the BLOCK MDE, never the iid form",
          srcs.issubset({MDE_SOURCE_FOR_BANDS}),
          {"observed_mde_sources": sorted(srcs),
           "iid_column_present_and_labelled_companion_only": iid_present})

    span_cov = {}
    for arm, df in cell_frames.items():
        if "span_exact_span_frac" in df.columns:
            has_h = df["h"].notna() if "h" in df.columns else pd.Series(False, index=df.index)
            need = int(has_h.sum())
            got = int((has_h & df["span_exact_span_frac"].notna()).sum())
            span_cov[arm] = {"cells_with_a_horizon": need, "cells_with_span_disclosed": got}
    _info(checks, "M-2 — exact-span subset and span distribution emitted for every horizon cell",
          span_cov)


def no_pass_field_check(cell_frames: dict[str, pd.DataFrame], checks: list) -> None:
    """INFR-016 / L-32: no ``pass`` field, no ``at_or_above_pXX`` boolean, anywhere."""
    offenders = {}
    for arm, df in cell_frames.items():
        bad = [c for c in df.columns
               if c == "pass" or c.startswith("pass_") or "at_or_above_p" in c
               or c.endswith("_passed")]
        if bad:
            offenders[arm] = bad
    _hard(checks, "No `pass` field / no at_or_above_pXX boolean anywhere (INFR-016, L-32)",
          not offenders and NO_PASS_FIELD, {"offending_columns": offenders})


def no_local_accounting_check(checks: list) -> None:
    """The lane rule: no accounting primitive mimicking ``xen.adjudication`` in the experiment dir."""
    banned = ("assemble_realized_bps", "def realized_pnl", "class Ledger", "def book_trade")
    hits = {}
    for p in sorted(SCREEN_CODE_DIR.glob("*.py")):
        if p.name == Path(__file__).name:
            continue        # this module NAMES the banned primitives in order to scan for them
        src = p.read_text()
        found = [b for b in banned if b in src]
        if found:
            hits[p.name] = found
    _hard(checks, "No local accounting primitive (cost is an xen.evaluation overlay only)",
          not hits, {"offenders": hits,
                     "cost_source": "SPDR-014 costs.py -> xen.evaluation (fees + counted "
                                    "funding stamps + 2.0 allowance); spread never charged"})


def spread_prohibition_check(checks: list) -> None:
    """P-20 / L-36: raw ``SpreadBps`` may never be a cost input."""
    hits = {}
    for p in sorted(SCREEN_CODE_DIR.glob("*.py")):
        src = p.read_text()
        if "spread_bps=" in src and "assert_no_spread_cost_input" not in src:
            hits[p.name] = "passes spread_bps into a cost call"
    _hard(checks, "Spread is never charged as a cost (P-20 / L-36)", not hits,
          {"offenders": hits, "disclosure": SPREAD_COST_DISCLOSURE})


# --------------------------------------------------------------------------- derangement
def derangement_check(controls_payload: dict, checks: list) -> None:
    """HARD: every destroy permutation is a DERANGEMENT — fixed-point count 0 (L-28)."""
    counts = {}

    def walk(node, path="") -> None:
        if isinstance(node, dict):
            if "fixed_points_total" in node:
                counts[path or node.get("control") or node.get("tripwire") or "?"] = int(
                    node["fixed_points_total"])
            for k, v in node.items():
                walk(v, f"{path}.{k}" if path else k)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")

    walk(controls_payload)
    _hard(checks, "Derangements — fixed-point count == 0, measured and reported",
          all(v == 0 for v in counts.values()),
          {"fixed_points_by_control": counts, "n_controls_checked": len(counts)})


# --------------------------------------------------------------------------- determinism
def determinism_check(seq_frame: pd.DataFrame, par_frame: pd.DataFrame, checks: list) -> None:
    """HARD: ``--jobs`` parallel output is BIT-IDENTICAL to sequential (§12)."""
    detail = {"n_sequential": int(len(seq_frame)), "n_parallel": int(len(par_frame))}
    if seq_frame.empty or par_frame.empty:
        _hard(checks, "Determinism — parallel is bit-identical to sequential", False,
              {**detail, "error": "one side is empty"})
        return
    a = seq_frame.reindex(sorted(seq_frame.columns), axis=1).reset_index(drop=True)
    b = par_frame.reindex(sorted(par_frame.columns), axis=1).reset_index(drop=True)
    same_cols = list(a.columns) == list(b.columns)
    identical = False
    diffs = []
    if same_cols and len(a) == len(b):
        identical = True
        for c in a.columns:
            x, y = a[c], b[c]
            if x.dtype.kind in "fc" or y.dtype.kind in "fc":
                xa = x.to_numpy(dtype=float, na_value=np.nan)
                ya = y.to_numpy(dtype=float, na_value=np.nan)
                eq = ((xa == ya) | (np.isnan(xa) & np.isnan(ya))).all()
            else:
                eq = x.astype(str).equals(y.astype(str))
            if not eq:
                identical = False
                diffs.append(c)
    detail.update({"columns_match": same_cols, "columns_differing": diffs[:20]})
    _hard(checks, "Determinism — parallel is bit-identical to sequential", identical, detail)


# --------------------------------------------------------------------------- code hash
def code_hashes() -> dict:
    out = {}
    for p in sorted(SCREEN_CODE_DIR.glob("*.py")):
        out[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    joint = hashlib.sha256("".join(f"{k}:{v}" for k, v in sorted(out.items())).encode()).hexdigest()
    return {"per_file_sha256": out, "screen_code_sha256": joint}


# --------------------------------------------------------------------------- run
def run(*, panels: dict[str, pd.DataFrame], cell_frames: dict[str, pd.DataFrame],
        controls_payload: dict, tripwires: list[dict],
        seq_frame: pd.DataFrame | None = None, par_frame: pd.DataFrame | None = None,
        ctrader_max_ts: int | None = None, recompute_universe: bool = True,
        equivalence: dict | None = None) -> dict:
    checks: list = []
    fence_checks(panels, checks)
    ctrader_fence_checks(ctrader_max_ts, checks)
    universe_check(checks, recompute=recompute_universe)
    identity_check(cell_frames, checks)
    mde_and_span_checks(cell_frames, checks)
    no_pass_field_check(cell_frames, checks)
    no_local_accounting_check(checks)
    spread_prohibition_check(checks)
    derangement_check(controls_payload, checks)

    for tw in tripwires:
        sev = "HARD" if tw.get("severity", "").startswith("HARD") else "INFORMATIVE"
        if sev == "HARD":
            _hard(checks, f"{tw.get('tripwire')} held", tw.get("all_held", True), tw)
        else:
            _info(checks, f"{tw.get('tripwire')}", tw)

    par = parity.run()
    _hard(checks, "Parent parity — each arm reproduces its parent's published cells",
          par["all_reproduced"], par)

    gold = golden.run()
    _hard(checks, "Golden traces G1-G6 computed on the self-check side", gold["all_computed"],
          gold)

    if equivalence is not None:
        _hard(checks, "Bootstrap speed path == xen.evaluation.block_bootstrap_ci (bit-identical)",
              bool(equivalence.get("equivalent")), equivalence)

    if seq_frame is not None and par_frame is not None:
        determinism_check(seq_frame, par_frame, checks)
    else:
        _info(checks, "Determinism", "parallel-vs-sequential comparison not requested this run")

    hard = [c for c in checks if c["severity"] == "HARD"]
    failed = [c for c in hard if not c.get("held")]
    payload = {
        "experiment": "SPDR-018",
        "lane": "SPDR — TRAIN-only, 0 counted TEST reads, no family action, no XENA",
        "stage": "stage-2 code-asserted self-check (design §12)",
        "spread_cost_disclosure": SPREAD_COST_DISCLOSURE,
        "checks": checks,
        "n_hard": len(hard), "n_hard_failed": len(failed),
        "hard_all_held": not failed,
        **code_hashes(),
    }
    if failed:
        payload["failed_checks"] = [c["check"] for c in failed]
    return payload


def enforce(payload: dict) -> None:
    """Raise if any HARD check failed — the emission is invalid and must not be interpreted."""
    if not payload.get("hard_all_held"):
        raise IntegrityViolation(
            "HARD integrity checks failed; the emission is invalid: "
            + ", ".join(payload.get("failed_checks", [])))
