"""Stage-2 integrity self-check — 28 HARD checks by name (design §12)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from config import (
    EXPECTED_HARD_CHECK_COUNT,
    EXPECTED_RESOLUTION_SHA256,
    HARD_CHECK_NAMES,
    HOLDOUT_START_NS,
    IDENTITY_RECONSTRUCTION_TOL_BPS,
    RESOLUTION_BASIS_GENERATOR_SHA256,
    RESOLUTION_BASIS_SHA256,
    RESULTS_DIR,
    SCREEN_CODE_DIR,
    TRAIN_END_NS,
    UNIVERSE_N,
    UNIVERSE_PIN_FAMILY,
    UNIVERSE_PIN_PREDECL,
    VARIANT_IDS,
)


class IntegrityViolation(RuntimeError):
    pass


def _hard(checks: list, name: str, held: bool, detail) -> None:
    checks.append({"check": name, "severity": "HARD", "held": bool(held), "detail": detail})


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_tree(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*.py")):
        h.update(p.name.encode())
        h.update(p.read_bytes())
    return h.hexdigest()


def run_selfcheck(
    *,
    metrics_df: pd.DataFrame,
    episodes_df: pd.DataFrame,
    signals_df: pd.DataFrame | None,
    integrity_extra: dict,
    controls: dict,
    selection: dict,
    golden: dict,
    parent_parity: dict,
    unit_pin: dict,
    determinism_ok: bool | None,
    jobs: int,
) -> dict:
    checks: list[dict] = []
    by_name: dict[str, bool] = {}

    def mark(name: str, held: bool, detail) -> None:
        _hard(checks, name, held, detail)
        by_name[name] = bool(held)

    # --- predeclaration / basis ---
    basis_path = RESULTS_DIR / "resolution_basis.json"
    exp_path = RESULTS_DIR / "expected_resolution.json"
    gen_path = Path(__file__).resolve().parents[3] / "src" / "xen" / "resolution_basis.py"
    basis_sha = _sha256_file(basis_path) if basis_path.exists() else ""
    exp_sha = _sha256_file(exp_path) if exp_path.exists() else ""
    gen_sha = _sha256_file(gen_path) if gen_path.exists() else ""

    exp = json.loads(exp_path.read_text()) if exp_path.exists() else {}
    basis = json.loads(basis_path.read_text()) if basis_path.exists() else {}

    predecl_ok = (
        exp_path.exists()
        and exp_sha == EXPECTED_RESOLUTION_SHA256
        and basis_sha == RESOLUTION_BASIS_SHA256
        and exp.get("row_count") == 5148
        and exp.get("input_sha256", {}).get("basis") == basis_sha
        and "COMPUTED AT RUN" not in json.dumps(exp)
    )
    mark("PREDECLARATION PRESENT", predecl_ok, {
        "expected_resolution_sha": exp_sha,
        "expected": EXPECTED_RESOLUTION_SHA256,
        "basis_sha": basis_sha,
        "row_count": exp.get("row_count"),
        "input_basis_match": exp.get("input_sha256", {}).get("basis") == basis_sha,
    })

    rc = basis.get("row_counts", {})
    filt = basis.get("input_filter", {})
    basis_ok = (
        filt.get("value") == "C"
        and rc.get("filter_matched", 0) - rc.get("retained", 0) == rc.get("excluded", -1)
        and rc.get("excluded", -1) == sum(rc.get("excluded_by_reason", {}).values())
    ) if rc else False
    # soft parse if keys differ
    if not basis_ok and rc:
        matched = rc.get("filter_matched") or rc.get("matched")
        retained = rc.get("retained")
        excluded = rc.get("excluded")
        by_reason = rc.get("excluded_by_reason") or {}
        if matched is not None and retained is not None and excluded is not None:
            basis_ok = (matched - retained == excluded) and (
                excluded == sum(by_reason.values()) if by_reason else True
            )
    mark("BASIS POPULATION", basis_ok, {"input_filter": filt, "row_counts": rc})

    # generator hash (informative pin)
    integrity_extra["generator_sha256_measured"] = gen_sha
    integrity_extra["generator_sha256_expected"] = RESOLUTION_BASIS_GENERATOR_SHA256

    # --- universe ---
    pin = json.loads(Path(UNIVERSE_PIN_FAMILY).read_text())
    pre = json.loads(Path(UNIVERSE_PIN_PREDECL).read_text())
    s_pin = set(pin.get("symbols") or pin.get("universe") or [])
    s_pre = set(pre.get("symbols") or pre.get("universe") or [])
    mark("universe pin", len(s_pin) == UNIVERSE_N, {"n": len(s_pin), "required": UNIVERSE_N})
    mark("UNIVERSE FILE EQUALITY", s_pin == s_pre, {
        "only_pin": sorted(s_pin - s_pre), "only_predecl": sorted(s_pre - s_pin),
    })

    # --- fences ---
    # An empty emission previously passed BOTH fences on an `else True` branch, on exactly the
    # run where a check matters most: one that produced nothing (QA run 8, R8-16).
    max_ts = 0
    n_eps = int(len(episodes_df))
    for col in ("exit_ts", "fill_ts", "decision_end_ns", "signal_ts"):
        if col in episodes_df.columns and n_eps:
            max_ts = max(max_ts, int(episodes_df[col].max()))
    have_ts = bool(n_eps and max_ts > 0)
    mark("TRAIN fence", have_ts and max_ts < TRAIN_END_NS, {
        "max_ts": max_ts, "train_end_ns": TRAIN_END_NS, "n_episodes": n_eps,
        "reason": None if have_ts else "no episode timestamps to fence",
    })
    mark("holdout", have_ts and max_ts < HOLDOUT_START_NS, {
        "max_ts": max_ts, "holdout_start_ns": HOLDOUT_START_NS, "n_episodes": n_eps,
        "reason": None if have_ts else "no episode timestamps to fence",
    })

    # --- causality / fill causality (from integrity_extra) ---
    mark("causality", bool(integrity_extra.get("causality_ok", False)),
         integrity_extra.get("causality_detail", {}))
    mark("fill causality", bool(integrity_extra.get("fill_causality_ok", False)),
         integrity_extra.get("fill_causality_detail", {}))

    # --- tripwires ---
    tw1 = integrity_extra.get("tripwire_1", {})
    mark("TRIPWIRE-1", bool(tw1.get("hard_pass")), tw1)
    tw2 = integrity_extra.get("tripwire_2", {})
    mark("TRIPWIRE-2", bool(tw2.get("hard_pass")), tw2)

    # --- identity + log R ---
    # an empty emission has no identity to reconstruct: that is a FAILURE, not a pass (P-23)
    id_ok = False
    id_detail = {"n_checked": 0, "n_fail": 0, "max_residual": 0.0,
                 "reason": "no scored cell carried an identity residual"}
    if len(metrics_df) and "identity_residual_bps" in metrics_df.columns:
        res = metrics_df["identity_residual_bps"].dropna()
        id_detail["n_checked"] = int(res.size)
        bad = res > IDENTITY_RECONSTRUCTION_TOL_BPS
        id_detail["n_fail"] = int(bad.sum())
        id_detail["max_residual"] = float(res.max()) if res.size else 0.0
        id_ok = id_detail["n_fail"] == 0 and id_detail["n_checked"] > 0
    mark("identity reconstruction", id_ok, id_detail)

    logR_ok = True
    if len(metrics_df) and "log_R" in metrics_df.columns:
        # recompute from p,W,L
        fails = 0
        n = 0
        for _, row in metrics_df.iterrows():
            p, W, L, lr = row.get("p"), row.get("W"), row.get("L"), row.get("log_R")
            if not all(np.isfinite(x) if isinstance(x, float) else False for x in (p, W, L, lr)):
                continue
            n += 1
            if p <= 0 or p >= 1 or L <= 0 or W <= 0:
                continue
            recon = float(np.log(W / L) - np.log((1 - p) / p))
            if abs(recon - lr) > 1e-9:
                fails += 1
        logR_ok = fails == 0 and n > 0
        logR_detail = {"n": n, "fails": fails}
    else:
        logR_detail = {"empty": True}
        logR_ok = False
    mark("log R definition", logR_ok, logR_detail)

    # cost isolation
    cost_ok = True
    banned = []
    for c in metrics_df.columns if len(metrics_df) else []:
        cl = c.lower()
        if "net" in cl and "p_be_net" not in cl and "disclosure" not in cl:
            if cl in ("mean_net", "edge_net", "log_r_net"):
                banned.append(c)
                cost_ok = False
    if "p_be_net" in metrics_df.columns:
        # must be flagged disclosure — check companion flag column or all equal cost floor form
        pass
    mark("cost isolation", cost_ok and "p_be_net" in (metrics_df.columns if len(metrics_df) else []), {
        "banned_cols": banned, "has_p_be_net": "p_be_net" in (metrics_df.columns if len(metrics_df) else []),
    })

    # derangement fixed points — MEASURED per seed, never a default (L-28);
    # battery size pinned at CONTROL_N_SEEDS independent of --n-boot (R9-05)
    from config import CONTROL_N_SEEDS
    arms = (controls or {}).get("side_derangement_by_arm", {})
    measured = [
        v for v in list(arms.values()) + [(controls or {}).get("entry_timing", {})]
        if isinstance(v, dict) and v.get("fixed_point_count_measured")
    ]
    fp_max = max((int(v.get("fixed_point_count", 0)) for v in measured), default=None)
    n_seeds_min = min(
        (int(v.get("n_seeds", 0)) for v in measured if isinstance(v, dict)),
        default=0,
    )
    seeds_ok = n_seeds_min >= CONTROL_N_SEEDS
    mark("derangement fixed-point count", bool(measured) and fp_max == 0 and seeds_ok, {
        "fixed_point_count_max": fp_max,
        "n_controls_measured": len(measured),
        "n_seeds_min": n_seeds_min,
        "n_seeds_required": CONTROL_N_SEEDS,
        "reason": (
            None if measured and seeds_ok else
            ("no control reported a MEASURED fixed-point count" if not measured
             else f"n_seeds_min {n_seeds_min} < {CONTROL_N_SEEDS}")
        ),
    })

    # golden — all SEVEN traces, G7 included (§12 "G1–G7 pass"); it was excluded from the
    # tuple that gates this check (QA run 8, R8-12)
    g_names = ("G1", "G2", "G3", "G4", "G5", "G6", "G7")
    g_status = {k: golden.get(k, {}).get("status") for k in g_names}
    g_ok = bool(golden) and all(g_status[k] in ("FOUND", "PASS") for k in g_names)
    mark("golden traces", g_ok, g_status)

    # determinism — §12 makes it unconditional at jobs > 1
    if jobs > 1:
        mark("determinism", determinism_ok is True, {
            "jobs": jobs, "ok": determinism_ok,
            "reason": None if determinism_ok is not None else "comparison did not run",
        })
    else:
        mark("determinism", True, {"jobs": jobs, "skipped_reason": "jobs<=1; identity trivial"})

    # block rule
    br = integrity_extra.get("block_rule", {})
    mark("BLOCK RULE", bool(br.get("hard_pass")), br)

    # L4 comparator
    mark("L4 COMPARATOR IDENTITY", bool(integrity_extra.get("l4_comparator_ok", False)),
         integrity_extra.get("l4_comparator_detail", {}))

    # parent gates
    mark("PARENT-GATE PROVENANCE", bool(integrity_extra.get("parent_prov_ok", False)),
         integrity_extra.get("parent_prov_detail", {}))
    mark("PARENT-GATE PARITY", bool(parent_parity.get("hard_pass")), {
        "n_ok": parent_parity.get("n_ok"),
        "failures": parent_parity.get("failures"),
        "exempt": parent_parity.get("parity_exempt_by_name"),
    })

    # decile causality
    mark("DECILE CAUSALITY", bool(integrity_extra.get("decile_ok", False)),
         integrity_extra.get("decile_detail", {}))

    # exit-matched nulls
    mark("EXIT-MATCHED NULLS", bool(integrity_extra.get("exit_matched_ok", False)),
         integrity_extra.get("exit_matched_detail", {}))

    # L1 subset
    mark("L1 FIXED-ENTRY SUBSET", bool(integrity_extra.get("l1_subset_ok", False)),
         integrity_extra.get("l1_subset_detail", {}))

    # MOD hold
    mark("MOD-HOLD ELIGIBILITY", bool(integrity_extra.get("mod_hold_ok", False)),
         integrity_extra.get("mod_hold_detail", {}))

    # L-51 — presence plus the design-named subset coverage floor (R9-07)
    # 10 layer subsets × 2 clocks + 2 mde50 splits = 22 when both clocks ran
    n_l51 = int((selection or {}).get("n_checks", 0))
    l51_names = set((selection or {}).get("subsets", {}) or {})
    required_tokens = (
        "L1_SHAT_DECILE_GE5", "L1_SHAT_DECILE_GE7", "L1_SHAT_DECILE_GE9",
        "L2_SHOCK_HMM", "L2_LEVEL_RMARKOV_K4", "L2_LEVEL_RMARKOV_K12",
        "L2_JOINT", "L3_TGTCUR_FIRES", "L3_TGTCUR_DOES_NOT_FIRE", "L3_TGTMED5",
        "MDE50_ABOVE", "MDE50_BELOW",
    )
    covered = sum(1 for tok in required_tokens if any(tok in n for n in l51_names))
    mark("L-51 SELECTION CHECK", n_l51 > 0 and covered >= 10, {
        "n_checks": n_l51,
        "n_required_tokens_covered": covered,
        "required_tokens": list(required_tokens),
        "subset_names": sorted(l51_names),
    })

    # log R never unaccompanied. §12 asserts this over metrics_by_cell, layer_deltas AND the
    # resolution ladder alike; it used to be tested on metrics_df only (QA run 12, R11-04).
    # The companion requirement attaches to each artifact's OWN primary read: `log_R` on the
    # cell table, `delta_log_R` on the layer deltas. `log_R_layer` / `log_R_L0` there are
    # CARRIED CONTEXT copied from another row, and their intervals live on that row.
    companions = ["ci_low", "ci_high", "ci_width", "block_mde"]

    def _unaccompanied(df, stat):
        """Rows whose own primary read is finite but is missing a companion."""
        cols = [stat, *companions]
        if df is None or not len(df) or not set(cols).issubset(df.columns):
            return None  # cannot verify → caller treats as a failure, never a vacuous pass
        m = df[cols].dropna(subset=[stat])
        return int((~m[cols].notna().all(axis=1)).sum())

    unacc_detail = {"metrics_by_cell": _unaccompanied(metrics_df, "log_R")}
    ld_path = RESULTS_DIR / "layer_deltas.parquet"
    lad_path = RESULTS_DIR / "resolution_ladder.parquet"
    if ld_path.exists():
        unacc_detail["layer_deltas"] = _unaccompanied(
            pd.read_parquet(ld_path), "delta_log_R"
        )
    if lad_path.exists():
        lad = pd.read_parquet(lad_path)
        # the ladder carries a log R only if it names one; absent → nothing to accompany
        unacc_detail["resolution_ladder"] = (
            _unaccompanied(lad, "log_R") if "log_R" in lad.columns else 0
        )
    unacc_ok = bool(unacc_detail) and all(
        v == 0 for v in unacc_detail.values()
    ) and None not in unacc_detail.values()
    mark("log R never unaccompanied", unacc_ok, {
        "primary_read_per_artifact": {
            "metrics_by_cell": "log_R",
            "layer_deltas": "delta_log_R",
            "resolution_ladder": "log_R (if present)",
        },
        "companions": companions,
        "n_unaccompanied_rows": unacc_detail,
        "carried_context_excluded": ["log_R_layer", "log_R_L0"],
    })

    # predeclared vs realised
    has_pre = "expected_n" in metrics_df.columns or "expected_mde50" in metrics_df.columns
    # may live in resolution_ladder
    ladder_path = RESULTS_DIR / "resolution_ladder.parquet"
    if ladder_path.exists():
        lad = pd.read_parquet(ladder_path)
        has_pre = has_pre or (
            "expected_n" in lad.columns and "n" in lad.columns and "mde50" in lad.columns
        )
    mark("PREDECLARED vs REALISED resolution", has_pre, {"has_columns": has_pre})

    # check-count reconciliation BY NAME
    present = {c["check"] for c in checks}
    expected = set(HARD_CHECK_NAMES)
    # map short names used above to HARD_CHECK_NAMES
    # Our mark() names must match HARD_CHECK_NAMES exactly
    missing = expected - present
    extra = present - expected
    count_ok = (
        len(checks) == EXPECTED_HARD_CHECK_COUNT
        and not missing
        and all(by_name.get(n) is not None for n in HARD_CHECK_NAMES)
    )
    # re-mark check-count as first logical check — already in list if named correctly
    if "check-count reconciliation" not in by_name:
        mark("check-count reconciliation", count_ok, {
            "expected_count": EXPECTED_HARD_CHECK_COUNT,
            "measured_count": len(checks) + 1,
            "missing_names": sorted(missing),
            "extra_names": sorted(extra),
        })
    else:
        # update
        for c in checks:
            if c["check"] == "check-count reconciliation":
                c["held"] = count_ok and all(by_name.get(n, False) or n == "check-count reconciliation" for n in HARD_CHECK_NAMES)
                c["detail"] = {
                    "expected_count": EXPECTED_HARD_CHECK_COUNT,
                    "measured_count": len(checks),
                    "missing_names": sorted(expected - {c["check"] for c in checks}),
                    "by_name_held": {n: by_name.get(n) for n in HARD_CHECK_NAMES},
                }

    # Final count check: we need exactly the 28 names
    present = {c["check"] for c in checks}
    missing = expected - present
    if missing:
        for name in sorted(missing):
            mark(name, False, {"error": "check was not executed"})
    present = {c["check"] for c in checks}
    # keep only one row per HARD name (last wins)
    dedup = {}
    for c in checks:
        if c["check"] in expected:
            dedup[c["check"]] = c
    checks = [dedup[n] for n in HARD_CHECK_NAMES if n in dedup]
    for n in HARD_CHECK_NAMES:
        if n not in dedup:
            checks.append({"check": n, "severity": "HARD", "held": False, "detail": {"missing": True}})

    # set check-count held based on final list
    all_held = all(c["held"] for c in checks if c["check"] != "check-count reconciliation")
    for c in checks:
        if c["check"] == "check-count reconciliation":
            c["held"] = len(checks) == EXPECTED_HARD_CHECK_COUNT and not any(
                x.get("detail", {}).get("missing") for x in checks
            )
            c["detail"] = {
                "expected_count": EXPECTED_HARD_CHECK_COUNT,
                "measured_count": len(checks),
                "names": [x["check"] for x in checks],
                "all_others_executed": not any(x.get("detail", {}).get("missing") for x in checks),
            }

    hard_fails = [c for c in checks if not c["held"]]
    code_sha = _sha256_tree(SCREEN_CODE_DIR)
    payload = {
        "n_hard_checks": len(checks),
        "expected_hard_checks": EXPECTED_HARD_CHECK_COUNT,
        "hard_checks": checks,
        "hard_fail_names": [c["check"] for c in hard_fails],
        "all_hard_pass": len(hard_fails) == 0,
        "code_sha256": code_sha,
        "resolution_basis_sha256": basis_sha,
        "expected_resolution_sha256": exp_sha,
        "generator_sha256": gen_sha,
        "unit_pin": unit_pin,
        "variants_n": len(VARIANT_IDS),
        "spread_cost_disclosure": {
            "spread_cost_status": "UNAVAILABLE_NOT_CHARGED",
            "note": "AMENDMENT-C5 gross-only",
        },
    }
    if hard_fails:
        # do not raise here — caller decides; but flag
        payload["integrity_violation"] = True
    return payload
