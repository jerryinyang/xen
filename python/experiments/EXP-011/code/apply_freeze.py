"""
EXP-011 (E7) freeze mechanics — apply the additive 15m domain rows to the frozen referee SOURCE and
emit the freeze manifest. GUARDED: refuses unless run_experiment.py wrote a FREEZE_LICENSED (or
RANGE_BOUNDED, which licenses the freeze at the validated prior) license verdict.

This is the ONLY code that edits the frozen module source. It performs four idempotent additive edits
(a new "15m" key in each of DOMAIN_SPECS / MATERIALITY_BPS / ROUND_TRIP_COST_BPS_17 / EPISODE_LENGTHS,
plus ADAPTIVE_DOMAINS) and leaves every 1h/4h/5m entry byte-identical. It then records the post-edit
module hashes + a byte-freeze check that the 1h/4h gate-logic lines are unchanged. Run AFTER the
Stage-3 battery + Stage-4 audit, gated by the operator.

Usage:  python python/experiments/EXP-011/code/apply_freeze.py [--force]
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import sys
from pathlib import Path

logger = logging.getLogger("EXP-011-freeze")

EXP_DIR = Path("python/experiments/EXP-011")
RESULTS_DIR = EXP_DIR / "results"
LICENSE = RESULTS_DIR / "license_verdict.json"

RC = Path("python/src/xen/referee_calibration.py")
RA = Path("python/src/xen/referee_adaptive.py")
IR = Path("python/src/xen/incremental_referee.py")
FROZEN_MODULES = (RA, RC, Path("python/src/xen/referee_pstar.py"), IR)

# The mechanical priors that the battery licensed (design "Derivation rule").
M15, N15, S15, EP15 = 0.75, 90, 25, 17

DOMAIN_SPEC_15M = f'    "15m": DomainSpec("15m", 15, 0.90, min_effective_n={N15}, min_state_count={S15}),\n'
LICENSE_OK = {"FREEZE_LICENSED", "RANGE_BOUNDED"}


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    """Idempotent single replacement: no-op if `new` already present; assert `old` is unique."""
    if new in text:
        logger.info("  [skip] %s already present", label)
        return text
    if text.count(old) != 1:
        raise RuntimeError(f"{label}: anchor not uniquely found ({text.count(old)} matches) — aborting")
    logger.info("  [edit] %s", label)
    return text.replace(old, new)


def edit_domain_specs(text: str) -> str:
    """Insert the 15m DomainSpec row after the 1h row."""
    anchor = '    "1h": DomainSpec("1h", 60, 0.90, min_effective_n=60, min_state_count=20),\n'
    return _replace_once(text, anchor, anchor + DOMAIN_SPEC_15M, "DOMAIN_SPECS[15m]")


def edit_materiality(text: str) -> str:
    """Add the 15m materiality (before 1h) — √-period 0.75."""
    old = 'MATERIALITY_BPS: dict[str, float] = {"5m": 0.5, "1h": 1.5, "4h": 3.0}'
    new = f'MATERIALITY_BPS: dict[str, float] = {{"5m": 0.5, "15m": {M15}, "1h": 1.5, "4h": 3.0}}'
    return _replace_once(text, old, new, "MATERIALITY_BPS[15m]")


def edit_episode_lengths(text: str) -> str:
    """Add the 15m episode length (substrate L) — log-interp 17."""
    old = 'EPISODE_LENGTHS: dict[str, int] = {"5m": 24, "1h": 8, "4h": 4}'
    new = f'EPISODE_LENGTHS: dict[str, int] = {{"5m": 24, "15m": {EP15}, "1h": 8, "4h": 4}}'
    return _replace_once(text, old, new, "EPISODE_LENGTHS[15m]")


def edit_adaptive_domains(text: str) -> str:
    """Add 15m to ADAPTIVE_DOMAINS."""
    old = 'ADAPTIVE_DOMAINS: tuple[str, ...] = ("1h", "4h")'
    new = 'ADAPTIVE_DOMAINS: tuple[str, ...] = ("15m", "1h", "4h")'
    return _replace_once(text, old, new, "ADAPTIVE_DOMAINS")


def edit_cost_map(text: str) -> str:
    """Add a domain-invariant 15m round-trip (== the instrument's 1h value) to every cost-map row."""
    if '"15m":' in text.split("ROUND_TRIP_COST_BPS_17")[1].split("}\n")[0]:
        logger.info("  [skip] ROUND_TRIP_COST_BPS_17[15m] already present")
        return text
    pattern = re.compile(r'\{"1h": ([\d.]+), "4h": \1\}')
    n = len(pattern.findall(text))
    if n < 16:
        raise RuntimeError(f"cost-map: expected >=16 domain-invariant rows, found {n} — aborting")
    logger.info("  [edit] ROUND_TRIP_COST_BPS_17[15m] on %d rows (inherit 1h)", n)
    return pattern.sub(lambda m: f'{{"15m": {m.group(1)}, "1h": {m.group(1)}, "4h": {m.group(1)}}}', text)


def module_hashes() -> dict[str, str]:
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in FROZEN_MODULES}


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    force = "--force" in sys.argv

    if not LICENSE.exists():
        logger.error("No license verdict at %s — run run_experiment.py first. ABORT.", LICENSE)
        return
    lic = json.loads(LICENSE.read_text())
    verdict = lic.get("verdict")
    if verdict not in LICENSE_OK and not force:
        logger.error("LICENSE VERDICT is %s (not in %s) — freeze REFUSED. Use --force only with an "
                     "explicit operator override.", verdict, sorted(LICENSE_OK))
        return
    logger.info("License verdict: %s -> applying additive 15m freeze edits.", verdict)

    hashes_before = module_hashes()
    RC.write_text(edit_materiality(edit_domain_specs(RC.read_text())))
    RA.write_text(edit_cost_map(edit_adaptive_domains(RA.read_text())))
    IR.write_text(edit_episode_lengths(IR.read_text()))
    hashes_after = module_hashes()

    manifest = {
        "status": "FROZEN", "experiment": "EXP-011", "renew_leg": "E7-15m-domain-extension",
        "added_domain": "15m",
        "operating_point": {"q_star": 0.75, "Q_STUD_MIN": 0.6744897501960817, "N_BOOTSTRAP": 500,
                            "alpha": 0.05, "return_basis": "open_to_open_le_t_minus_1"},
        "domain_spec_15m": {"period_minutes": 15, "min_coverage": 0.90, "min_effective_n": N15,
                            "min_state_count": S15},
        "materiality_bps_15m": M15, "episode_length_15m": EP15,
        "cost_rule_15m": "inherit_per_instrument_1h_round_trip (domain-invariant, per-trade)",
        "derivation": {"materiality": "0.19365*sqrt(15)=0.75 (reproduces frozen 1h/4h)",
                       "min_effective_n": "log-period interp(5m 120, 1h 60)~=93.5 -> 90",
                       "min_state_count": "log-period interp(5m 30, 1h 20)~=25.6 -> 25",
                       "episode_length": "log-period interp(5m 24, 1h 8)~=16.9 -> 17"},
        "license_verdict": verdict,
        "frozen_modules_before": hashes_before, "frozen_modules_after": hashes_after,
        "modules_edited": [RC.name, RA.name, IR.name],
    }
    (RESULTS_DIR / "freeze_manifest.json").write_text(json.dumps(manifest, indent=2))

    # Post-edit byte-freeze check: the 1h/4h gate-logic constants must be textually intact.
    checks = {
        "1h_domain_spec_intact": 'min_effective_n=60, min_state_count=20' in RC.read_text(),
        "4h_domain_spec_intact": 'min_effective_n=25, min_state_count=8' in RC.read_text(),
        "materiality_1h_4h_intact": '"1h": 1.5, "4h": 3.0' in RC.read_text(),
        "episode_1h_4h_intact": '"1h": 8, "4h": 4' in IR.read_text(),
        "adaptive_domains_has_15m": '"15m", "1h", "4h"' in RA.read_text(),
        "cost_map_15m_present": '"15m":' in RA.read_text(),
    }
    (RESULTS_DIR / "byte_freeze_check_post.json").write_text(json.dumps(
        {"all_intact": all(checks.values()), "checks": checks,
         "frozen_source_hashes_post_edit": hashes_after}, indent=2))

    logger.info("freeze manifest -> %s", RESULTS_DIR / "freeze_manifest.json")
    logger.info("post-edit 1h/4h intact: %s", all(checks.values()))
    if not all(checks.values()):
        logger.error("BYTE-FREEZE CHECK FAILED — a 1h/4h constant was altered: %s",
                     {k: v for k, v in checks.items() if not v})


if __name__ == "__main__":
    main()
