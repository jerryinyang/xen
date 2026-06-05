"""
Experiment EXP-019: Assembled Suite Composition Anchor.

Runs the concluded strict + ratified-loose + revised incremental suite on the
EXP-009 dogfood negative path and a deterministic synthetic positive fixture.
Missing upstream suite artifacts or an undefined dogfood reference book are
blockers, not measurements.

Manual execution gate: do not run inside the research pipeline.
"""
from __future__ import annotations

import json
import logging
import math
import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from tqdm.auto import tqdm

from xen.incremental_referee import (
    EPISODE_LENGTHS,
    revised_incremental_gate_verdict,
    marginal_net_series,
    per_bar_incremental_cost,
)
from xen.referee_calibration import (
    ALPHA_GRID,
    EDGE_GRID_BPS,
    build_domain_frames,
    cost_bps_for,
    domain_split_index,
    donchian_breakout_positions,
    gate_stack_core,
    gate_stack_row,
    list_timebar_files,
    load_analysis_data,
    ma_crossover_positions,
    materiality_bps_for,
    next_log_returns_from_bars,
    seed_for,
    write_json,
)

PROJECT_ROOT = Path(__file__).resolve().parents[4]
EXP009_CODE_DIR = PROJECT_ROOT / "python" / "experiments" / "EXP-009" / "code"
EXP012_CODE_DIR = PROJECT_ROOT / "python" / "experiments" / "EXP-012" / "code"
sys.path.insert(0, str(EXP009_CODE_DIR))
sys.path.insert(0, str(EXP012_CODE_DIR))

from loose_referee import gate_verdict_rows  # noqa: E402
from strategies import (  # noqa: E402
    bollinger_positions,
    macd_positions,
    roc_positions,
    rsi_positions,
)

LOGGER = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants & paths
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-019"
DATA_DIR = PROJECT_ROOT / "data"
EXPERIMENTS_DIR = PROJECT_ROOT / "python" / "experiments"
EXPERIMENT_DIR = EXPERIMENTS_DIR / EXPERIMENT_ID
INPUTS_DIR = EXPERIMENT_DIR / "inputs"
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"


def _results(exp_id: str) -> Path:
    return EXPERIMENTS_DIR / exp_id / "results"


EXP003_MDE = _results("EXP-003") / "mde_summary.csv"
EXP009_META = _results("EXP-009") / "run_metadata.json"
EXP009_EFFECTS = _results("EXP-009") / "strategy_effects.csv"
EXP009_VERDICTS = _results("EXP-009") / "strategy_verdicts.csv"
EXP012_META = _results("EXP-012") / "run_metadata.json"
EXP012_ADOPTION = _results("EXP-012") / "adoption_decisions.csv"
EXP012_MDE = _results("EXP-012") / "fresh_mde_summary.csv"
EXP018_META = _results("EXP-018") / "run_metadata.json"
EXP018_DOMAIN_MDE = _results("EXP-018") / "domain_mde_summary.csv"

DOGFOOD_REFERENCE_BOOK = INPUTS_DIR / "dogfood_reference_book.csv"
DOGFOOD_REFERENCE_MANIFEST = INPUTS_DIR / "dogfood_reference_book_manifest.json"

DOMAINS: tuple[str, ...] = ("5m", "1h", "4h")
ALPHA0 = 0.05
BOOTSTRAP_RESAMPLES = 1000
FIXTURE_ROWS_BY_DOMAIN: dict[str, int] = {"5m": 48_000, "1h": 12_000, "4h": 6_000}
FIXTURE_INSTRUMENT = "EURUSD"


# --------------------------------------------------------------------------- #
# Output helpers
# --------------------------------------------------------------------------- #
def configure_logging() -> None:
    """Configure concise INFO-level logging for the manual run."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")


def ensure_output_dirs() -> None:
    """Create experiment output directories during orchestration only."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write result rows to CSV, preserving an empty artifact when no rows exist."""
    if rows:
        pl.DataFrame(rows).write_csv(path)
    else:
        path.write_text("", encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Dependency and suite manifests
# --------------------------------------------------------------------------- #
def dependency_manifest() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Check upstream suite artifacts and predeclared reference-book inputs."""
    checks = [
        ("EXP-009 metadata", EXP009_META, "COMPLETE"),
        ("EXP-012 metadata", EXP012_META, "COMPLETE"),
        ("EXP-018 metadata", EXP018_META, "COMPLETE"),
    ]
    manifest: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    for label, path, required_status in checks:
        if not path.exists():
            manifest.append({"dependency": label, "artifact": str(path), "status": "MISSING"})
            blockers.append({"artifact": str(path), "reason": "missing"})
            continue
        meta = _load_json(path)
        status = str(meta.get("overall_status"))
        manifest.append({"dependency": label, "artifact": str(path), "status": status})
        if status != required_status:
            blockers.append(
                {
                    "artifact": str(path),
                    "reason": f"overall_status={status!r}, required {required_status!r}",
                }
            )

    for label, path in (
        ("EXP-003 strict MDE map", EXP003_MDE),
        ("EXP-009 strategy effects", EXP009_EFFECTS),
        ("EXP-009 strategy verdicts", EXP009_VERDICTS),
        ("EXP-012 adoption decisions", EXP012_ADOPTION),
        ("EXP-012 fresh MDE summary", EXP012_MDE),
        ("EXP-018 domain MDE summary", EXP018_DOMAIN_MDE),
    ):
        status = "FOUND" if path.exists() else "MISSING"
        manifest.append({"dependency": label, "artifact": str(path), "status": status})
        if status == "MISSING":
            blockers.append({"artifact": str(path), "reason": "missing"})

    # F02: a COMPLETE EXP-018 whose per-domain MDE is non-finite for any in-scope
    # domain must BLOCK cleanly here, not crash later in load_suite_manifest. The
    # revised unit is only validated where it has a finite headline MDE.
    if EXP018_DOMAIN_MDE.exists():
        mde_by_domain: dict[str, Any] = {
            str(row["domain"]): row["domain_mde_bps"]
            for row in pl.read_csv(EXP018_DOMAIN_MDE).iter_rows(named=True)
        }
        for domain in DOMAINS:
            value = mde_by_domain.get(domain)
            try:
                finite = value is not None and math.isfinite(float(value))
            except (TypeError, ValueError):
                finite = False
            if not finite:
                manifest.append(
                    {
                        "dependency": f"EXP-018 domain MDE [{domain}]",
                        "artifact": str(EXP018_DOMAIN_MDE),
                        "status": "NON_FINITE" if domain in mde_by_domain else "MISSING_DOMAIN",
                    }
                )
                blockers.append(
                    {
                        "artifact": str(EXP018_DOMAIN_MDE),
                        "reason": (
                            f"domain {domain} has no finite revised-unit MDE; the "
                            "revised incremental unit is not validated for this domain"
                        ),
                    }
                )

    if not DOGFOOD_REFERENCE_BOOK.exists():
        blockers.append(
            {
                "artifact": str(DOGFOOD_REFERENCE_BOOK),
                "reason": (
                    "dogfood reference book is undefined; EXP-019 scope forbids "
                    "inventing it during implementation"
                ),
            }
        )
        manifest.append(
            {
                "dependency": "dogfood reference book",
                "artifact": str(DOGFOOD_REFERENCE_BOOK),
                "status": "MISSING",
            }
        )
    else:
        manifest.append(
            {
                "dependency": "dogfood reference book",
                "artifact": str(DOGFOOD_REFERENCE_BOOK),
                "status": "FOUND",
            }
        )
    if DOGFOOD_REFERENCE_MANIFEST.exists():
        manifest.append(
            {
                "dependency": "dogfood reference manifest",
                "artifact": str(DOGFOOD_REFERENCE_MANIFEST),
                "status": "FOUND",
            }
        )
    return manifest, blockers


def write_blocked_metadata(
    manifest_rows: list[dict[str, Any]], blocker_rows: list[dict[str, Any]]
) -> None:
    """Record a BLOCKED run without producing measurements."""
    write_rows(RESULTS_DIR / "dependency_manifest.csv", manifest_rows)
    write_rows(RESULTS_DIR / "blocker_report.csv", blocker_rows)
    write_json(
        RESULTS_DIR / "run_metadata.json",
        {
            "experiment_id": EXPERIMENT_ID,
            "overall_status": "BLOCKED",
            "measurements_produced": False,
            "reason": "Suite dependencies or the dogfood reference book are unavailable.",
            "blockers": blocker_rows,
        },
    )


def load_strict_mde_map() -> dict[str, float]:
    """Load Phase 001 strict gate-stack MDEs at alpha0."""
    frame = pl.read_csv(EXP003_MDE).filter(
        (pl.col("alpha") == ALPHA0) & (pl.col("referee") == "gate_stack")
    )
    out: dict[str, float] = {}
    for row in frame.iter_rows(named=True):
        domain = str(row["domain"])
        if domain in DOMAINS and row["mde_bps"] is not None:
            value = float(row["mde_bps"])
            if math.isfinite(value):
                out[domain] = value
    missing = [domain for domain in DOMAINS if domain not in out]
    if missing:
        raise RuntimeError(f"Missing strict MDE domains: {missing}")
    return out


def load_suite_manifest(strict_mde_map: dict[str, float]) -> list[dict[str, Any]]:
    """Assemble per-domain strict/loose/revised-incremental suite settings."""
    adoption = pl.read_csv(EXP012_ADOPTION)
    exp012_mde = pl.read_csv(EXP012_MDE)
    exp018_mde = pl.read_csv(EXP018_DOMAIN_MDE)
    manifest: list[dict[str, Any]] = []
    for domain in DOMAINS:
        decision = adoption.filter(pl.col("domain") == domain).row(0, named=True)
        loose_row = exp012_mde.filter(
            (pl.col("domain") == domain)
            & (pl.col("referee") == "loose")
            & (pl.col("alpha") == ALPHA0)
        )
        loose_mde = float(loose_row.row(0, named=True)["mde_bps"]) if loose_row.height else math.nan
        inc_row = exp018_mde.filter(pl.col("domain") == domain).row(0, named=True)
        inc_mde = float(inc_row["domain_mde_bps"]) if inc_row["domain_mde_bps"] is not None else math.nan
        adopted = str(decision["verdict"]) == "ADOPT_LOOSE"
        tau_bps = float(decision["tau_bps"]) if adopted else materiality_bps_for(domain)
        effective_loose_mde = loose_mde if adopted and math.isfinite(loose_mde) else strict_mde_map[domain]
        if not math.isfinite(inc_mde):
            raise RuntimeError(f"EXP-018 domain MDE is not finite for {domain}")
        manifest.append(
            {
                "domain": domain,
                "strict_mde_bps": strict_mde_map[domain],
                "loose_decision": str(decision["verdict"]),
                "effective_loose_referee": "loose" if adopted else "strict_fallback",
                "tau_bps": tau_bps,
                "effective_loose_or_fallback_mde_bps": effective_loose_mde,
                "incremental_domain_mde_bps": inc_mde,
                "incremental_domain_status": str(inc_row["status"]),
            }
        )
    return manifest


def grid_step_after(value: float) -> float:
    """Return the next edge-grid step size after ``value``."""
    grid = list(EDGE_GRID_BPS)
    for idx, edge in enumerate(grid):
        if value <= edge:
            if idx + 1 < len(grid):
                return float(grid[idx + 1] - grid[idx])
            return float(grid[idx] - grid[idx - 1])
    return float(grid[-1] - grid[-2])


def expected_output_matrix(suite_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Predeclare expected outputs for both integration paths."""
    rows: list[dict[str, Any]] = []
    for row in suite_rows:
        domain = row["domain"]
        rows.append(
            {
                "path": "dogfood_negative",
                "domain": domain,
                "strict_expected": "REJECT",
                "loose_or_fallback_expected": "REJECT",
                "incremental_expected": "NO_POSITIVE_INCREMENTAL",
                "suite_expected": "REJECT_PATH_EXERCISED",
            }
        )
        rows.append(
            {
                "path": "synthetic_positive",
                "domain": domain,
                "strict_expected": "PASS",
                "loose_or_fallback_expected": "PASS",
                "incremental_expected": "POSITIVE_INCREMENTAL",
                "suite_expected": "PASS_PATH_EXERCISED",
            }
        )
    return rows


# --------------------------------------------------------------------------- #
# Referee helpers
# --------------------------------------------------------------------------- #
def strict_and_loose_rows(
    returns: np.ndarray,
    positions: np.ndarray,
    *,
    instrument: str,
    domain: str,
    tau_bps: float,
    seed: int,
    split_index: int | None,
    base_label: dict[str, Any],
) -> list[dict[str, Any]]:
    """Evaluate strict and effective loose/fallback standalone referee rows."""
    core = gate_stack_core(
        returns,
        positions,
        instrument=instrument,
        domain=domain,
        n_bootstrap=BOOTSTRAP_RESAMPLES,
        seed=seed,
        split_index=split_index,
    )
    strict = gate_stack_row(core, alpha=ALPHA0)
    loose_rows = gate_verdict_rows(
        core,
        alpha_values=(ALPHA0,),
        tau_bps=tau_bps,
        base_label={},
    )
    loose = next(row for row in loose_rows if row["referee"] == "loose")
    return [
        {**base_label, "suite_component": "strict", **strict},
        {
            **base_label,
            "suite_component": "loose_or_strict_fallback",
            "referee": "loose_or_strict_fallback",
            "alpha": loose["alpha"],
            "verdict": "PASS" if loose["passed"] else "REJECT",
            "passed": bool(loose["passed"]),
            "effect_bps": loose["effect_bps"],
            "ci_lower_bps": loose["ci_lower_bps"],
            "ci_upper_bps": math.nan,
            "effective_n": loose["effective_n"],
            "block_length": loose["block_length"],
            "tau_bps": tau_bps,
        },
    ]


def strategy_positions(domain_frame: pl.DataFrame) -> dict[str, np.ndarray]:
    """Compute the EXP-009 dogfood strategy positions aligned to next returns."""
    ordered = domain_frame.sort("CloseTime")
    high = np.asarray(ordered.get_column("High"), dtype=float)
    low = np.asarray(ordered.get_column("Low"), dtype=float)
    close = np.asarray(ordered.get_column("Close"), dtype=float)
    return {
        "donchian_20": donchian_breakout_positions(high, low, close, lookback=20),
        "ma_20_50": ma_crossover_positions(close, fast=20, slow=50),
        "rsi_14": rsi_positions(close),
        "bollinger_20_2": bollinger_positions(close),
        "macd_12_26_9": macd_positions(close),
        "roc_20": roc_positions(close),
    }


def reference_family_from_manifest() -> str | None:
    """Return the EXP-009 family declared as the reference book R, if any (F06).

    design D-dogfood-book specifies "candidates C are the **remaining** EXP-009
    families" (excluding the one designated as the reference book R). The
    operator-provided reference-book manifest may name that family in a
    ``reference_family`` field; when present, it is dropped from the candidate slate so
    R is never also run as a candidate against itself. Absent the field, all families
    are evaluated (a redundant self-comparison is harmless on the negative path).
    """
    if not DOGFOOD_REFERENCE_MANIFEST.exists():
        return None
    family = _load_json(DOGFOOD_REFERENCE_MANIFEST).get("reference_family")
    return str(family) if family is not None else None


def load_reference_book() -> pl.DataFrame:
    """Load the predeclared dogfood reference book positions."""
    frame = pl.read_csv(DOGFOOD_REFERENCE_BOOK)
    required = {"instrument", "domain", "CloseTime", "reference_position"}
    missing = required.difference(frame.columns)
    if missing:
        raise RuntimeError(f"Reference book missing columns: {sorted(missing)}")
    return frame.with_columns(
        pl.col("instrument").cast(pl.Utf8),
        pl.col("domain").cast(pl.Utf8),
        pl.col("CloseTime").cast(pl.Utf8),
        pl.col("reference_position").cast(pl.Float64),
    )


def align_reference_positions(
    reference_book: pl.DataFrame,
    *,
    instrument: str,
    domain: str,
    aligned: pl.DataFrame,
) -> np.ndarray:
    """Align predeclared reference positions to domain return rows by CloseTime."""
    keyed = aligned.select(pl.col("CloseTime").cast(pl.Utf8).alias("CloseTime"))
    ref = reference_book.filter(
        (pl.col("instrument") == instrument) & (pl.col("domain") == domain)
    ).select(["CloseTime", "reference_position"])
    joined = keyed.join(ref, on="CloseTime", how="left")
    if joined.get_column("reference_position").null_count() > 0:
        missing = joined.get_column("reference_position").null_count()
        raise RuntimeError(
            f"Reference book missing {missing} rows for {instrument}/{domain}; "
            "CloseTime alignment must be complete"
        )
    return np.asarray(joined.get_column("reference_position"), dtype=float)


# --------------------------------------------------------------------------- #
# Dogfood negative path
# --------------------------------------------------------------------------- #
def run_dogfood_path(
    suite_rows: list[dict[str, Any]],
    reference_book: pl.DataFrame,
    *,
    reference_family: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Run assembled suite on the EXP-009 dogfood negative path.

    ``reference_family`` (F06), when set, is the EXP-009 family backing the reference
    book R and is excluded from the candidate slate so R is not scored against itself.
    """
    suite_by_domain = {row["domain"]: row for row in suite_rows}
    standalone_rows: list[dict[str, Any]] = []
    incremental_rows: list[dict[str, Any]] = []
    files = list_timebar_files(DATA_DIR)
    if not files:
        raise FileNotFoundError(f"No time-bar files found under {DATA_DIR / 'timebars'}")

    for path in tqdm(files, desc="EXP-019 dogfood"):
        data = load_analysis_data(path)
        for domain, frame in build_domain_frames(data.frame).items():
            suite = suite_by_domain[domain]
            returns, aligned = next_log_returns_from_bars(frame)
            split_index = domain_split_index(aligned, data.train_end_ts)
            r_positions = align_reference_positions(
                reference_book, instrument=data.instrument, domain=domain, aligned=aligned
            )
            for strategy, c_positions in strategy_positions(frame).items():
                if reference_family is not None and strategy == reference_family:
                    continue  # F06: the reference family backs R, not a candidate C.
                base = {
                    "path": "dogfood_negative",
                    "instrument": data.instrument,
                    "domain": domain,
                    "strategy": strategy,
                }
                standalone_rows.extend(
                    strict_and_loose_rows(
                        returns,
                        c_positions,
                        instrument=data.instrument,
                        domain=domain,
                        tau_bps=float(suite["tau_bps"]),
                        seed=seed_for(EXPERIMENT_ID, "dogfood", data.instrument, domain, strategy),
                        split_index=split_index,
                        base_label=base,
                    )
                )
                inc = revised_incremental_gate_verdict(
                    returns,
                    r_positions,
                    c_positions,
                    instrument=data.instrument,
                    domain=domain,
                    alpha=ALPHA0,
                    n_bootstrap=BOOTSTRAP_RESAMPLES,
                    seed=seed_for(EXPERIMENT_ID, "dogfood_incremental", data.instrument, domain, strategy),
                    split_index=split_index,
                    episode_length=EPISODE_LENGTHS[domain],
                )
                marginal = marginal_net_series(
                    returns,
                    r_positions,
                    c_positions,
                    cost_bps=cost_bps_for(data.instrument, domain),
                    episode_length=EPISODE_LENGTHS[domain],
                )
                incremental_rows.append(
                    {
                        **base,
                        "suite_component": "incremental",
                        "verdict": inc["verdict"],
                        "passed": inc["passed"],
                        "incremental_edge_bps": inc["incremental_edge_bps"],
                        "incremental_ci_lower_bps": inc["incremental_ci_lower_bps"],
                        "incremental_ci_upper_bps": inc["incremental_ci_upper_bps"],
                        "effective_n": inc["effective_n"],
                        "block_length": inc["block_length"],
                        "denominator_count": marginal["denominator_count"],
                    }
                )
    return standalone_rows, incremental_rows


# --------------------------------------------------------------------------- #
# Synthetic positive path
# --------------------------------------------------------------------------- #
def build_positive_fixture(
    *,
    domain: str,
    standalone_target_bps: float,
    incremental_target_bps: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    """Build deterministic non-redundant R/C fixture arrays for one domain."""
    n = FIXTURE_ROWS_BY_DOMAIN[domain]
    episode_length = EPISODE_LENGTHS[domain]
    rng = np.random.default_rng(seed)
    n_episodes = (n + episode_length - 1) // episode_length
    states = rng.choice(np.array([-1.0, 1.0]), size=n_episodes)
    masks = np.array(["R_only", "C_change", "C_change", "inactive"])[
        np.arange(n_episodes) % 4
    ]
    rng.shuffle(masks)
    state = np.repeat(states, episode_length)[:n]
    mask_rows = np.repeat(masks, episode_length)[:n]

    r_positions = np.where(mask_rows == "R_only", state, 0.0)
    c_positions = np.where(mask_rows == "C_change", state, 0.0)
    returns = rng.normal(0.0, 1.0 / 10_000.0, n)

    cost = cost_bps_for(FIXTURE_INSTRUMENT, domain)
    inc_cost = per_bar_incremental_cost(cost, episode_length)
    # One return drift must support both standalone and incremental pass-path
    # expectations. The manifest records the scoped thresholds; the actual drift is
    # the smallest value that clears both cost conventions.
    required_return_bps = max(standalone_target_bps + cost, incremental_target_bps + inc_cost)
    active = c_positions != 0.0
    returns[active] += c_positions[active] * (required_return_bps / 10_000.0)

    overlap = float(np.count_nonzero((r_positions != 0.0) & (c_positions != 0.0)) / max(np.count_nonzero(c_positions != 0.0), 1))
    union = (r_positions != 0.0) | (c_positions != 0.0)
    rho = 0.0
    if int(np.count_nonzero(union)) > 1 and np.std(r_positions[union]) > 0 and np.std(c_positions[union]) > 0:
        rho = float(np.corrcoef(r_positions[union], c_positions[union])[0, 1])
    manifest = {
        "domain": domain,
        "instrument": FIXTURE_INSTRUMENT,
        "rows": n,
        "seed": seed,
        "standalone_target_bps": standalone_target_bps,
        "incremental_target_bps": incremental_target_bps,
        "required_return_drift_bps": required_return_bps,
        "active_overlap_fraction": overlap,
        "signed_r_c_rho": rho,
        "nonredundancy_ok": bool(overlap <= 0.10 and abs(rho) <= 0.05),
    }
    return returns, r_positions, c_positions, manifest


def run_positive_path(suite_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Run the synthetic positive pass-path fixture."""
    fixture_manifest: list[dict[str, Any]] = []
    standalone_rows: list[dict[str, Any]] = []
    incremental_rows: list[dict[str, Any]] = []
    for suite in suite_rows:
        domain = str(suite["domain"])
        standalone_step = grid_step_after(
            max(
                float(suite["strict_mde_bps"]),
                float(suite["effective_loose_or_fallback_mde_bps"]),
            )
        )
        incremental_step = grid_step_after(
            max(float(suite["incremental_domain_mde_bps"]), materiality_bps_for(domain))
        )
        standalone_target = (
            max(
                float(suite["strict_mde_bps"]),
                float(suite["effective_loose_or_fallback_mde_bps"]),
            )
            + standalone_step
        )
        incremental_target = (
            max(float(suite["incremental_domain_mde_bps"]), materiality_bps_for(domain))
            + incremental_step
        )
        returns, r_positions, c_positions, manifest = build_positive_fixture(
            domain=domain,
            standalone_target_bps=standalone_target,
            incremental_target_bps=incremental_target,
            seed=seed_for(EXPERIMENT_ID, "positive_fixture", domain),
        )
        fixture_manifest.append(manifest)
        if not manifest["nonredundancy_ok"]:
            continue
        base = {
            "path": "synthetic_positive",
            "instrument": FIXTURE_INSTRUMENT,
            "domain": domain,
            "strategy": "positive_fixture",
        }
        standalone_rows.extend(
            strict_and_loose_rows(
                returns,
                c_positions,
                instrument=FIXTURE_INSTRUMENT,
                domain=domain,
                tau_bps=float(suite["tau_bps"]),
                seed=seed_for(EXPERIMENT_ID, "positive_standalone", domain),
                split_index=None,
                base_label=base,
            )
        )
        inc = revised_incremental_gate_verdict(
            returns,
            r_positions,
            c_positions,
            instrument=FIXTURE_INSTRUMENT,
            domain=domain,
            alpha=ALPHA0,
            n_bootstrap=BOOTSTRAP_RESAMPLES,
            seed=seed_for(EXPERIMENT_ID, "positive_incremental", domain),
            split_index=None,
            episode_length=EPISODE_LENGTHS[domain],
        )
        marginal = marginal_net_series(
            returns,
            r_positions,
            c_positions,
            cost_bps=cost_bps_for(FIXTURE_INSTRUMENT, domain),
            episode_length=EPISODE_LENGTHS[domain],
        )
        incremental_rows.append(
            {
                **base,
                "suite_component": "incremental",
                "verdict": inc["verdict"],
                "passed": inc["passed"],
                "incremental_edge_bps": inc["incremental_edge_bps"],
                "incremental_ci_lower_bps": inc["incremental_ci_lower_bps"],
                "incremental_ci_upper_bps": inc["incremental_ci_upper_bps"],
                "effective_n": inc["effective_n"],
                "block_length": inc["block_length"],
                "denominator_count": marginal["denominator_count"],
            }
        )
    return fixture_manifest, standalone_rows, incremental_rows


# --------------------------------------------------------------------------- #
# Composition summary and plots
# --------------------------------------------------------------------------- #
def composition_summary(
    standalone_rows: list[dict[str, Any]],
    incremental_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Summarize whether each path exercised the expected suite wiring."""
    rows: list[dict[str, Any]] = []
    standalone = pl.DataFrame(standalone_rows) if standalone_rows else pl.DataFrame()
    incremental = pl.DataFrame(incremental_rows) if incremental_rows else pl.DataFrame()
    for path in ("dogfood_negative", "synthetic_positive"):
        for domain in DOMAINS:
            s_sub = standalone.filter((pl.col("path") == path) & (pl.col("domain") == domain)) if not standalone.is_empty() else pl.DataFrame()
            i_sub = incremental.filter((pl.col("path") == path) & (pl.col("domain") == domain)) if not incremental.is_empty() else pl.DataFrame()
            strict_passes = (
                int(s_sub.filter((pl.col("suite_component") == "strict") & pl.col("passed")).height)
                if not s_sub.is_empty()
                else 0
            )
            loose_passes = (
                int(
                    s_sub.filter(
                        (pl.col("suite_component") == "loose_or_strict_fallback") & pl.col("passed")
                    ).height
                )
                if not s_sub.is_empty()
                else 0
            )
            inc_passes = int(i_sub.filter(pl.col("passed")).height) if not i_sub.is_empty() else 0
            n_standalone = s_sub.height
            n_incremental = i_sub.height
            if path == "dogfood_negative":
                ok = strict_passes == 0 and loose_passes == 0 and inc_passes == 0 and n_incremental > 0
                status = "REJECT_PATH_EXERCISED" if ok else "UNEXPECTED_DOGFOOD_OUTPUT"
            else:
                ok = strict_passes > 0 and loose_passes > 0 and inc_passes > 0
                status = "PASS_PATH_EXERCISED" if ok else "PASS_PATH_NOT_EXERCISED"
            rows.append(
                {
                    "path": path,
                    "domain": domain,
                    "strict_passes": strict_passes,
                    "loose_or_fallback_passes": loose_passes,
                    "incremental_passes": inc_passes,
                    "standalone_rows": n_standalone,
                    "incremental_rows": n_incremental,
                    "status": status,
                }
            )
    return rows


def plot_suite_verdict_matrix(summary_rows: list[dict[str, Any]]) -> None:
    """Plot suite path status by domain."""
    if not summary_rows:
        return
    pdf = pl.DataFrame(summary_rows).to_pandas()
    code = {
        "REJECT_PATH_EXERCISED": 1.0,
        "PASS_PATH_EXERCISED": 1.0,
        "UNEXPECTED_DOGFOOD_OUTPUT": 0.0,
        "PASS_PATH_NOT_EXERCISED": 0.0,
    }
    grid = np.zeros((2, len(DOMAINS)))
    paths = ["dogfood_negative", "synthetic_positive"]
    for i, path in enumerate(paths):
        for j, domain in enumerate(DOMAINS):
            status = pdf[(pdf["path"] == path) & (pdf["domain"] == domain)]["status"].iloc[0]
            grid[i, j] = code.get(status, 0.0)
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.imshow(grid, cmap="Greens", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(DOMAINS)), DOMAINS)
    ax.set_yticks(range(len(paths)), paths)
    for i in range(len(paths)):
        for j in range(len(DOMAINS)):
            ax.text(j, i, "OK" if grid[i, j] else "CHECK", ha="center", va="center")
    ax.set_title("Suite path wiring status")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "suite_verdict_matrix.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_incremental_edges(incremental_rows: list[dict[str, Any]]) -> None:
    """Plot incremental edge intervals for both paths."""
    if not incremental_rows:
        return
    pdf = pl.DataFrame(incremental_rows).to_pandas()
    pdf["label"] = pdf["path"] + " " + pdf["domain"] + " " + pdf["strategy"]
    fig, ax = plt.subplots(figsize=(10, 6))
    y = np.arange(len(pdf))
    ax.errorbar(
        pdf["incremental_edge_bps"],
        y,
        xerr=[
            pdf["incremental_edge_bps"] - pdf["incremental_ci_lower_bps"],
            pdf["incremental_ci_upper_bps"] - pdf["incremental_edge_bps"],
        ],
        fmt="o",
        markersize=3,
    )
    ax.axvline(0.0, color="grey", linewidth=1)
    ax.set_yticks(y, pdf["label"], fontsize=5)
    ax.set_xlabel("Incremental edge (bps)")
    ax.set_title("Incremental edge intervals by path")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "incremental_edge_intervals.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_denominators(incremental_rows: list[dict[str, Any]]) -> None:
    """Plot incremental denominator counts by path/domain."""
    if not incremental_rows:
        return
    pdf = pl.DataFrame(incremental_rows).to_pandas()
    pdf["label"] = pdf["path"] + " " + pdf["domain"] + " " + pdf["strategy"]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(range(len(pdf)), pdf["denominator_count"], color="slateblue")
    ax.set_xticks(range(len(pdf)), pdf["label"], rotation=90, fontsize=5)
    ax.set_ylabel("Incremental denominator rows")
    ax.set_title("Bars where C changes the book beyond R")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "incremental_denominators.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_referee_flow(suite_rows: list[dict[str, Any]]) -> None:
    """Plot strict vs effective loose/fallback MDE flow by domain."""
    pdf = pl.DataFrame(suite_rows).to_pandas()
    x = np.arange(len(pdf))
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(x - 0.2, pdf["strict_mde_bps"], width=0.4, label="strict")
    ax.bar(x + 0.2, pdf["effective_loose_or_fallback_mde_bps"], width=0.4, label="loose/fallback")
    ax.set_xticks(x, pdf["domain"])
    ax.set_ylabel("Standalone MDE (bps)")
    ax.set_title("Ratified-loose decisions flowing into suite")
    ax.legend()
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "strict_vs_loose_flow.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_integration_status(summary_rows: list[dict[str, Any]]) -> None:
    """Plot pass counts by path/domain/component."""
    if not summary_rows:
        return
    pdf = pl.DataFrame(summary_rows).to_pandas()
    labels = pdf["path"] + " " + pdf["domain"]
    x = np.arange(len(pdf))
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(x - 0.25, pdf["strict_passes"], width=0.25, label="strict")
    ax.bar(x, pdf["loose_or_fallback_passes"], width=0.25, label="loose/fallback")
    ax.bar(x + 0.25, pdf["incremental_passes"], width=0.25, label="incremental")
    ax.set_xticks(x, labels, rotation=45, ha="right")
    ax.set_ylabel("PASS count")
    ax.set_title("Suite component PASS counts")
    ax.legend()
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "integration_status_counts.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    """Run the EXP-019 suite composition anchor and write outputs."""
    configure_logging()
    ensure_output_dirs()
    manifest_rows, blocker_rows = dependency_manifest()
    if blocker_rows:
        write_blocked_metadata(manifest_rows, blocker_rows)
        LOGGER.warning("EXP-019 BLOCKED: %s", blocker_rows)
        return

    strict_mde_map = load_strict_mde_map()
    suite_rows = load_suite_manifest(strict_mde_map)
    expected_rows = expected_output_matrix(suite_rows)
    reference_book = load_reference_book()
    reference_family = reference_family_from_manifest()

    positive_manifest, positive_standalone, positive_incremental = run_positive_path(suite_rows)
    dogfood_standalone, dogfood_incremental = run_dogfood_path(
        suite_rows, reference_book, reference_family=reference_family
    )

    standalone_rows = dogfood_standalone + positive_standalone
    incremental_rows = dogfood_incremental + positive_incremental
    summary_rows = composition_summary(standalone_rows, incremental_rows)

    status_values = {row["status"] for row in summary_rows}
    complete = status_values.issubset({"REJECT_PATH_EXERCISED", "PASS_PATH_EXERCISED"})
    overall_status = "COMPLETE" if complete else "INCONCLUSIVE"

    write_rows(RESULTS_DIR / "dependency_manifest.csv", manifest_rows)
    write_rows(RESULTS_DIR / "suite_manifest.csv", suite_rows)
    write_rows(RESULTS_DIR / "expected_output_matrix.csv", expected_rows)
    write_rows(RESULTS_DIR / "positive_fixture_manifest.csv", positive_manifest)
    write_rows(RESULTS_DIR / "standalone_suite_verdicts.csv", standalone_rows)
    write_rows(RESULTS_DIR / "incremental_suite_verdicts.csv", incremental_rows)
    write_rows(RESULTS_DIR / "suite_composition_summary.csv", summary_rows)
    write_json(
        RESULTS_DIR / "run_metadata.json",
        {
            "experiment_id": EXPERIMENT_ID,
            "overall_status": overall_status,
            "measurements_produced": True,
            "alpha0": ALPHA0,
            "alpha_grid": list(ALPHA_GRID),
            "suite_components": [
                "strict_gate_stack",
                "exp012_ratified_loose_referee",
                "exp018_revised_incremental_referee",
            ],
            "revised_incremental_gate_formula": "L1 and L3 and L4_prime and strict_L5; L2 absent",
            "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
            "dogfood_reference_family_excluded_from_candidates": reference_family,
            "dogfood_reference_book": str(DOGFOOD_REFERENCE_BOOK),
            "dogfood_reference_manifest": (
                _load_json(DOGFOOD_REFERENCE_MANIFEST) if DOGFOOD_REFERENCE_MANIFEST.exists() else None
            ),
            "suite_status": {f"{row['path']}|{row['domain']}": row["status"] for row in summary_rows},
        },
    )

    plot_suite_verdict_matrix(summary_rows)
    plot_incremental_edges(incremental_rows)
    plot_denominators(incremental_rows)
    plot_referee_flow(suite_rows)
    plot_integration_status(summary_rows)

    LOGGER.info("EXP-019 complete: %s", overall_status)
    LOGGER.info("Suite status: %s", {f"{row['path']}|{row['domain']}": row["status"] for row in summary_rows})
    LOGGER.info("Results: %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
