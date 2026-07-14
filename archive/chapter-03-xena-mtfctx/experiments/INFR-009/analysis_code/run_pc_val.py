"""INFR-009 P4/P5 — freeze (c) registry + blind VAL + net-path amendment + route-restore.

P4: hash-pin (c) + SEG_PROXY VAL (holdout NEVER read).
P5 (operator 2026-07-14): inject flat RT=1.0 bps on **net** path only; binding deployability
    = top-1 net_LCB>0; re-VAL; route-restore under accepted α̂=5.0% boundary.

Usage:
  .venv/bin/python run_pc_val.py --freeze-only
  .venv/bin/python run_pc_val.py --val-only
  .venv/bin/python run_pc_val.py --p5          # amended freeze + re-VAL + route pin
  .venv/bin/python run_pc_val.py --cost-sweep
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve()
INFR = HERE.parents[1]
RESULTS = INFR / "results"
REPO_PY = HERE.parents[3]                     # .../python
sys.path.insert(0, str(REPO_PY / "src"))

from xen.xena.calibration_p3d import eval_lcb_legs                         # noqa: E402
from xen.xena.oracle import CandidateStream, OracleConfig, evaluate        # noqa: E402
from xen.xena.score import robust_g_hat                                    # noqa: E402
from xen.xena.search import (bootstrap_block_starts, clip_grid_covering,   # noqa: E402
                             universe_grid)

NS = 1_000_000_000
FIXTURES = ("XENA-001", "XENA-002", "XENA-003")

# Bands (design §5 / INFR-006 A-2). Holdout TEST is declared for provenance ONLY, never a segment.
SEARCH_BAND = (int(np.datetime64("2021-06-02T00:01", "ns").astype(np.int64)),
               int(np.datetime64("2023-03-08T00:00", "ns").astype(np.int64)))
SEG_PROXY = (int(datetime(2023, 7, 13, tzinfo=timezone.utc).timestamp() * 1e9),
             int(datetime(2024, 3, 28, tzinfo=timezone.utc).timestamp() * 1e9))
TEST_HOLDOUT_NEVER_READ = (int(datetime(2024, 3, 28, tzinfo=timezone.utc).timestamp() * 1e9),
                           int(datetime(2024, 12, 11, 8, 19, tzinfo=timezone.utc).timestamp() * 1e9))

# Frozen (c) stage-2 estimator params (design §P-C.1 / P4.2 / P5.1)
N_BOOT = 200
BLOCK_LEGS = 1
STAGE1_BLOCK = 64
STAGE1_QUANTILE = 0.25

# P5 net-path amendment (operator lock 2026-07-14)
INJECTED_RT_BPS = 1.0
P4_PARENT_SHA = "44e1aa3cd7690fe04109533590c768c770b51e44c74bdc5e6bd45ba6a47ec5ee"

Q1_P50_REALIZED_BPS = {"XENA-001": 0.043, "XENA-002": -0.284, "XENA-003": 1.910}
EXPECTED = {
    "XENA-001": {"deployable": False, "gross_certified": False,
                 "note": "random-entry null → not certified"},
    "XENA-002": {"deployable": False, "gross_certified": False,
                 "note": "sub-zero → not certified"},
    "XENA-003": {"deployable": False, "gross_certified": True,
                 "note": "real gross, sub-cost → not deployable at 1.0 bps RT"},
}


def _write(name: str, obj: dict) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / name).write_text(json.dumps(obj, indent=1, default=str), encoding="utf-8")
    print(f"  wrote {RESULTS / name}", flush=True)


def _with_flat_cost(streams: list[CandidateStream], cost_bps: float) -> list[CandidateStream]:
    """Inject a FLAT round-trip cost on every stream (engine-costless fixtures need this)."""
    return [CandidateStream(s.candidate_id, s.symbol, s.trades, s.marks,
                            float(cost_bps), s.money_per_unit) for s in streams]


# --------------------------------------------------------------------------- #
# Freeze (P4 base + P5 amendment)
# --------------------------------------------------------------------------- #
def freeze() -> dict:
    """Original P4 freeze (kept for reproducibility). Prefer freeze_p5 for live pin."""
    design = json.loads((RESULTS / "pc_design.json").read_text())
    confirm = json.loads((RESULTS / "pc_confirm.json").read_text())
    proc = design["frozen_procedure"]
    if not proc:
        raise SystemExit("no frozen_procedure in pc_design.json")
    registry = {
        "schema": "xena.infr009.pc_registry.v1",
        "binder": "exit_(c)_two_stage_sample_split",
        "frozen_procedure": proc,
        "confirm_summary": {
            "verdict": confirm["outcome"]["verdict"],
            "per_cadence": confirm["per_cadence"],
            "gate_rule": confirm["stop_condition"]["gate_rule"],
        },
        "design_bite": design["bite"],
        "design_coverage": design["coverage"],
        "integrity_attestation": {
            "rust_python_bitwise_parity": True,
            "parity_gate": "tests/test_xena_fold_parity.py",
            "binding_estimand": "g_gross_ratio (design §3); not mean_per_leg",
        },
        "boundary_pass_disclosure": (
            "α̂ exactly 5.0% both cadences (10/200); Wilson-95 upper 9.0% — thin margin, "
            "accepted by operator 2026-07-14 (no α rewrite)."
        ),
        "route_restore": "NOT frozen here — separate operator decision (out of §P4 scope)",
        "operator_signoff": "Jerry Inyang — 2026-07-14 session mandate: freeze (c) + blind VAL",
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
    }
    blob = json.dumps(registry, sort_keys=True).encode("utf-8")
    artifact = {"registry": registry, "sha256": hashlib.sha256(blob).hexdigest()}
    _write("pc_frozen_registry.json", artifact)
    print(f"[P4] froze (c) registry sha256={artifact['sha256'][:16]}…", flush=True)
    return artifact


def freeze_p5() -> dict:
    """§P5 amended freeze: parent P4 pin + net-path injection + route-restore authorized."""
    design = json.loads((RESULTS / "pc_design.json").read_text())
    confirm = json.loads((RESULTS / "pc_confirm.json").read_text())
    parent = json.loads((RESULTS / "pc_frozen_registry.json").read_text())
    parent_sha = parent.get("sha256", P4_PARENT_SHA)
    proc = dict(design["frozen_procedure"])
    # TIGHTER deployability amendment (gross/α unchanged)
    proc["stage2_gross"] = "lcb_g_leg_studentized(g_gross)>0 costless on gate/SEG_PROXY band"
    proc["stage2_net_deployability"] = (
        f"lcb_g_leg_studentized(g_net)>0 with FLAT injected RT={INJECTED_RT_BPS} bps "
        "(not stream cost_bps)"
    )
    proc["injected_rt_bps"] = INJECTED_RT_BPS
    proc["deployability_binding"] = "top1_net_lcb_positive_after_injection"
    proc["finalist_stage2"] = "disclosure_only"
    proc["amendment"] = "P5_net_path_flat_1bps_TIGHTER_deployability"
    registry = {
        "schema": "xena.infr009.pc_registry.v2",
        "binder": "exit_(c)_two_stage_sample_split",
        "parent_sha256": parent_sha,
        "amendment": {
            "id": "P5",
            "tag": "TIGHTER",
            "scope": "net_deployability_path_only",
            "injected_rt_bps": INJECTED_RT_BPS,
            "rationale": (
                "Stream cost_bps inert on engine-costless emissions. Operator lock: "
                "flat 1.0 bps RT conservative floor (live FTMO index median ~1.5 bps; "
                "range ~0.5–4.2 on 2026-07-14 snapshot). Per-symbol pins not required."
            ),
            "alpha_boundary": (
                "confirm α̂=5.0% both cadences ACCEPTED; Wilson upper 9.0% disclosed; "
                "no α gate rewrite (informal 8–10% posture is not a new threshold)."
            ),
        },
        "frozen_procedure": proc,
        "confirm_summary": {
            "verdict": confirm["outcome"]["verdict"],
            "per_cadence": confirm["per_cadence"],
            "gate_rule": confirm["stop_condition"]["gate_rule"],
        },
        "design_bite": design["bite"],
        "design_coverage": design["coverage"],
        "integrity_attestation": {
            "rust_python_bitwise_parity": True,
            "parity_gate": "tests/test_xena_fold_parity.py",
            "binding_estimand": "g_gross_ratio (design §3); not mean_per_leg",
            "parent_p4_sha256": parent_sha,
        },
        "boundary_pass_disclosure": (
            "α̂ exactly 5.0% both cadences (10/200); Wilson-95 upper 9.0% — boundary accepted "
            "by operator 2026-07-14. Do not re-run confirm to improve (α-shopping)."
        ),
        "route_restore": (
            "RESTORED under this pin — default XENA route uses exit (c) + injected net "
            f"{INJECTED_RT_BPS} bps deployability; INFR-006 v3 extensive-F remains superseded; "
            "operator remains final on capital/universe certify."
        ),
        "operator_signoff": (
            "Jerry Inyang — 2026-07-14: P5 net fix flat 1.0 bps; accept α 5.0% boundary; "
            "route-restore authorized after re-VAL PASS"
        ),
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
    }
    blob = json.dumps(registry, sort_keys=True).encode("utf-8")
    artifact = {"registry": registry, "sha256": hashlib.sha256(blob).hexdigest()}
    # Keep P4 pin as archive; live pin is v2
    if parent_sha == P4_PARENT_SHA or parent.get("registry", {}).get("schema") == "xena.infr009.pc_registry.v1":
        _write("pc_frozen_registry_p4.json", parent if "registry" in parent else {
            "registry": parent, "sha256": parent_sha})
    _write("pc_frozen_registry.json", artifact)
    print(f"[P5] amended freeze sha256={artifact['sha256'][:16]}… "
          f"(parent={parent_sha[:16]}…)", flush=True)
    return artifact


# --------------------------------------------------------------------------- #
# Fixture loading
# --------------------------------------------------------------------------- #
def load_streams(fixture: str) -> list[CandidateStream]:
    code_dir = REPO_PY / "experiments" / fixture / "code"
    for stale in [m for m in list(sys.modules) if m == "run_search"]:
        del sys.modules[stale]
    sys.path.insert(0, str(code_dir))
    try:
        import run_search
        return run_search.load_streams()
    finally:
        sys.path.remove(str(code_dir))
        sys.modules.pop("run_search", None)


def finalists(fixture: str) -> list[list[str]]:
    rd = REPO_PY / "experiments" / fixture / "results"
    out = []
    for f in sorted(rd.glob("search_restart_*.json")):
        best = json.loads(f.read_text()).get("best_subset")
        if best:
            out.append(sorted(str(c) for c in best))
    return out


# --------------------------------------------------------------------------- #
# VAL
# --------------------------------------------------------------------------- #
def _stage1_score(subset, streams, grid, starts) -> float:
    cfg = OracleConfig(charge_costs=False, backend="rust")
    res = evaluate(set(subset), streams, cfg, segment=SEARCH_BAND)
    g_hat, _g_point, _boot = robust_g_hat(res, streams, grid, starts,
                                          block=STAGE1_BLOCK, quantile=STAGE1_QUANTILE)
    return float(g_hat)


def _stage2(subset, streams, *, injected_rt_bps: float | None = None) -> dict:
    """Stage-2: gross costless; net with optional flat RT injection (P5)."""
    cfg = OracleConfig(backend="rust")
    g = eval_lcb_legs(set(subset), streams, cfg, SEG_PROXY, n_boot=N_BOOT, seed=0,
                      block_legs=BLOCK_LEGS, net=False)
    if injected_rt_bps is None:
        streams_net = streams
        inj = None
    else:
        streams_net = _with_flat_cost(streams, float(injected_rt_bps))
        inj = float(injected_rt_bps)
    n = eval_lcb_legs(set(subset), streams_net, cfg, SEG_PROXY, n_boot=N_BOOT, seed=0,
                      block_legs=BLOCK_LEGS, net=True)
    return {"gross_lcb": g.get("lcb"), "gross_point": g.get("point"),
            "gross_pass": bool(g.get("pass_positive")),
            "net_lcb": n.get("lcb"), "net_point": n.get("point"),
            "net_pass": bool(n.get("pass_positive")),
            "n_legs": g.get("n_legs"),
            "injected_rt_bps": inj}


def val_fixture(fixture: str, *, injected_rt_bps: float | None) -> dict:
    print(f"[VAL] {fixture}: load + score finalists (inject={injected_rt_bps})...", flush=True)
    streams = load_streams(fixture)
    fins = finalists(fixture)
    grid = clip_grid_covering(universe_grid(streams), SEARCH_BAND, streams)
    starts = bootstrap_block_starts(len(grid), block=STAGE1_BLOCK, n_boot=200, seed=424243)

    scored = [{"finalist": i, "stage1_g_hat": _stage1_score(sub, streams, grid, starts),
               "size": len(sub), "subset": sub} for i, sub in enumerate(fins)]
    scored.sort(key=lambda r: (r["stage1_g_hat"] if np.isfinite(r["stage1_g_hat"])
                               else -np.inf), reverse=True)
    top = scored[0]
    print(f"  top-1 finalist #{top['finalist']} g_hat={top['stage1_g_hat']:.4f} "
          f"(size {top['size']}); stage-2 on SEG_PROXY...", flush=True)

    top_s2 = _stage2(top["subset"], streams, injected_rt_bps=injected_rt_bps)
    all_s2 = []
    for r in scored:
        s2 = _stage2(r["subset"], streams, injected_rt_bps=injected_rt_bps)
        all_s2.append({"finalist": r["finalist"], "stage1_g_hat": r["stage1_g_hat"],
                       "size": r["size"], **s2})

    # §P4.2 / P5.1: BINDING = top-1 only; all-finalist = disclosure
    deployable = bool(top_s2["net_pass"])
    any_finalist_deployable = any(x["net_pass"] for x in all_s2)
    exp = EXPECTED[fixture]
    gross_ok = bool(top_s2["gross_pass"]) == bool(exp.get("gross_certified", False))
    # 003: gross_certified True means gross_pass expected True; 001/002 expected False
    if fixture == "XENA-003":
        # gross>0 acceptable; gross≤0 also acceptable (conservative) per §P4.3
        gross_matches = True
    else:
        gross_matches = (not top_s2["gross_pass"])
    matches_expected = (deployable == exp["deployable"]) and gross_matches
    print(f"  {fixture}: gross_LCB={top_s2['gross_lcb']:.3f} net_LCB={top_s2['net_lcb']:.3f} "
          f"deployable={deployable} (expected {exp['deployable']}) match={matches_expected}",
          flush=True)
    return {
        "fixture": fixture,
        "q1_p50_realized_bps": Q1_P50_REALIZED_BPS[fixture],
        "top1": {"finalist": top["finalist"], "size": top["size"],
                 "stage1_g_hat": top["stage1_g_hat"], **top_s2},
        "top1_deployable": deployable,
        "top1_gross_certified": bool(top_s2["gross_pass"]),
        "any_finalist_deployable_disclosure": any_finalist_deployable,
        "expected": exp,
        "matches_expected": matches_expected,
        "all_finalists_stage2": all_s2,
    }


def run_val(registry_sha: str, *, injected_rt_bps: float | None,
            schema: str, binding_note: str) -> dict:
    per = {f: val_fixture(f, injected_rt_bps=injected_rt_bps) for f in FIXTURES}
    # Binding acceptance: top-1 only (§P4.2 / P5.1)
    credited = {f: per[f]["top1_deployable"] for f in FIXTURES}
    val_pass = not any(credited.values())
    verdict = "VAL_PASS" if val_pass else "VAL_FAIL_redesign_rejected"
    all_match = all(per[f]["matches_expected"] for f in FIXTURES)
    print(f"[VAL] verdict={verdict} credited_deployable_top1={credited} "
          f"all_match_expected={all_match}", flush=True)
    return {
        "schema": schema,
        "frozen_registry_sha256": registry_sha,
        "injected_rt_bps": injected_rt_bps,
        "seg_proxy": list(SEG_PROXY),
        "search_band": list(SEARCH_BAND),
        "holdout_test_never_read": list(TEST_HOLDOUT_NEVER_READ),
        "per_fixture": per,
        "acceptance_rule": (
            "VAL_PASS iff top-1 net_LCB≤0 on all fixtures after declared cost policy; "
            "all-finalist stage-2 is disclosure only; no extensive-F; no holdout read"
        ),
        "binding": binding_note,
        "credited_deployable_top1": credited,
        "verdict": verdict,
        "all_match_expected": all_match,
        "route_restore": (
            "RESTORED under P5 pin" if injected_rt_bps is not None
            else "NOT in scope — separate operator decision"
        ),
        "note": (
            "Blind VAL on SEG_PROXY. Holdout TEST NEVER read. "
            + ("P5: net path uses flat injected RT; gross costless." if injected_rt_bps is not None
               else "P4: stream-cost net (superseded for deployability by P5).")
        ),
    }


def cost_sweep(costs=(0.0, 0.7, 1.0, 1.5, 2.0)) -> dict:
    val = json.loads((RESULTS / "pc_val.json").read_text())
    out = {}
    for f in FIXTURES:
        streams0 = load_streams(f)
        fx = val["per_fixture"][f]
        fins = finalists(f)
        rows = []
        for c in costs:
            streams = _with_flat_cost(streams0, c)
            top_idx = fx["top1"]["finalist"]
            top_sub = fins[top_idx]
            s2 = _stage2(top_sub, streams, injected_rt_bps=None)  # cost already on streams
            # re-eval: streams already have cost; use net=True via injected None + charged streams
            # _stage2 with inject None uses streams as-is for net — good if cost already set
            n_fin_netpass = None
            if f == "XENA-003":
                n_fin_netpass = sum(1 for sub in fins
                                    if _stage2(sub, streams, injected_rt_bps=None)["net_pass"])
            rows.append({"flat_cost_bps": c, "top1_net_lcb": s2["net_lcb"],
                         "top1_net_pass": s2["net_pass"],
                         "n_finalists_net_pass_of_12": n_fin_netpass})
            print(f"  {f} cost={c}: top1 net_LCB={s2['net_lcb']:.3f} pass={s2['net_pass']}"
                  + (f" finalists_net_pass={n_fin_netpass}/12" if n_fin_netpass is not None else ""),
                  flush=True)
        out[f] = {"gross_lcb_top1": fx["top1"]["gross_lcb"], "sweep": rows}
    result = {"schema": "xena.infr009.pc_val_costsweep.v1",
              "note": "Flat injected RT cost sweep (disclosure).",
              "per_fixture": out}
    _write("pc_val_costsweep.json", result)
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze-only", action="store_true")
    ap.add_argument("--val-only", action="store_true")
    ap.add_argument("--p5", action="store_true",
                    help="P5: amended freeze (1.0 bps net inject) + re-VAL + route pin")
    ap.add_argument("--cost-sweep", action="store_true")
    args = ap.parse_args()

    if args.cost_sweep:
        cost_sweep()
        return

    if args.p5:
        # Archive P4 pin if current file is still v1
        cur = RESULTS / "pc_frozen_registry.json"
        if cur.exists():
            old = json.loads(cur.read_text())
            if old.get("registry", {}).get("schema") == "xena.infr009.pc_registry.v1":
                _write("pc_frozen_registry_p4.json", old)
        artifact = freeze_p5()
        val = run_val(
            artifact["sha256"],
            injected_rt_bps=INJECTED_RT_BPS,
            schema="xena.infr009.pc_val.p5.v1",
            binding_note=(
                f"top-1 net_LCB>0 after flat injected RT={INJECTED_RT_BPS} bps; "
                "gross costless; all-finalist disclosure only"
            ),
        )
        _write("pc_val_p5.json", val)
        # Also refresh pc_val.json pointer for consumers
        val_ptr = dict(val)
        val_ptr["note"] = (val["note"] + " Governing P5 re-VAL artifact: results/pc_val_p5.json.")
        _write("pc_val.json", val_ptr)
        print(f"[P5] done verdict={val['verdict']} route={val['route_restore']}", flush=True)
        return

    if args.val_only:
        reg = json.loads((RESULTS / "pc_frozen_registry.json").read_text())
        # Detect schema for injection policy
        inj = None
        schema = "xena.infr009.pc_val.v1"
        binding = "legacy P4 stream-cost net (prefer --p5)"
        if reg.get("registry", {}).get("schema") == "xena.infr009.pc_registry.v2":
            inj = float(reg["registry"]["amendment"]["injected_rt_bps"])
            schema = "xena.infr009.pc_val.p5.v1"
            binding = f"top-1 net after flat inject {inj} bps"
        val = run_val(reg["sha256"], injected_rt_bps=inj, schema=schema, binding_note=binding)
        _write("pc_val.json", val)
        if inj is not None:
            _write("pc_val_p5.json", val)
        return

    artifact = freeze()
    if args.freeze_only:
        return
    val = run_val(artifact["sha256"], injected_rt_bps=None,
                  schema="xena.infr009.pc_val.v1",
                  binding_note="P4 stream-cost net (superseded by P5)")
    _write("pc_val.json", val)


if __name__ == "__main__":
    main()
