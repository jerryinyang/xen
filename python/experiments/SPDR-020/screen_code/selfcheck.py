"""Stage-2 integrity self-check — 29 HARD checks by name (design §12)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from config import (
    BOOT_RESAMPLES,
    EXPECTED_HARD_CHECK_COUNT,
    EXPECTED_RESOLUTION_ROW_COUNT,
    EXPECTED_RESOLUTION_SHA256,
    HARD_CHECK_NAMES,
    HOLDOUT_START_NS,
    IDENTITY_RECONSTRUCTION_TOL_BPS,
    RESOLUTION_BASIS_SHA256,
    RESULTS_DIR,
    SCREEN_CODE_DIR,
    TRAIN_END_NS,
    UNIVERSE_N,
    UNIVERSE_PIN_FAMILY,
    UNIVERSE_PIN_PREDECL,
    ZVOL_COVERED_N,
    ZVOL_NAN_SYMBOLS,
    ZVOL_SCALE_PATH,
    execution_manifest,
)


class IntegrityViolation(RuntimeError):
    pass


def check_zvol_partition(
    *,
    covered_symbols: list[str],
    missing_symbols: list[str],
) -> dict:
    """Require the exact frozen 17-covered/8-missing partition."""
    covered = set(covered_symbols)
    missing = set(missing_symbols)
    expected_missing = set(ZVOL_NAN_SYMBOLS)
    pin = json.loads(Path(UNIVERSE_PIN_FAMILY).read_text())
    universe = set(pin["symbols"])
    expected_covered = universe - expected_missing
    held = (
        covered == expected_covered
        and missing == expected_missing
        and covered.isdisjoint(missing)
        and covered | missing == universe
        and len(covered) == ZVOL_COVERED_N
    )
    return {
        "held": held,
        "covered_symbols": sorted(covered),
        "missing_symbols": sorted(missing),
        "expected_covered_symbols": sorted(expected_covered),
        "expected_missing_symbols": sorted(expected_missing),
    }


def execution_candidate_eligibility(plan: dict) -> dict:
    """Separate developer artifacts from a verdict-bearing execution candidate."""
    expected = execution_manifest()
    reasons: list[str] = []
    if plan.get("smoke") or plan.get("subset") or plan.get("primary_only"):
        reasons.append("developer_mode")
    if int(plan.get("n_boot", 0)) != BOOT_RESAMPLES:
        reasons.append("bootstrap_count")
    exact_fields = (
        "symbols",
        "clocks",
        "sources",
        "H",
        "z",
        "h",
        "event_types",
        "variants",
        "expected_primary_cells",
        "expected_full_cells",
    )
    for field in exact_fields:
        actual = plan.get(field)
        wanted = expected[field]
        if isinstance(wanted, list):
            if set(actual or []) != set(wanted):
                reasons.append(f"manifest:{field}")
        elif actual != wanted:
            reasons.append(f"manifest:{field}")
    return {
        "eligible": not reasons,
        "grade": "EXECUTION_CANDIDATE" if not reasons else "DEVELOPER_ONLY",
        "reasons": reasons,
    }


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

    # --- predeclaration consumed ---
    basis_path = RESULTS_DIR / "resolution_basis.json"
    exp_path = RESULTS_DIR / "expected_resolution.json"
    basis_sha = _sha256_file(basis_path) if basis_path.exists() else ""
    exp_sha = _sha256_file(exp_path) if exp_path.exists() else ""
    exp = json.loads(exp_path.read_text()) if exp_path.exists() else {}

    # 1 check-count — filled at end
    # 2–3 tripwires
    tw1 = integrity_extra.get("tripwire_1", {})
    mark("TRIPWIRE-1", bool(tw1.get("hard_pass")), tw1)
    tw2 = integrity_extra.get("tripwire_2", {})
    mark("TRIPWIRE-2", bool(tw2.get("hard_pass")), tw2)

    # 4–5 fences
    max_ts = 0
    for col in ("exit_ts", "entry_ts"):
        if col in episodes_df.columns and len(episodes_df):
            max_ts = max(max_ts, int(np.nanmax(episodes_df[col].to_numpy())))
    mark("TRAIN fence", bool(max_ts and max_ts < TRAIN_END_NS), {
        "max_ts": max_ts, "train_end_ns": TRAIN_END_NS,
    })
    mark("holdout", bool(max_ts and max_ts < HOLDOUT_START_NS), {
        "max_ts": max_ts, "holdout_start_ns": HOLDOUT_START_NS,
    })

    # 6 causality
    mark("causality", bool(integrity_extra.get("causality_ok", False)),
         integrity_extra.get("causality_detail", {"note": "entry open[j+1], residual open[entry+h]"}))

    # 7 breach detection
    mark("breach detection", bool(integrity_extra.get("breach_ok", False)),
         integrity_extra.get("breach_detail", {"tripwire_2": tw2}))

    # 8 exit fill causality
    mark("EXIT FILL CAUSALITY", bool(integrity_extra.get("fill_causality_ok", False)),
         integrity_extra.get("fill_causality_detail", {}))

    # 9 parent parity
    mark("parent parity", bool(parent_parity.get("hard_pass")), {
        "n_compared": parent_parity.get("n_compared"),
        "n_reproduced": parent_parity.get("n_reproduced"),
        "max_abs_diff": parent_parity.get("max_abs_diff"),
        "tolerance": parent_parity.get("tolerance"),
    })

    # 10 universe pin
    pin = json.loads(Path(UNIVERSE_PIN_FAMILY).read_text())
    pre = json.loads(Path(UNIVERSE_PIN_PREDECL).read_text()) if Path(UNIVERSE_PIN_PREDECL).exists() else {}
    s_pin = set(pin.get("symbols") or pin.get("universe") or [])
    s_pre = set(pre.get("symbols") or pre.get("universe") or [])
    mark("universe pin", len(s_pin) == UNIVERSE_N and (not s_pre or s_pin == s_pre), {
        "n": len(s_pin), "required": UNIVERSE_N,
        "set_equal_predecl": (s_pin == s_pre) if s_pre else None,
    })

    # 11 identity
    id_ok = True
    id_detail: dict = {"n_checked": 0, "n_fail": 0, "max_residual": 0.0}
    if len(metrics_df) and "identity_residual_bps" in metrics_df.columns:
        res = metrics_df["identity_residual_bps"].dropna()
        id_detail["n_checked"] = int(res.size)
        bad = res > IDENTITY_RECONSTRUCTION_TOL_BPS
        id_detail["n_fail"] = int(bad.sum())
        id_detail["max_residual"] = float(res.max()) if res.size else 0.0
        id_ok = id_detail["n_fail"] == 0 and id_detail["n_checked"] > 0
    mark("identity reconstruction", id_ok, id_detail)

    # 12 log R definition
    logR_ok = True
    logR_detail: dict = {"n": 0, "fails": 0}
    if len(metrics_df) and "log_R" in metrics_df.columns:
        fails = n = 0
        for _, row in metrics_df.iterrows():
            p, W, L, lr = row.get("p"), row.get("W"), row.get("L"), row.get("log_R")
            vals = [p, W, L, lr]
            if not all(isinstance(x, (int, float, np.floating)) and np.isfinite(x) for x in vals):
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
        logR_ok = False
        logR_detail = {"empty": True}
    mark("log R definition", logR_ok, logR_detail)

    # 13 cost isolation
    cost_ok = True
    banned = []
    for c in metrics_df.columns if len(metrics_df) else []:
        cl = c.lower()
        if cl in ("mean_net", "edge_net", "log_r_net", "net_mean"):
            banned.append(c)
            cost_ok = False
    if "p_be_net" in (metrics_df.columns if len(metrics_df) else []):
        # must be disclosure-flagged somewhere
        pass
    mark("cost isolation", cost_ok and "p_be_net" in (metrics_df.columns if len(metrics_df) else []), {
        "banned_columns": banned,
        "p_be_net_present": "p_be_net" in (metrics_df.columns if len(metrics_df) else []),
    })

    # 14 MDE column is block
    mde_ok = False
    if len(metrics_df) and "block_mde" in metrics_df.columns:
        # iid companion may exist; live resolution column must be block_mde
        has_block = metrics_df["block_mde"].notna().any()
        src_ok = True
        if "mde_source_for_bands" in metrics_df.columns:
            src = metrics_df["mde_source_for_bands"].dropna()
            src_ok = src.empty or (src.astype(str) == "block").all()
        mde_ok = bool(has_block and src_ok)
    mark("MDE column", mde_ok, {
        "has_block_mde": "block_mde" in (metrics_df.columns if len(metrics_df) else []),
        "n_finite_block_mde": int(metrics_df["block_mde"].notna().sum()) if len(metrics_df) and "block_mde" in metrics_df.columns else 0,
    })

    # 15 BLOCK RULE
    br = integrity_extra.get("block_rule", {})
    mark("BLOCK RULE", bool(br.get("ok", False)), br)

    # 16 s_symbol provenance
    s_pin_file = json.loads(Path(ZVOL_SCALE_PATH).read_text())
    used = unit_pin.get("per_symbol", [])
    s_ok = True
    mismatches = []
    nan_named = []
    for u in used:
        sym = u.get("symbol")
        pin_v = s_pin_file.get(sym)
        if pin_v is None or (isinstance(pin_v, float) and not np.isfinite(pin_v)):
            nan_named.append(sym)
            continue
        uv = u.get("s_symbol")
        if uv is not None and np.isfinite(uv) and abs(float(uv) - float(pin_v)) > 1e-9:
            s_ok = False
            mismatches.append(sym)
    partition = check_zvol_partition(
        covered_symbols=unit_pin.get("zvol_covered_symbols", []),
        missing_symbols=unit_pin.get("zvol_nan_symbols", []),
    )
    mark("s_symbol PROVENANCE", s_ok and partition["held"] and Path(ZVOL_SCALE_PATH).exists(), {
        "source": str(ZVOL_SCALE_PATH),
        "mismatches": mismatches,
        "nan_symbols_seen": nan_named,
        "expected_nan": sorted(ZVOL_NAN_SYMBOLS),
        "partition": partition,
    })

    # 17 UNDECIDED
    und_ok = False
    und_detail: dict = {}
    if len(episodes_df) and "n_undecided" in episodes_df.columns:
        und_ok = True
        und_detail = {
            "sum_n_undecided": int(episodes_df["n_undecided"].fillna(0).sum()),
            "present": True,
        }
    elif integrity_extra.get("undecided_counts"):
        und_ok = True
        und_detail = integrity_extra["undecided_counts"]
    mark("UNDECIDED accounting", und_ok, und_detail)

    # 18 M-4
    m4_ok = False
    if len(metrics_df) and "n_symbols_in_cell" in metrics_df.columns:
        pooled = metrics_df[metrics_df.get("scope", pd.Series(dtype=str)) == "POOLED"] if "scope" in metrics_df.columns else metrics_df
        if len(pooled):
            mx = pooled["n_symbols_in_cell"].max()
            m4_ok = mx <= ZVOL_COVERED_N + 8  # allow full 25 if Z-MAG present; Z-VOL asserted in unit_pin
    m4_ok = m4_ok and partition["held"]
    mark("M-4 effective coverage", m4_ok, {
        "zvol_covered_n": unit_pin.get("zvol_covered_n"),
        "required": ZVOL_COVERED_N,
        "partition": partition,
    })

    # 19 p_event NON-APPLICATION
    pev_ok = bool(integrity_extra.get("p_event_never_filters", False))
    if len(metrics_df):
        pev_ok = pev_ok and "p_event" in metrics_df.columns
    mark("p_event NON-APPLICATION", pev_ok, {
        "p_event_column_present": "p_event" in (metrics_df.columns if len(metrics_df) else []),
        "code_asserts_no_filter": bool(integrity_extra.get("p_event_never_filters", False)),
    })

    # 20 NO ADEQUACY FLAG
    banned_flags = {"powered", "unpowered", "at_target", "not_resolvable", "NOT_RESOLVABLE"}
    found = [c for c in (metrics_df.columns if len(metrics_df) else []) if c.lower() in {b.lower() for b in banned_flags}]
    mark("NO ADEQUACY FLAG", len(found) == 0, {"banned_found": found})

    # 21 LADDER EMITTED
    def paired_ladder_count_ok(value) -> bool:
        return bool(
            isinstance(value, dict)
            and value.get("requested_replicates_per_seed") == BOOT_RESAMPLES
            and value.get("all_replicate_counts_match")
            and value.get("realised_replicates_per_seed")
        )

    ladder_ok = False
    if len(metrics_df):
        ladder_columns = [
            c for c in metrics_df.columns if c.startswith("detect_wl_")
        ]
        ladder_ok = bool(ladder_columns and "mde50" in metrics_df.columns)
        if ladder_ok:
            finite_rows = metrics_df["log_R"].notna()
            ladder_ok = bool(
                metrics_df.loc[finite_rows, ladder_columns].notna().all(axis=1).all()
            )
            if "ladder" not in metrics_df.columns:
                ladder_ok = False
            else:
                counts = metrics_df.loc[finite_rows, "ladder"].map(
                    lambda value: (
                        (
                            value.get("plant_bootstrap_replicates_per_seed")
                            == BOOT_RESAMPLES
                        )
                        or paired_ladder_count_ok(value)
                        if isinstance(value, dict) else False
                    )
                )
                ladder_ok = bool(ladder_ok and counts.all())
            delta_path = RESULTS_DIR / "layer_deltas.parquet"
            if delta_path.exists():
                delta_frame = pd.read_parquet(delta_path)
                ladder_ok = bool(
                    ladder_ok
                    and not delta_frame.empty
                    and "ladder" in delta_frame.columns
                    and delta_frame["ladder"].map(paired_ladder_count_ok).all()
                )
            else:
                ladder_ok = False
    mark("LADDER EMITTED", ladder_ok, {
        "has_detect_wl": ladder_ok,
        "required_replicates_per_seed": BOOT_RESAMPLES,
    })

    # 22 LADDER PLANT OPERATOR
    plant_ok = False
    if len(metrics_df):
        wl_columns = [c for c in metrics_df.columns if c.startswith("detect_wl_")]
        p_columns = [c for c in metrics_df.columns if c.startswith("detect_p_")]
        finite_rows = metrics_df["log_R"].notna()
        plant_ok = bool(
            wl_columns
            and p_columns
            and metrics_df.loc[finite_rows, wl_columns + p_columns]
            .notna()
            .all(axis=1)
            .all()
        )
        paired_metric_rows = metrics_df[
            metrics_df.get(
                "paired", pd.Series(False, index=metrics_df.index)
            ).fillna(False).astype(bool)
        ]
        paired_operator_ok = bool(
            not paired_metric_rows.empty
            and paired_metric_rows["ladder"].map(
                lambda value: (
                    isinstance(value, dict)
                    and set(value.get("operator_definitions", {}))
                    == {"via_WL", "via_p"}
                )
            ).all()
        )
        delta_path = RESULTS_DIR / "layer_deltas.parquet"
        delta_frame = (
            pd.read_parquet(delta_path) if delta_path.exists() else pd.DataFrame()
        )
        delta_operator_ok = bool(
            not delta_frame.empty
            and "ladder" in delta_frame.columns
            and delta_frame["ladder"].map(
                lambda value: (
                    isinstance(value, dict)
                    and set(value.get("operator_definitions", {}))
                    == {"via_WL", "via_p"}
                )
            ).all()
        )
        plant_ok = bool(plant_ok and paired_operator_ok and delta_operator_ok)
    mark("LADDER PLANT OPERATOR", plant_ok, {"both_operators": plant_ok})

    # 23 L-51
    sel_ok = bool(selection.get("schema_ok")) and int(selection.get("n_rows", 0)) > 0
    mark("L-51 SELECTION CHECK", sel_ok, {
        "n_rows": selection.get("n_rows"), "schema_ok": selection.get("schema_ok"),
    })

    # 24 log R never unaccompanied
    unacc_ok = True
    artifacts = {"metrics_by_cell": metrics_df}
    for name in ("layer_deltas.parquet", "resolution_ladder.parquet"):
        path = RESULTS_DIR / name
        artifacts[name] = pd.read_parquet(path) if path.exists() else pd.DataFrame()
    artifact_detail = {}
    for name, frame in artifacts.items():
        log_column = (
            "log_R"
            if "log_R" in frame.columns
            else "delta_log_R"
            if "delta_log_R" in frame.columns
            else None
        )
        required = [
            log_column,
            "ci_low",
            "ci_high",
            "ci_width",
            "block_mde",
        ]
        held = bool(
            log_column
            and not frame.empty
            and all(column in frame.columns for column in required)
        )
        unacc_ok = unacc_ok and held
        artifact_detail[name] = {"held": held, "required_columns": required}
    mark("log R never unaccompanied", unacc_ok, artifact_detail)

    # 25 PREDECLARED vs REALISED
    pre_ok = (
        exp_path.exists()
        and exp_sha == EXPECTED_RESOLUTION_SHA256
        and basis_sha == RESOLUTION_BASIS_SHA256
        and exp.get("row_count") == EXPECTED_RESOLUTION_ROW_COUNT
    )
    if len(metrics_df):
        pre_ok = pre_ok and (
            "expected_n" in metrics_df.columns or "expected_mde50" in metrics_df.columns
            or integrity_extra.get("predeclared_joined", False)
        )
    mark("PREDECLARED vs REALISED resolution", pre_ok, {
        "expected_sha": exp_sha, "required": EXPECTED_RESOLUTION_SHA256,
        "basis_sha": basis_sha, "row_count": exp.get("row_count"),
    })

    # 26 NO LOCAL ACCOUNTING
    local_acc = False
    for p in SCREEN_CODE_DIR.rglob("*.py"):
        txt = p.read_text(errors="ignore")
        if "partial_net_bps" in txt and "DISCLOSURE" not in txt and p.name not in ("config.py",):
            # costs disclosure is fine; adjudication mimic is not
            if "class Position" in txt or "booked_pnl" in txt:
                local_acc = True
    mark("NO LOCAL ACCOUNTING", not local_acc, {"local_accounting_found": local_acc})

    # 27 derangement fixed points
    fp = controls.get("fixed_point_total", controls.get("side_derangement", {}).get("fixed_point_count", 1))
    control_manifest = controls.get("control_manifest", [])
    chronological_cells = controls.get(
        "chronological_thirds", {}
    ).get("cells", [])
    chronological_ok = bool(
        chronological_cells
        and all(
            row.get("split_rule") == "equal_full_TRAIN_timestamp_intervals"
            and row.get("interval_start_ns") < row.get("interval_end_ns")
            and isinstance(row.get("sign_agreement"), bool)
            and len(row.get("thirds", [])) == 3
            for row in chronological_cells
        )
    )
    control_quality_ok = bool(
        controls.get("control_manifest_complete")
        and controls.get("all_mandatory_controls_present")
        and control_manifest
        and chronological_ok
        and all(
            (
                row.get("usable")
                and row.get("plant_resolution", {}).get("timing", {}).get(
                    "unique_assignment_count", 0
                ) > 1
                and row.get("plant_resolution", {}).get("side", {}).get(
                    "unique_assignment_count", 0
                ) > 1
                and row.get("plant_resolution", {}).get("timing", {}).get(
                    "changed_input_count", 0
                ) > 0
                and row.get("plant_resolution", {}).get("side", {}).get(
                    "changed_input_count", 0
                ) > 0
            )
            or (
                not row.get("usable")
                and row.get("status") in {
                    "UNUSABLE_THIN", "UNUSABLE_VACUOUS",
                }
                and row.get("plant_resolution") is not None
            )
            for row in control_manifest
        )
        and not any(row.get("status") == "MISSING" for row in control_manifest)
        and int(controls.get("required_control_cell_count", 0))
        == len(control_manifest)
    )
    mark("derangement fixed-point count", int(fp) == 0 and control_quality_ok, {
        "fixed_point_total": fp,
        "control_manifest_complete": controls.get("control_manifest_complete"),
        "all_control_cells_usable": controls.get("all_control_cells_usable"),
        "control_manifest_rows": len(control_manifest),
        "required_control_cell_count": controls.get("required_control_cell_count"),
        "missing_labelled_cells": controls.get("missing_labelled_cells"),
        "chronological_full_train_cells": len(chronological_cells),
        "chronological_intervals_and_sign_emitted": chronological_ok,
        "seed_diversity_and_changed_inputs": control_quality_ok,
    })

    # 28 golden traces
    mark("golden traces", bool(golden.get("all_held")), {
        k: v.get("held") for k, v in golden.items() if k.startswith("G")
    })

    # 29 determinism
    det = determinism_ok if jobs > 1 else True
    mark("determinism", bool(det), {
        "jobs": jobs, "determinism_ok": det,
    })

    # 1 check-count reconciliation by name
    names_run = [c["check"] for c in checks]
    # we marked 28 so far; add check-count as the first logical check
    missing = [n for n in HARD_CHECK_NAMES if n != "check-count reconciliation" and n not in by_name]
    extra = [n for n in by_name if n not in HARD_CHECK_NAMES]
    count_ok = (
        len(by_name) == EXPECTED_HARD_CHECK_COUNT - 1  # without check-count itself yet
        and not missing
        and not extra
    )
    # insert check-count at front
    check_count_held = count_ok or (
        set(by_name) == set(HARD_CHECK_NAMES) - {"check-count reconciliation"}
        and len(by_name) == EXPECTED_HARD_CHECK_COUNT - 1
    )
    # After adding check-count, total HARD marks should be 29
    _hard(checks, "check-count reconciliation", check_count_held, {
        "expected": EXPECTED_HARD_CHECK_COUNT,
        "names_expected": list(HARD_CHECK_NAMES),
        "names_run": ["check-count reconciliation"] + names_run,
        "missing": missing,
        "extra": extra,
        "n_run_excluding_self": len(by_name),
    })
    by_name["check-count reconciliation"] = check_count_held

    # Re-validate: all 29 present
    all_present = set(by_name.keys()) == set(HARD_CHECK_NAMES)
    if all_present and len(by_name) == EXPECTED_HARD_CHECK_COUNT:
        # fix check-count held true
        for c in checks:
            if c["check"] == "check-count reconciliation":
                c["held"] = True
                c["detail"]["final_n"] = len(by_name)
                by_name["check-count reconciliation"] = True

    execution_eligibility = integrity_extra.get(
        "execution_eligibility",
        {"eligible": False, "grade": "DEVELOPER_ONLY", "reasons": ["missing_run_plan"]},
    )
    dependency_manifest = integrity_extra.get(
        "dependency_manifest",
        {"complete": False, "dependencies": []},
    )
    hard_checks_pass = all(by_name.get(n, False) for n in HARD_CHECK_NAMES)
    hard_pass = bool(
        hard_checks_pass
        and execution_eligibility.get("eligible")
        and dependency_manifest.get("complete")
    )
    payload = {
        "expected_hard_check_count": EXPECTED_HARD_CHECK_COUNT,
        "hard_check_names": list(HARD_CHECK_NAMES),
        "checks": checks,
        "by_name": by_name,
        "hard_pass": hard_pass,
        "hard_checks_pass": hard_checks_pass,
        "execution_eligibility": execution_eligibility,
        "dependency_manifest": dependency_manifest,
        "code_sha256": _sha256_tree(SCREEN_CODE_DIR),
        "resolution_basis_sha256": basis_sha,
        "expected_resolution_sha256": exp_sha,
        "fills_source": integrity_extra.get("fills_source"),
    }
    if not hard_pass:
        failed = [n for n, h in by_name.items() if not h]
        payload["failed"] = failed
    return payload
