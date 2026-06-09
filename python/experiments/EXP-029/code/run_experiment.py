"""Experiment EXP-029: cTrader Per-Bar Streaming Parity for Faithful AVWAP Strategy.

Implements the approved scope.md / analysis-plan.md (Phase 006, §9 amendment).
EXP-029 closes the EXP-028 omission: it evaluates the **corrected** C# AVWAP
strategy as actually executed bar-by-bar inside cTrader's engine (pyramid bounces
opened as independent positions), and confirms parity with the Python-only
EXP-028 re-analysis under the *same* estimand and the *same* frozen EXP-027
event-level inference.

Two prior divergences are guarded explicitly (see analysis-plan.md "Divergences
To Avoid"):

  * D1 (execution-path): the estimand is built from the **cTrader-emitted runs**
    only (the corrected, pyramid-inclusive, event-detail-bearing emission). The
    EXP-023 ``avwap_baseline_*`` runs (pyramid-suppressed, no event-detail table)
    are explicitly NOT reusable; a corrected run is recognised by the presence of
    ``avwap_events.parquet`` in the run directory.
  * D2 (estimand/framing): the binding PRIMARY estimand is the **same** per-event
    *symmetric own-exit matched-control excess* EXP-028 reports
    (``event_lifetime_bps - mean(control_lifetime_bps)``), reconstructed by the
    imported EXP-022 own-exit lifetime machinery on the cTrader ``RealClose`` feed.
    Comparing raw per-event return against EXP-028's excess is a category mismatch
    and is never done.

Other guards: D3 the frozen EXP-027 inference tail is imported unchanged and
sha256-hash-guarded; D4 regime / anchor / frozen targets / pyramid tag come from
the cTrader emission — the AVWAP signal is never re-derived in Python (no signal
oracle); D5 the final-30% global holdout is never loaded and the per-instrument
``AnalysisEndUtc`` fence is re-asserted; D6 cross-feed alignment is by
``SourceCloseTime`` (timestamp), never bar-index transfer; D7 effects are bps /
absolute counts / CIs only (zero-baseline safe); D8 the parity criteria are
predeclared in the plan.

Adversarial-review hardening (2026-06-09) — the binding disposition is no longer a
coarse "verdict + CI-overlap" read that can only confirm:
  * F01 exit-parity — the corrected C# concurrent-completion code is graded per event
    (exit bar / reason / signed bps) against the Python scan on the SAME feed
    (``build_exit_parity``); a completion-code bug now forces INCONSISTENT.
  * F02 magnitude equivalence — CONSISTENT requires the EXP-029 vs EXP-028 effect
    difference inside a predeclared margin, and a divergence beyond the larger margin
    is INCONSISTENT (a magnitude divergence can now downgrade EXP-028, not just fail
    to upgrade it).
  * F03 signal-layer 5m reconciliation — the C# 5m event set is checked against the
    EXP-020 substrate on the feed-exact domain (``reconcile_signal_layer``), so a
    signal-logic divergence is not silently absorbed as "benign feed coverage".
  * F04 the per-domain pyramid split is now inside the ±10% count gate.
  * F05 the frozen-inference hash is hard-asserted equal to the one EXP-028 used.

Emitted-schema contract consumed here (produced by the corrected C# model; see
``StrategyHost/AvwapBounceModel.cs`` + ``StrategyRunParquetWriter.cs``):

  * ``positions.parquet`` (per domain bar, emission/`SourceCloseTime` order):
    the generic strategy-host columns PLUS ``RegimeId`` (int32) and
    ``RegimeDirection`` (int32) — already-computed per-bar model state.
  * ``avwap_events.parquet`` (one row per bounce, incl. pyramids): the serialized
    ``AvwapEventDetail`` table — ``SourceCloseTime`` (trigger time), ``Domain``,
    ``RegimeId``, ``Direction``, ``IsPyramidBounce``, ``BounceIndexInRegime``,
    ``AnchorIdx``, ``AnchorTime``, ``AnchorPrice``, ``TriggerIdx``,
    ``TriggerClose``, ``AvwapAtTrigger``, ``FavorableTargetAtTrigger``,
    ``AdverseTargetAtTrigger``, ``AnchorAgeBars``, and — for the F01 exit-parity
    grading — the C#-executed completion ``ExitIdx`` / ``ExitTime`` / ``ExitClose`` /
    ``ExitReason`` / ``ExitBars`` / ``ExitLifetimeBps`` (``ExitReason="open"`` /
    ``ExitIdx=-1`` for a position never completed within the fence).
  * ``trade_blotter.parquet`` (diagnostic): generic, plus the per-position
    ``enter_*`` / ``exit_*`` actions.

Run:
    cd <project-root>/python && uv run python experiments/EXP-029/code/run_experiment.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402  (backend must be set first)
import numpy as np  # noqa: E402
import polars as pl  # noqa: E402
from tqdm.auto import tqdm  # noqa: E402

# --------------------------------------------------------------------------- #
# Path setup
# --------------------------------------------------------------------------- #
PROJECT_ROOT = Path(__file__).resolve().parents[4]
EXP029_CODE = Path(__file__).resolve().parent
if str(EXP029_CODE) not in sys.path:
    sys.path.insert(0, str(EXP029_CODE))

from xen.referee_calibration import seed_for  # noqa: E402

# Frozen EXP-027 inference tail (local sha256-verified copy of event_method.py).
import event_method as EM  # noqa: E402
from event_method import (  # noqa: E402
    bootstrap_effect_distribution,
    build_strata,
    decide_label,
    domain_effect,
    holm_adjust,
    permutation_p,
    sortino_ratio,
    verify_control_matching,
)

LOGGER = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-029"
DATA_DIR = PROJECT_ROOT / "data"
RUNS_DIR = DATA_DIR / "strategy_runs"
EXP_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"

EXP020_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-020" / "results"
EXP022_CODE = PROJECT_ROOT / "python" / "experiments" / "EXP-022" / "code" / "run_experiment.py"
EXP027_METHOD = PROJECT_ROOT / "python" / "experiments" / "EXP-027" / "code" / "event_method.py"
EXP027_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-027" / "results"
EXP028_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-028" / "results"

DOMAINS: tuple[str, ...] = ("5m", "1h", "4h")
INSTRUMENTS: tuple[str, ...] = ("BTCUSD", "EURUSD", "USTEC", "XAUUSD")

# cTrader strategy-run identity (corrected model emits the same strategy label).
STRATEGY_NAME = "avwap_baseline"

# Per-instrument analysis-end fence (identical to EXP-023/028); the C# host emits
# no row at or after it; re-asserted here.
ANALYSIS_END: dict[str, str] = {
    "BTCUSD": "2025-06-17T22:38:00Z",
    "EURUSD": "2025-05-09T16:55:00Z",
    "USTEC": "2025-05-12T04:54:00Z",
    "XAUUSD": "2025-05-12T03:35:00Z",
}

# Reportability (EXP-021/022/027/028 thresholds).
MIN_REPORTABLE_EVENTS = 30
MIN_DIRECTION_EVENTS = 8
DOMAIN_MIN_INSTRUMENTS = 3

# Inference (calibration convention; matches EXP-027/028 exactly).
N_BOOT = 1000
N_PERM = 1000
CHUNK = 200
ALPHA = 0.05
CI_PERCENTILES = (2.5, 97.5)

# Fixed-horizon secondary-stability family (EXP-021/027/028).
HORIZONS: tuple[int, ...] = EM.HORIZONS
SEC_LOW_HORIZON = 1
SEC_HIGH_HORIZON = 6

# Reconciliation tolerance for event/control lifetime_bps vs frame recompute.
RECON_TOL_BPS = 1e-3
# Trigger-close alignment tolerance (cTrader event row vs positions RealClose).
ALIGN_TOL_REL = 1e-9

# EXP-022 exit-rule outcomes that count as a realized exit.
COMPLETED_OUTCOMES = ("favorable", "adverse", "trend_change")

# Parity tolerances (analysis-plan.md Step 6 / scope Parity Criteria).
COUNT_TOL_CONSISTENT = 0.10
COUNT_TOL_INCONCLUSIVE = 0.20
DISPOSITION_MIN_DOMAINS = 2  # CONSISTENT iff all binding criteria hold on >= 2/3 domains

# Frozen-method identity (F05): the inference tail must be byte-identical to the one
# EXP-028 used, not merely to the current EXP-027 source. Hard-asserted in main().
EXP028_FROZEN_HASH = "ea261b9ee0a8aca3"

# Effect-difference equivalence margins (F02): "verdict agreement + CI overlap" is a
# coarse, lax agreement test that cannot bound the actual effect-size disagreement, so
# parity also requires the EXP-029 vs EXP-028 effect difference to fall inside a
# predeclared margin. A divergence beyond the larger margin is INCONSISTENT even when
# the 3-way verdict label still matches. Margins are absolute-or-relative (max of the
# two) so the tight 5m CI and the wide 4h CI are both handled sensibly. Predeclared
# here before any cTrader result exists (D8: no goalpost-moving).
EFFECT_EQUIV_ABS_BPS = 2.0      # |Δeffect| <= max(2 bps, 25% of |EXP-028 effect|) -> equivalent
EFFECT_EQUIV_REL = 0.25
EFFECT_DIVERGENT_REL = 0.50     # |Δeffect| >  max(2 bps, 50% of |EXP-028 effect|) -> INCONSISTENT

# Exit-parity gate (F01/F06): the corrected C# concurrent-completion code is graded
# per event against the Python scan_lifetime on the SAME cTrader feed (same frozen
# targets, same trend-change boundary), so a multi-position completion bug surfaces
# here even though the binding estimand keeps the symmetric Python scan for EXP-028
# comparability. A domain whose C# exits do not reproduce the Python scan is NOT
# parity-confirmable. Same-feed, so the only slack is float rounding.
EXIT_PARITY_MIN = 0.99          # >= 99% of completed events must match bar + reason + bps
EXIT_PARITY_BPS_TOL = 1e-3      # |C# exit bps - Python lifetime bps| tolerance

# Signal-layer reconciliation gate (F03): the C# AVWAP signal (regime/anchor/band/
# bounce/frozen-target) was never validated to reproduce the EXP-020 Python event set.
# On 5m the cTrader feed reproduces local bars to float precision (VAL-002), so the 5m
# event set is the clean place to isolate signal-layer parity from feed drift. A 5m
# divergence cannot be attributed to "benign feed coverage" and blocks a CONSISTENT
# upgrade. (1h/4h feed differences remain absorbed by the count tolerance.)
SIGNAL_MATCH_MIN = 0.98         # >= 98% of EXP-020 5m triggers matched by the C# event set
SIGNAL_TARGET_REL = 1e-3        # median rel. diff of matched frozen targets must be <= this

# Names of the frozen inference functions whose source must match EXP-027.
FROZEN_FUNCTIONS: tuple[str, ...] = (
    "domain_effect", "build_strata", "bootstrap_effect_distribution",
    "permutation_p", "holm_adjust", "decide_label", "sortino_ratio",
    "wilson_interval", "nearest_controls", "equity_advantage",
)


# --------------------------------------------------------------------------- #
# Upstream helper modules (validated, side-effect-free at import)
# --------------------------------------------------------------------------- #
def _load_module(name: str, path: Path):
    """Import a validated upstream experiment module by file path (no main run)."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # register before exec for @dataclass introspection
    spec.loader.exec_module(module)
    return module


EXP022 = _load_module("exp022_helpers", EXP022_CODE)


# --------------------------------------------------------------------------- #
# I/O helpers
# --------------------------------------------------------------------------- #
def configure_logging() -> None:
    """Configure concise INFO logging for the manual run."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                        datefmt="%H:%M:%S")


def ensure_output_dirs() -> None:
    """Create ``results/`` and ``plots/`` (orchestration-time only)."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> dict[str, Any]:
    """Read a JSON metadata file (raises if absent)."""
    if not path.exists():
        raise FileNotFoundError(f"missing metadata: {path}")
    return json.loads(path.read_text())


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write dict rows to CSV (empty-safe)."""
    if not rows:
        path.write_text("")
        return
    pl.DataFrame(rows).write_csv(path)


# --------------------------------------------------------------------------- #
# Step 0 — frozen-inference + control-matching integrity guards (D3)
# --------------------------------------------------------------------------- #
def verify_frozen_inference() -> str:
    """Assert the local frozen inference functions match the EXP-027 source.

    Returns
    -------
    str
        16-char hash prefix of the concatenated frozen-function source. Must equal
        EXP-028's ``ea261b9ee0a8aca3``.
    """
    ref_mod = _load_module("exp027_event_method", EXP027_METHOD)
    local_src, ref_src = [], []
    for name in FROZEN_FUNCTIONS:
        local_fn = getattr(EM, name, None)
        ref_fn = getattr(ref_mod, name, None)
        if local_fn is None or ref_fn is None:
            raise ValueError(f"FROZEN_INFERENCE_MODIFIED: function {name} missing")
        local_src.append(inspect.getsource(local_fn))
        ref_src.append(inspect.getsource(ref_fn))
    h_local = hashlib.sha256("".join(local_src).encode()).hexdigest()
    h_ref = hashlib.sha256("".join(ref_src).encode()).hexdigest()
    if h_local != h_ref:
        raise ValueError(
            "FROZEN_INFERENCE_MODIFIED: local inference tail diverges from EXP-027 "
            f"(local={h_local[:16]} != ref={h_ref[:16]}). Re-copy event_method.py."
        )
    LOGGER.info("Frozen inference tail verified against EXP-027 (hash=%s)", h_local[:16])
    return h_local[:16]


# --------------------------------------------------------------------------- #
# Dependency gate
# --------------------------------------------------------------------------- #
def check_dependencies() -> dict[str, str]:
    """Assert EXP-027 METHOD_VALID and EXP-028 results present (comparison target)."""
    exp027 = load_json(EXP027_RESULTS / "run_metadata.json")
    mv = exp027.get("method_verdict", "")
    verdict027 = str(mv.get("verdict", "")) if isinstance(mv, dict) else str(mv)
    if verdict027 != "METHOD_VALID":
        raise ValueError(f"EXP-027 method_verdict must be METHOD_VALID, got {verdict027!r}")
    for artifact in (EXP028_RESULTS / "event_level_results.csv",
                     EXP028_RESULTS / "run_metadata.json"):
        if not artifact.exists():
            raise FileNotFoundError(f"missing EXP-028 comparison artifact: {artifact}")
    exp028 = load_json(EXP028_RESULTS / "run_metadata.json")
    LOGGER.info("Dependency gate PASS (EXP-027=%s, EXP-028=%s)",
                verdict027, exp028.get("overall_verdict"))
    return {"EXP-027": verdict027, "EXP-028": str(exp028.get("overall_verdict", ""))}


def load_exp028_reference() -> dict[str, dict[str, Any]]:
    """Load EXP-028 PRIMARY per-domain results as the parity reference."""
    ref = pl.read_csv(EXP028_RESULTS / "event_level_results.csv")
    out: dict[str, dict[str, Any]] = {}
    for row in ref.iter_rows(named=True):
        out[str(row["domain"])] = row
    return out


def load_ref_pyramid() -> dict[str, int]:
    """Load EXP-028 per-domain pyramid counts for the F04 pyramid-split count gate.

    EXP-028's per-domain ``n_pyramid`` lives in its ``event_diagnostics.csv`` (the
    run-metadata ``pyramid_split`` is only a dataset total), so the per-domain pyramid
    tolerance cannot be checked without loading it.
    """
    path = EXP028_RESULTS / "event_diagnostics.csv"
    if not path.exists():
        raise FileNotFoundError(f"missing EXP-028 event_diagnostics.csv (F04 pyramid gate): {path}")
    diag = pl.read_csv(path)
    return {str(row["domain"]): int(row["n_pyramid"]) for row in diag.iter_rows(named=True)}


# --------------------------------------------------------------------------- #
# Step 1/2 — locate corrected cTrader runs; build cTrader-feed domain frame (D1, D5)
# --------------------------------------------------------------------------- #
def discover_corrected_runs() -> dict[tuple[str, str], Path]:
    """Map (instrument, domain) -> latest corrected cTrader run directory.

    A corrected EXP-029 run is recognised by the presence of
    ``avwap_events.parquet`` (the serialized event-detail table). EXP-023
    ``avwap_baseline_*`` runs lack it and are skipped (D1: not reusable).

    Returns
    -------
    dict[tuple[str, str], Path]
        Newest corrected run directory per cell.
    """
    chosen: dict[tuple[str, str], Path] = {}
    for inst in INSTRUMENTS:
        for domain in DOMAINS:
            pattern = f"{STRATEGY_NAME}_{inst.lower()}_{domain}_*"
            candidates = sorted(
                d for d in RUNS_DIR.glob(pattern)
                if d.is_dir() and (d / "avwap_events.parquet").exists()
                and (d / "positions.parquet").exists()
            )
            if candidates:
                chosen[(inst, domain)] = candidates[-1]  # latest by timestamp suffix
    return chosen


def _parse_fence(stamp: str) -> datetime:
    """Parse an ``...Z`` ISO fence string to a naive UTC datetime for comparison."""
    return datetime.fromisoformat(stamp.replace("Z", "+00:00")).replace(tzinfo=None)


def load_cell_frame(run_dir: Path, instrument: str) -> dict[str, Any]:
    """Load a corrected run's positions into a cTrader-feed domain frame.

    Returns ``close`` (RealClose), ``log_close``, per-bar ``regime_id`` /
    ``regime_dir``, ``times`` (SourceCloseTime list), and ``n``. Re-asserts strict
    monotonic SourceCloseTime and the per-instrument holdout fence (D5).
    """
    pos = (
        pl.read_parquet(run_dir / "positions.parquet")
        .sort("SourceCloseTime")
    )
    for col in ("RegimeId", "RegimeDirection"):
        if col not in pos.columns:
            raise ValueError(
                f"{run_dir.name}: positions.parquet missing '{col}' — run is not the "
                "corrected EXP-029 emission (regime serialization required)."
            )
    times = pos.get_column("SourceCloseTime").to_list()
    if any(times[i] >= times[i + 1] for i in range(len(times) - 1)):
        raise ValueError(f"{run_dir.name}: SourceCloseTime is not strictly increasing.")
    fence = _parse_fence(ANALYSIS_END[instrument])
    max_t = times[-1] if times else None
    if max_t is not None and max_t >= fence:
        raise ValueError(
            f"{run_dir.name}: holdout fence breach — max SourceCloseTime {max_t} "
            f">= AnalysisEndUtc {fence}."
        )
    close = pos.get_column("RealClose").to_numpy().astype(float)
    return {
        "close": close,
        "log_close": np.log(close),
        "regime_id": pos.get_column("RegimeId").to_numpy().astype(np.int64),
        "regime_dir": pos.get_column("RegimeDirection").to_numpy().astype(np.int64),
        "times": times,
        "n": pos.height,
        "max_source_close_time": max_t,
    }


# --------------------------------------------------------------------------- #
# Step 3 — event ingestion + index alignment + regime LUT (D4, D6)
# --------------------------------------------------------------------------- #
# Map serialized PascalCase event-detail columns to the snake_case the EXP-022
# helpers expect.
EVENT_COL_MAP = {
    "RegimeId": "regime_id",
    "Direction": "direction",
    "IsPyramidBounce": "is_pyramid_bounce",
    "AnchorIdx": "anchor_idx",
    "TriggerIdx": "trigger_idx_emitted",
    "TriggerClose": "trigger_close",
    "FavorableTargetAtTrigger": "favorable_target_at_trigger",
    "AdverseTargetAtTrigger": "adverse_target_at_trigger",
    "AnchorAgeBars": "anchor_age_bars",
    "SourceCloseTime": "trigger_time",
    # EXP-029 (F01): the C#-executed completion per bounce (exit-parity grading).
    "ExitIdx": "ctrader_exit_idx",
    "ExitTime": "ctrader_exit_time",
    "ExitClose": "ctrader_exit_close",
    "ExitReason": "ctrader_exit_reason",
    "ExitBars": "ctrader_exit_bars",
    "ExitLifetimeBps": "ctrader_exit_bps",
}

# Columns the corrected EXP-029 emission MUST carry (distinguishes it from any
# pre-correction run and guarantees the exit-parity grading is possible).
REQUIRED_EVENT_COLS: tuple[str, ...] = (
    "regime_id", "direction", "is_pyramid_bounce", "anchor_idx", "trigger_close",
    "favorable_target_at_trigger", "adverse_target_at_trigger", "anchor_age_bars",
    "ctrader_exit_idx", "ctrader_exit_reason", "ctrader_exit_bps",
)


def load_event_detail(run_dir: Path, instrument: str, domain: str,
                      frame: dict[str, Any]) -> pl.DataFrame:
    """Load the cTrader event-detail table and align triggers to frame indices.

    Maps each event's ``SourceCloseTime`` (trigger time) to the integer index in
    the SourceCloseTime-ordered frame (timestamp alignment, D6 — never a bar-index
    transfer across feeds). Hard-fails if a trigger timestamp is absent or its
    ``TriggerClose`` disagrees with the frame ``RealClose`` at that index, or if the
    emitted ``TriggerIdx`` disagrees with the aligned index.
    """
    ev = pl.read_parquet(run_dir / "avwap_events.parquet")
    rename = {k: v for k, v in EVENT_COL_MAP.items() if k in ev.columns}
    ev = ev.rename(rename)
    missing_cols = [c for c in REQUIRED_EVENT_COLS if c not in ev.columns]
    if missing_cols:
        raise ValueError(
            f"{run_dir.name}: avwap_events.parquet missing {missing_cols} — run is not the "
            "corrected EXP-029 emission (the executed-exit columns are required for the "
            "F01 exit-parity grading; re-run the corrected AvwapBounceModel)."
        )
    time_to_idx = {t: i for i, t in enumerate(frame["times"])}
    trig_times = ev.get_column("trigger_time").to_list()
    missing = [t for t in trig_times if t not in time_to_idx]
    if missing:
        raise ValueError(
            f"{run_dir.name}: {len(missing)} event trigger timestamps absent from the "
            "positions frame (alignment failure)."
        )
    trig_idx = np.array([time_to_idx[t] for t in trig_times], dtype=np.int64)
    frame_close = frame["close"]
    ev_close = ev.get_column("trigger_close").to_numpy().astype(float)
    if not np.allclose(frame_close[trig_idx], ev_close, rtol=ALIGN_TOL_REL, atol=ALIGN_TOL_REL):
        bad = int(np.sum(~np.isclose(frame_close[trig_idx], ev_close,
                                     rtol=ALIGN_TOL_REL, atol=ALIGN_TOL_REL)))
        raise ValueError(f"{run_dir.name}: {bad} events: trigger_close != frame RealClose.")
    if "trigger_idx_emitted" in ev.columns:
        emitted = ev.get_column("trigger_idx_emitted").to_numpy().astype(np.int64)
        if not np.array_equal(emitted, trig_idx):
            raise ValueError(f"{run_dir.name}: emitted TriggerIdx != timestamp-aligned index.")
    ev = ev.with_columns(
        pl.Series("trigger_idx", trig_idx),
        pl.lit(instrument).alias("instrument"),
        pl.lit(domain).alias("domain"),
        pl.col("is_pyramid_bounce").cast(pl.Boolean),
        pl.col("ctrader_exit_idx").cast(pl.Int64),
        pl.col("ctrader_exit_bps").cast(pl.Float64),
    )
    return ev


def build_regimes_cell(frame: dict[str, Any], events_cell: pl.DataFrame) -> pl.DataFrame:
    """Derive the EXP-020-style regime summary from the per-bar regime sequence.

    Contiguous runs of equal ``RegimeId`` (excluding warmup id<=0) give
    ``regime_start_idx`` (== confirm bar), ``regime_end_idx``, and ``direction``.
    ``anchor_idx`` is taken from the event-detail (shared per regime); regimes
    without events get a harmless placeholder anchor (never referenced). This is a
    pure groupby on emitted state — NOT a re-derivation of the AVWAP signal (D4).
    """
    rid = frame["regime_id"]
    rdir = frame["regime_dir"]
    n = rid.size
    anchor_by_regime: dict[int, int] = {}
    if events_cell.height:
        for r, a in zip(events_cell.get_column("regime_id").to_list(),
                        events_cell.get_column("anchor_idx").to_list()):
            anchor_by_regime.setdefault(int(r), int(a))
    rows: list[dict[str, Any]] = []
    i = 0
    while i < n:
        cur = int(rid[i])
        j = i
        while j + 1 < n and int(rid[j + 1]) == cur:
            j += 1
        if cur > 0:
            rows.append({
                "regime_id": cur,
                "regime_start_idx": i,
                "regime_end_idx": j,
                "confirm_idx": i,
                "anchor_idx": anchor_by_regime.get(cur, i),
                "direction": int(rdir[i]),
            })
        i = j + 1
    return pl.DataFrame(rows) if rows else pl.DataFrame(
        schema={"regime_id": pl.Int64, "regime_start_idx": pl.Int64,
                "regime_end_idx": pl.Int64, "confirm_idx": pl.Int64,
                "anchor_idx": pl.Int64, "direction": pl.Int64})


# --------------------------------------------------------------------------- #
# Step 4 — PRIMARY symmetric own-exit lifetime construction (D2; EXP-022 reuse)
# --------------------------------------------------------------------------- #
def build_cell_lifetimes(
    instrument: str, domain: str, events_cell: pl.DataFrame,
    regimes_cell: pl.DataFrame, frame: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    """Per-cell event + matched-control lifetime rows + fixed-horizon paired diffs.

    Mirrors EXP-022 ``_event_with_controls`` exactly via the imported helpers, but
    driven by the cTrader-emitted events and the cTrader ``RealClose`` feed. Both
    event and controls complete under the same EXP-022 band-target / trend-change
    own-exit rule (symmetric own-exit). Returns ``(lifetime_rows, fh_rows,
    counters)``.
    """
    close = frame["close"]
    log_close = frame["log_close"]
    n = frame["n"]
    analysis_end_idx = n - 1
    regime_lut = EXP022.build_regime_lut(regimes_cell)
    tc_map = EXP022.build_trend_change_map(regimes_cell)
    trig = events_cell.get_column("trigger_idx").to_numpy().astype(np.int64)
    is_trigger, near_trigger = EXP022.build_exclusion_masks(n, trig)
    base_cache: dict[int, np.ndarray] = {}

    lifetime_rows: list[dict[str, Any]] = []
    fh_rows: list[dict[str, Any]] = []
    counters = {"invalid_target_events": 0, "events_no_controls": 0, "events_total": 0}

    for ev in events_cell.iter_rows(named=True):
        counters["events_total"] += 1
        rid = int(ev["regime_id"])
        if rid not in regime_lut:
            raise ValueError(f"{instrument}/{domain}: event regime_id={rid} absent from regime summary.")
        meta = regime_lut[rid]
        direction = int(ev["direction"])
        t = int(ev["trigger_idx"])
        trigger_close = float(ev["trigger_close"])
        fav_target = float(ev["favorable_target_at_trigger"])
        adv_target = float(ev["adverse_target_at_trigger"])
        is_pyr = bool(ev["is_pyramid_bounce"])

        fav_bps, adv_bps, *_ = EXP022.transfer_targets(
            direction, fav_target, adv_target, trigger_close, trigger_close)
        if not (fav_bps > 0.0 and adv_bps < 0.0):
            counters["invalid_target_events"] += 1
            continue

        if rid not in base_cache:
            base_cache[rid] = EXP022.regime_candidate_base(
                meta["start_idx"], meta["end_idx"], is_trigger, near_trigger)
        base = base_cache[rid]
        controls = EXP022.select_controls(base, meta["anchor_idx"],
                                          int(ev["anchor_age_bars"]), t, n)
        reportable = len(controls) >= EM.MIN_CONTROLS
        if not reportable:
            counters["events_no_controls"] += 1

        ev_outcome, ev_comp, ev_bars, ev_life, _ = EXP022.scan_lifetime(
            close, log_close, t, direction, fav_target, adv_target,
            tc_map.get(rid), analysis_end_idx)
        ct_exit_idx = ev["ctrader_exit_idx"]
        ct_exit_bps = ev["ctrader_exit_bps"]
        lifetime_rows.append(_lifetime_row(
            instrument, domain, rid, direction, is_pyr, "event", t, t,
            ev_outcome, ev_comp, ev_bars, ev_life, len(controls), reportable,
            ctrader_exit_idx=int(ct_exit_idx) if ct_exit_idx is not None else None,
            ctrader_exit_reason=str(ev["ctrader_exit_reason"]),
            ctrader_exit_bps=float(ct_exit_bps) if ct_exit_bps is not None else float("nan")))

        for c in controls:
            f_bps, a_bps, c_fav, c_adv = EXP022.transfer_targets(
                direction, fav_target, adv_target, trigger_close, float(close[c]))
            c_outcome, c_comp, c_bars, c_life, _ = EXP022.scan_lifetime(
                close, log_close, c, direction, c_fav, c_adv,
                tc_map.get(rid), analysis_end_idx)
            lifetime_rows.append(_lifetime_row(
                instrument, domain, rid, direction, is_pyr, "control", c, t,
                c_outcome, c_comp, c_bars, c_life, len(controls), reportable))

        if reportable:
            fh_rows.extend(_fixed_horizon_rows(
                instrument, domain, direction, t, controls, log_close, n))

    return lifetime_rows, fh_rows, counters


def _lifetime_row(
    instrument: str, domain: str, regime_id: int, direction: int, is_pyramid: bool,
    role: str, start_idx: int, event_trigger_idx: int, outcome: str,
    completion_idx: int | None, bars_to_completion: int | None, lifetime_bps: float | None,
    n_controls: int, reportable: bool,
    ctrader_exit_idx: int | None = None, ctrader_exit_reason: str | None = None,
    ctrader_exit_bps: float | None = None,
) -> dict[str, Any]:
    """Assemble one lifetime observation row (event or matched control).

    Event rows additionally carry the C#-executed completion (``ctrader_exit_*``) so
    the F01 exit-parity step can grade the corrected concurrent-completion code
    against the Python ``scan_lifetime`` on the same feed. Controls leave them ``None``.
    """
    return {
        "instrument": instrument, "domain": domain, "regime_id": regime_id,
        "direction": direction, "is_pyramid_bounce": is_pyramid, "role": role,
        "start_idx": start_idx, "event_trigger_idx": event_trigger_idx,
        "outcome": outcome, "completion_idx": completion_idx,
        "bars_to_completion": bars_to_completion, "lifetime_bps": lifetime_bps,
        "n_controls": n_controls, "reportable_event": reportable,
        "ctrader_exit_idx": ctrader_exit_idx, "ctrader_exit_reason": ctrader_exit_reason,
        "ctrader_exit_bps": ctrader_exit_bps,
    }


def _fixed_horizon_rows(
    instrument: str, domain: str, direction: int, t: int, controls: list[int],
    log_close: np.ndarray, n: int,
) -> list[dict[str, Any]]:
    """Fixed-horizon {1,3,6} paired-excess rows (cTrader-feed secondary-stability).

    Event h-forward signed return minus the mean of its controls' h-forward signed
    returns, for controls with a valid horizon window. Diagnostic input to the
    frozen ``decide_label`` secondary-stability guard (mirrors the role EXP-021
    reaction observations play in EXP-028).
    """
    rows: list[dict[str, Any]] = []
    for h in HORIZONS:
        if t + h > n - 1:
            continue
        ev_fwd = 10_000.0 * direction * (log_close[t + h] - log_close[t])
        cvals = [10_000.0 * direction * (log_close[c + h] - log_close[c])
                 for c in controls if c + h <= n - 1]
        if not cvals:
            continue
        rows.append({"instrument": instrument, "domain": domain, "horizon": h,
                     "direction": direction,
                     "paired_diff_bps": ev_fwd - float(np.mean(cvals)),
                     "reportable": True})
    return rows


def build_primary_excess(
    lifetime: pl.DataFrame, frames: dict[tuple[str, str], dict[str, Any]],
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Per-event symmetric own-exit paired excess (ports EXP-028 build_primary_excess).

    Excess = event ``lifetime_bps`` - mean(matched control ``lifetime_bps``); both
    completed under the same own-exit rule. Only completed (non right-censored) rows
    contribute; require >= EM.MIN_CONTROLS finite controls. Reconciles each row's
    lifetime_bps against the cTrader frame to guard index alignment.
    """
    diag: dict[str, Any] = {}
    lt = lifetime.filter(pl.col("outcome").is_in(COMPLETED_OUTCOMES))
    lt = lt.filter(pl.col("lifetime_bps").is_not_null())
    keys = ["instrument", "domain", "regime_id", "direction", "event_trigger_idx"]

    events = lt.filter((pl.col("role") == "event") & (pl.col("reportable_event")))
    controls = lt.filter(pl.col("role") == "control")
    ctrl_mean = (
        controls.group_by(keys)
        .agg(pl.col("lifetime_bps").mean().alias("mean_control_lifetime_bps"),
             pl.len().alias("n_controls_finite"))
    )
    merged = events.join(ctrl_mean, on=keys, how="inner")
    merged = merged.filter(pl.col("n_controls_finite") >= EM.MIN_CONTROLS)

    # Reconcile lifetime_bps vs frame recompute (vectorized per cell).
    recon_bad = 0
    for (inst, domain), frame in frames.items():
        lc = frame["log_close"]
        sub = merged.filter((pl.col("instrument") == inst) & (pl.col("domain") == domain))
        if sub.height == 0:
            continue
        si = sub.get_column("start_idx").to_numpy().astype(np.int64)
        ci = sub.get_column("completion_idx").to_numpy().astype(np.int64)
        d = sub.get_column("direction").to_numpy().astype(float)
        lb = sub.get_column("lifetime_bps").to_numpy().astype(float)
        oob = (ci >= lc.size) | (si >= lc.size) | (ci < 0) | (si < 0)
        safe = ~oob
        recomputed = 10_000.0 * d[safe] * (lc[ci[safe]] - lc[si[safe]])
        recon_bad += int(oob.sum() + np.sum(np.abs(recomputed - lb[safe]) > RECON_TOL_BPS))
    if recon_bad:
        raise ValueError(
            f"PRIMARY reconciliation failed for {recon_bad} events: lifetime_bps does "
            "not match cTrader-frame recompute (index misalignment)."
        )

    out = merged.with_columns(
        (pl.col("lifetime_bps") - pl.col("mean_control_lifetime_bps")).alias("paired_excess_bps")
    ).select(
        "instrument", "domain", "regime_id", "direction", "is_pyramid_bounce",
        "event_trigger_idx", "lifetime_bps", "mean_control_lifetime_bps",
        "paired_excess_bps", "n_controls_finite",
    )
    diag["n_primary_events"] = out.height
    diag["reconciliation_bad"] = recon_bad
    diag["n_pyramid"] = int(out.filter(pl.col("is_pyramid_bounce")).height)
    diag["n_nonpyramid"] = int(out.filter(~pl.col("is_pyramid_bounce")).height)
    LOGGER.info("PRIMARY events: %d (pyramid=%d, non-pyramid=%d); reconciliation clean",
                out.height, diag["n_pyramid"], diag["n_nonpyramid"])
    return out, diag


def fixed_horizon_effects(fh: pl.DataFrame) -> dict[str, dict[int, float]]:
    """Per-domain fixed-horizon excess effect (frozen ``domain_effect`` estimator)."""
    out: dict[str, dict[int, float]] = {}
    if fh.height == 0:
        return {d: {h: float("nan") for h in HORIZONS} for d in DOMAINS}
    for domain in DOMAINS:
        out[domain] = {}
        for h in HORIZONS:
            sub = fh.filter((pl.col("domain") == domain) & (pl.col("horizon") == h))
            if sub.height == 0:
                out[domain][h] = float("nan")
                continue
            diffs = sub.get_column("paired_diff_bps").to_numpy().astype(float)
            insts = sub.get_column("instrument").to_numpy()
            present = [i for i in INSTRUMENTS if (insts == i).any()]
            out[domain][h] = domain_effect(diffs, insts, present)
    return out


# --------------------------------------------------------------------------- #
# Step 4b — exit-parity grading of the corrected C# completion code (F01/F06)
# --------------------------------------------------------------------------- #
def build_exit_parity(
    lifetime: pl.DataFrame,
) -> tuple[list[dict[str, Any]], dict[str, bool | None]]:
    """Grade the C#-executed completion per event vs the Python scan on the same feed.

    The binding PRIMARY estimand re-scans exits in Python (for EXP-028 comparability),
    which on its own would leave the corrected C# concurrent-completion logic — the
    actual code the EXP-028 omission demanded — ungraded. This step closes that gap:
    for every Python-scanned event it compares the C#-executed completion (exit bar,
    reason, signed bps) against the Python ``scan_lifetime`` completion on the *same*
    cTrader feed and frozen targets. Same feed, same targets, same trend-change
    boundary, so the only legitimate slack is float rounding; a genuine multi-position
    completion bug drops the per-domain match rate below ``EXIT_PARITY_MIN``.

    Restricted to the Python event population (role==event), which already dropped
    invalid-target-geometry bounces, so the comparison is apples-to-apples (F06) — not
    a raw blotter count over a different population. A systematic exit-index offset is
    caught here too (the bar-match check fails en masse), so no separate guard needed.

    Returns ``(per_domain_rows, per_domain_ok)`` where ``per_domain_ok[d]`` is
    ``True`` / ``False`` / ``None`` (None == no comparable events).
    """
    completed = set(COMPLETED_OUTCOMES)
    events = lifetime.filter(pl.col("role") == "event")
    rows: list[dict[str, Any]] = []
    per_domain_ok: dict[str, bool | None] = {}
    for domain in DOMAINS:
        cell = events.filter(pl.col("domain") == domain)
        n = cell.height
        if n == 0:
            per_domain_ok[domain] = None
            rows.append({"domain": domain, "n_events": 0, "n_matched": 0, "match_rate": None,
                         "n_bar_mismatch": 0, "n_reason_mismatch": 0, "n_bps_mismatch": 0,
                         "max_bps_discrepancy": None, "exit_parity_ok": None})
            continue
        n_match = n_bar = n_reason = n_bps = 0
        max_disc = 0.0
        for r in cell.iter_rows(named=True):
            py_completed = r["outcome"] in completed
            ct_reason = r["ctrader_exit_reason"]
            ct_idx = r["ctrader_exit_idx"]
            ct_completed = ct_reason not in (None, "open") and ct_idx is not None and ct_idx >= 0
            if not py_completed and not ct_completed:
                n_match += 1                       # both leave the position open: agree
                continue
            if py_completed != ct_completed:
                n_reason += 1                       # one completed, one open: disagreement
                continue
            reason_ok = ct_reason == r["outcome"]
            bar_ok = r["completion_idx"] is not None and int(ct_idx) == int(r["completion_idx"])
            ct_bps, py_bps = r["ctrader_exit_bps"], r["lifetime_bps"]
            disc = abs(float(ct_bps) - float(py_bps)) if (ct_bps is not None and py_bps is not None) else float("inf")
            bps_ok = disc <= EXIT_PARITY_BPS_TOL
            if np.isfinite(disc):
                max_disc = max(max_disc, disc)
            if not reason_ok:
                n_reason += 1
            if not bar_ok:
                n_bar += 1
            if not bps_ok:
                n_bps += 1
            if reason_ok and bar_ok and bps_ok:
                n_match += 1
        rate = n_match / n
        ok = rate >= EXIT_PARITY_MIN
        per_domain_ok[domain] = ok
        rows.append({"domain": domain, "n_events": n, "n_matched": n_match, "match_rate": rate,
                     "n_bar_mismatch": n_bar, "n_reason_mismatch": n_reason, "n_bps_mismatch": n_bps,
                     "max_bps_discrepancy": max_disc, "exit_parity_ok": ok})
    LOGGER.info("Exit-parity (C# completion vs Python scan): %s",
                {row["domain"]: row["match_rate"] for row in rows})
    return rows, per_domain_ok


# --------------------------------------------------------------------------- #
# Step 3b — 5m signal-layer reconciliation vs the EXP-020 substrate (F03)
# --------------------------------------------------------------------------- #
def _ts_key(value: Any) -> str:
    """Second-resolution comparable key for a timestamp (datetime or ISO string)."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.replace("T", " ").replace("Z", "").strip()[:19]
    return value.strftime("%Y-%m-%d %H:%M:%S")


def reconcile_signal_layer(
    event_detail_5m: pl.DataFrame,
) -> tuple[list[dict[str, Any]], bool]:
    """Reconcile the C# 5m AVWAP event set against the EXP-020 Python substrate (F03).

    On 5m the cTrader feed reproduces local bars to float precision (VAL-002), so the
    5m event set isolates *signal-layer* parity (regime / anchor / band / bounce /
    frozen targets) from feed drift. This guards against the design's blanket
    attribution of all count/effect drift to "benign feed coverage": a real C#-vs-Python
    signal divergence would surface here on the feed-exact domain. A 5m divergence
    blocks a CONSISTENT upgrade. (1h/4h feed differences are expected and remain
    absorbed by the count tolerance, so they are not reconciled.)

    Returns ``(per_instrument_rows, signal_5m_ok)``.
    """
    path = EXP020_RESULTS / "avwap_events.csv"
    if not path.exists():
        raise FileNotFoundError(f"missing EXP-020 substrate for signal reconciliation: {path}")
    exp020 = pl.read_csv(path, try_parse_dates=True).filter(pl.col("domain") == "5m")
    rows: list[dict[str, Any]] = []
    all_ok = True
    any_inst = False
    for inst in INSTRUMENTS:
        ref = exp020.filter(pl.col("instrument") == inst)
        if ref.height == 0:
            continue
        any_inst = True
        cur = (event_detail_5m.filter(pl.col("instrument") == inst)
               if event_detail_5m.height else event_detail_5m)
        ref_map = {_ts_key(t): row for t, row in
                   zip(ref.get_column("trigger_time").to_list(), ref.iter_rows(named=True))}
        cur_map = ({_ts_key(t): row for t, row in
                    zip(cur.get_column("trigger_time").to_list(), cur.iter_rows(named=True))}
                   if cur.height else {})
        matched = set(ref_map) & set(cur_map)
        frac = len(matched) / ref.height
        rels: list[float] = []
        for k in matched:
            rr, cc = ref_map[k], cur_map[k]
            for col in ("favorable_target_at_trigger", "adverse_target_at_trigger"):
                a, b = float(rr[col]), float(cc[col])
                if a != 0.0:
                    rels.append(abs(b - a) / abs(a))
        med_rel = float(np.median(rels)) if rels else 0.0
        max_rel = float(np.max(rels)) if rels else 0.0
        ok = frac >= SIGNAL_MATCH_MIN and med_rel <= SIGNAL_TARGET_REL
        all_ok = all_ok and ok
        rows.append({"instrument": inst, "domain": "5m", "n_exp020": ref.height,
                     "n_ctrader": cur.height, "n_matched": len(matched), "frac_matched": frac,
                     "median_target_rel_diff": med_rel, "max_target_rel_diff": max_rel,
                     "signal_ok": ok})
    signal_5m_ok = bool(all_ok and any_inst)
    LOGGER.info("Signal-layer 5m reconciliation vs EXP-020: ok=%s %s", signal_5m_ok,
                {row["instrument"]: round(row["frac_matched"], 4) for row in rows})
    return rows, signal_5m_ok


# --------------------------------------------------------------------------- #
# Step 5 — frozen-tail inference on the per-event excess (ports EXP-028)
# --------------------------------------------------------------------------- #
def reportable_instruments(cell: pl.DataFrame) -> list[str]:
    """Instruments in a domain meeting per-instrument reportability thresholds."""
    out = []
    for inst in INSTRUMENTS:
        sub = cell.filter(pl.col("instrument") == inst)
        n_bull = sub.filter(pl.col("direction") == 1).height
        n_bear = sub.filter(pl.col("direction") == -1).height
        if (sub.height >= MIN_REPORTABLE_EVENTS and n_bull >= MIN_DIRECTION_EVENTS
                and n_bear >= MIN_DIRECTION_EVENTS):
            out.append(inst)
    return out


def infer_domain(cell: pl.DataFrame, rng: np.random.Generator) -> dict[str, Any]:
    """Frozen-tail inference (effect, regime-cluster bootstrap CI, permutation p)."""
    insts = reportable_instruments(cell)
    total = cell.height
    n_bull = cell.filter(pl.col("direction") == 1).height
    n_bear = cell.filter(pl.col("direction") == -1).height
    base = {"n_events": total, "n_bull": n_bull, "n_bear": n_bear,
            "n_instruments": len(insts), "reportable_instruments": insts}
    if len(insts) < DOMAIN_MIN_INSTRUMENTS:
        return {**base, "effect_bps": None, "ci_low": None, "ci_high": None,
                "ci_half_width": None, "raw_p": None}

    cell = cell.filter(pl.col("instrument").is_in(insts))
    diffs = cell.get_column("paired_excess_bps").to_numpy().astype(float)
    inst_labels = cell.get_column("instrument").to_numpy()
    dir_labels = cell.get_column("direction").to_numpy().astype(int)
    regime_labels = cell.get_column("regime_id").to_numpy().astype(int)

    effect = domain_effect(diffs, inst_labels, insts)
    strata = build_strata(diffs, inst_labels, dir_labels, regime_labels, insts)
    boot = bootstrap_effect_distribution(strata, insts, rng, N_BOOT, CHUNK)
    ci_low = float(np.percentile(boot, CI_PERCENTILES[0]))
    ci_high = float(np.percentile(boot, CI_PERCENTILES[1]))
    counts = np.array([int((inst_labels == i).sum()) for i in insts], dtype=float)
    inst_index = np.array([insts.index(i) for i in inst_labels], dtype=np.int64)
    raw_p = permutation_p(diffs, inst_index, counts, effect, rng, N_PERM, CHUNK)
    return {**base, "effect_bps": effect, "ci_low": ci_low, "ci_high": ci_high,
            "ci_half_width": (ci_high - ci_low) / 2.0, "raw_p": raw_p}


def run_primary(primary: pl.DataFrame, fixedh: dict[str, dict[int, float]]) -> dict[str, dict[str, Any]]:
    """PRIMARY per-domain verdicts via the frozen tail + Holm + secondary stability."""
    results: dict[str, dict[str, Any]] = {}
    raw_p: dict[str, float] = {}
    for domain in DOMAINS:
        cell = primary.filter(pl.col("domain") == domain)
        rng = np.random.default_rng(seed_for(EXPERIMENT_ID, "primary", domain))
        res = infer_domain(cell, rng)
        results[domain] = res
        if res["raw_p"] is not None:
            raw_p[domain] = res["raw_p"]
    adjusted = holm_adjust(raw_p) if raw_p else {}
    for domain, res in results.items():
        hp = adjusted.get(domain)
        res["holm_p"] = hp
        if res["effect_bps"] is None or hp is None:
            res["verdict"] = "UNDER_POWERED"
            continue
        eff_h1 = fixedh.get(domain, {}).get(SEC_LOW_HORIZON, res["effect_bps"])
        eff_h6 = fixedh.get(domain, {}).get(SEC_HIGH_HORIZON, res["effect_bps"])
        eff_h1 = res["effect_bps"] if (eff_h1 is None or not np.isfinite(eff_h1)) else eff_h1
        eff_h6 = res["effect_bps"] if (eff_h6 is None or not np.isfinite(eff_h6)) else eff_h6
        res["sec_h1_bps"], res["sec_h6_bps"] = eff_h1, eff_h6
        res["verdict"] = decide_label(res["effect_bps"], res["ci_low"], res["ci_high"],
                                      hp, ALPHA, eff_h1, eff_h6)
    return results


# --------------------------------------------------------------------------- #
# Step 6 — parity comparison vs EXP-028 + disposition
# --------------------------------------------------------------------------- #
def _ci_overlap(lo1: float, hi1: float, lo2: float, hi2: float) -> bool:
    """True if two closed intervals overlap."""
    return max(lo1, lo2) <= min(hi1, hi2)


def _count_delta(a: float, b: float) -> float:
    """Relative count delta |a-b|/max(b,1) (b is the EXP-028 reference)."""
    return abs(a - b) / max(abs(b), 1.0)


def compare_parity(
    primary_res: dict[str, dict[str, Any]], primary: pl.DataFrame,
    ref: dict[str, dict[str, Any]], ref_pyramid: dict[str, int],
    exit_parity_ok: dict[str, bool | None], signal_5m_ok: bool,
) -> tuple[list[dict[str, Any]], str]:
    """Per-domain parity bands + overall disposition (analysis-plan.md Step 6).

    Binding per-domain criteria (all required for CONSISTENT):
      * verdict agreement (3-way label);
      * magnitude equivalence — |Δeffect| inside the predeclared margin (F02), the
        principled replacement for the demoted "point inside EXP-028 CI" check;
      * count alignment within ±10% on total / bull / bear / **pyramid** (F04);
      * exit-parity OK — the C# completion code reproduces the Python scan (F01);
      * on 5m, signal-layer reconciliation OK (F03).
    A magnitude divergence beyond the larger margin, an exit-parity failure, or a
    verdict disagreement with non-overlapping CIs makes the domain INCONSISTENT — so a
    real execution-path divergence can now actually downgrade EXP-028, not just fail to
    upgrade it. CI overlap is retained as a diagnostic, not the primary signal.
    """
    rows: list[dict[str, Any]] = []
    consistent_domains = 0
    bands: list[str] = []
    for domain in DOMAINS:
        r = primary_res[domain]
        e = ref.get(domain, {})
        n_ctr = primary.filter(pl.col("domain") == domain).height
        n_bull = primary.filter((pl.col("domain") == domain) & (pl.col("direction") == 1)).height
        n_bear = primary.filter((pl.col("domain") == domain) & (pl.col("direction") == -1)).height
        n_pyr = primary.filter((pl.col("domain") == domain) & pl.col("is_pyramid_bounce")).height

        eff, ref_eff = r.get("effect_bps"), e.get("effect_bps")
        ref_lo, ref_hi = e.get("ci_low"), e.get("ci_high")
        ref_n, ref_bull, ref_bear = e.get("n_events"), e.get("n_bull"), e.get("n_bear")
        ref_pyr = ref_pyramid.get(domain)
        verdict_match = (r.get("verdict") == e.get("verdict"))
        contained = (eff is not None and ref_lo is not None and ref_lo <= eff <= ref_hi)
        ci_ov = (r.get("ci_low") is not None and ref_lo is not None
                 and _ci_overlap(r["ci_low"], r["ci_high"], ref_lo, ref_hi))

        # Count alignment incl. pyramid split (F04).
        d_total = _count_delta(n_ctr, ref_n) if ref_n is not None else float("nan")
        d_bull = _count_delta(n_bull, ref_bull) if ref_bull is not None else float("nan")
        d_bear = _count_delta(n_bear, ref_bear) if ref_bear is not None else float("nan")
        d_pyr = _count_delta(n_pyr, ref_pyr) if ref_pyr is not None else float("nan")
        deltas = (d_total, d_bull, d_bear, d_pyr)
        count_ok = all(np.isfinite(x) and x <= COUNT_TOL_CONSISTENT for x in deltas)
        count_inconclusive = any(np.isfinite(x) and x > COUNT_TOL_INCONCLUSIVE for x in deltas)

        # Effect-difference equivalence (F02).
        if eff is not None and ref_eff is not None:
            delta_eff = abs(eff - ref_eff)
            equiv_margin = max(EFFECT_EQUIV_ABS_BPS, EFFECT_EQUIV_REL * abs(ref_eff))
            div_margin = max(EFFECT_EQUIV_ABS_BPS, EFFECT_DIVERGENT_REL * abs(ref_eff))
            magnitude_equivalent = delta_eff <= equiv_margin
            magnitude_divergent = delta_eff > div_margin
        else:
            delta_eff = None
            magnitude_equivalent = magnitude_divergent = False

        ep_ok = exit_parity_ok.get(domain)            # True / False / None
        sig_ok = signal_5m_ok if domain == "5m" else True

        # A verdict conflict is only INCONSISTENT when EXP-029 actually produced a
        # finite, contradicting estimate; an underpowered (effect=None) domain cannot
        # contradict EXP-028 and is INCONCLUSIVE. Exit-parity failure is INCONSISTENT
        # regardless of power (it is about C# code correctness, not statistical power).
        verdict_conflict = (not verdict_match) and (eff is not None) and (not ci_ov)
        inconsistent = (verdict_conflict or magnitude_divergent or ep_ok is False)
        consistent = (verdict_match and magnitude_equivalent and count_ok
                      and ep_ok is True and sig_ok)
        if inconsistent:
            band = "INCONSISTENT"
        elif consistent:
            band = "CONSISTENT"
            consistent_domains += 1
        else:
            band = "INCONCLUSIVE"
        bands.append(band)
        rows.append({
            "domain": domain,
            "exp029_effect_bps": eff, "exp029_ci_low": r.get("ci_low"),
            "exp029_ci_high": r.get("ci_high"), "exp029_verdict": r.get("verdict"),
            "exp029_n_events": n_ctr, "exp029_n_pyramid": n_pyr,
            "exp028_effect_bps": ref_eff, "exp028_ci_low": ref_lo, "exp028_ci_high": ref_hi,
            "exp028_verdict": e.get("verdict"), "exp028_n_events": ref_n, "exp028_n_pyramid": ref_pyr,
            "verdict_match": verdict_match, "point_in_exp028_ci": contained, "ci_overlap": ci_ov,
            "effect_delta_bps": delta_eff, "magnitude_equivalent": magnitude_equivalent,
            "magnitude_divergent": magnitude_divergent,
            "count_delta_total": d_total, "count_delta_bull": d_bull,
            "count_delta_bear": d_bear, "count_delta_pyramid": d_pyr,
            "count_within_10pct": count_ok, "exit_parity_ok": ep_ok,
            "signal_layer_ok": sig_ok, "band": band,
        })
    # INCONSISTENT on any domain vetoes the upgrade and forces escalation; otherwise
    # CONSISTENT requires >= 2/3 fully-consistent domains AND a clean 5m signal layer.
    if "INCONSISTENT" in bands:
        overall = "INCONSISTENT"
    elif consistent_domains >= DISPOSITION_MIN_DOMAINS and signal_5m_ok:
        overall = "CONSISTENT"
    else:
        overall = "INCONCLUSIVE"
    return rows, overall


# --------------------------------------------------------------------------- #
# Step 7 — diagnostics (non-binding)
# --------------------------------------------------------------------------- #
def equity_companion(primary: pl.DataFrame) -> dict[str, dict[str, Any]]:
    """Exposure-matched equity companion on PRIMARY own-exit trades (non-gating)."""
    out: dict[str, dict[str, Any]] = {}
    for domain in DOMAINS:
        cell = primary.filter(pl.col("domain") == domain)
        adv, sortino_diff, strat_terms, base_terms = [], [], [], []
        for inst in INSTRUMENTS:
            sub = cell.filter(pl.col("instrument") == inst)
            if sub.height == 0:
                continue
            strat = sub.get_column("lifetime_bps").to_numpy().astype(float)
            base = sub.get_column("mean_control_lifetime_bps").to_numpy().astype(float)
            adv.append(float(np.nansum(strat) - np.nansum(base)))
            sortino_diff.append(sortino_ratio(strat) - sortino_ratio(base))
            strat_terms.append(float(np.nansum(strat)))
            base_terms.append(float(np.nansum(base)))
        if not adv:
            out[domain] = {"strategy_terminal_bps": float("nan"),
                           "baseline_terminal_bps": float("nan"),
                           "advantage_bps": float("nan"), "advantage_rate": float("nan"),
                           "sortino_diff": float("nan")}
            continue
        out[domain] = {"strategy_terminal_bps": float(np.mean(strat_terms)),
                       "baseline_terminal_bps": float(np.mean(base_terms)),
                       "advantage_bps": float(np.mean(adv)),
                       "advantage_rate": float(np.mean([a > 0 for a in adv])),
                       "sortino_diff": float(np.nanmean(sortino_diff))}
    return out


# --------------------------------------------------------------------------- #
# Plotting (3)
# --------------------------------------------------------------------------- #
def _verdict_color(verdict: str | None) -> str:
    if verdict == "EVIDENCE_FOR":
        return "#2ecc71"
    if verdict and "AGAINST" in verdict:
        return "#e74c3c"
    return "#95a5a6"


def plot_effect_forest(primary_res: dict, ref: dict, path: Path) -> None:
    """cTrader (EXP-029) vs Python (EXP-028) per-domain effect forest with 95% CIs."""
    fig, ax = plt.subplots(figsize=(10, 5))
    for i, domain in enumerate(DOMAINS):
        r = primary_res[domain]
        e = ref.get(domain, {})
        y029, y028 = i + 0.12, i - 0.12
        if e.get("effect_bps") is not None:
            ax.errorbar(e["effect_bps"], y028,
                        xerr=[[e["effect_bps"] - e["ci_low"]], [e["ci_high"] - e["effect_bps"]]],
                        fmt="s", color="#7f8c8d", capsize=4, markersize=7, label="EXP-028" if i == 0 else None)
        if r.get("effect_bps") is not None:
            ax.errorbar(r["effect_bps"], y029,
                        xerr=[[r["effect_bps"] - r["ci_low"]], [r["ci_high"] - r["effect_bps"]]],
                        fmt="o", color=_verdict_color(r.get("verdict")), capsize=4, markersize=8,
                        label="EXP-029 (cTrader)" if i == 0 else None)
        else:
            ax.text(0, y029, f"{domain}: {r.get('verdict')}", va="center", fontsize=8)
    ax.axvline(0, color="black", ls="--", lw=0.8, alpha=0.6)
    ax.set_yticks(range(len(DOMAINS)))
    ax.set_yticklabels(DOMAINS)
    ax.set_xlabel("PRIMARY own-exit matched-control excess (bps), 95% CI")
    ax.set_title("EXP-029 cTrader vs EXP-028 Python — per-domain event-level effect", fontweight="bold")
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_count_diagnostic(primary: pl.DataFrame, ref: dict, diag: dict, path: Path) -> None:
    """Event count + pyramid split: EXP-029 vs EXP-028."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    x = np.arange(len(DOMAINS))
    e029 = [primary.filter(pl.col("domain") == d).height for d in DOMAINS]
    e028 = [ref.get(d, {}).get("n_events") or 0 for d in DOMAINS]
    axes[0].bar(x - 0.2, e029, 0.4, label="EXP-029 (cTrader)", color="#3498db")
    axes[0].bar(x + 0.2, e028, 0.4, label="EXP-028 (Python)", color="#95a5a6")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(DOMAINS)
    axes[0].set_ylabel("PRIMARY event count")
    axes[0].set_title("Event counts vs EXP-028 (±10% / ±20% tolerances)")
    axes[0].legend(fontsize=8)

    pyr = [primary.filter((pl.col("domain") == d) & pl.col("is_pyramid_bounce")).height for d in DOMAINS]
    nonpyr = [primary.filter((pl.col("domain") == d) & ~pl.col("is_pyramid_bounce")).height for d in DOMAINS]
    axes[1].bar(x - 0.2, nonpyr, 0.4, label="Non-pyramid", color="#34495e")
    axes[1].bar(x + 0.2, pyr, 0.4, label="Pyramid", color="#9b59b6")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(DOMAINS)
    axes[1].set_title(f"EXP-029 pyramid split (EXP-028: {diag.get('ref_pyramid_split')})")
    axes[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _yn(value: bool | None) -> str:
    """Render a tri-state gate (True/False/None) as Y / N / - for the parity table."""
    return "-" if value is None else ("Y" if value else "N")


def plot_parity_table(parity_rows: list[dict[str, Any]], overall: str,
                      signal_5m_ok: bool, path: Path) -> None:
    """Per-domain verdict / parity alignment table figure (binding gates surfaced)."""
    fig, ax = plt.subplots(figsize=(13, 3.4))
    ax.axis("off")
    cols = ["domain", "EXP-029 verdict", "EXP-028 verdict", "verdict\nmatch",
            "mag\nequiv", "counts\n±10%", "exit\nparity", "CI\noverlap", "band"]
    table_data = [[
        r["domain"], str(r["exp029_verdict"]), str(r["exp028_verdict"]),
        _yn(r["verdict_match"]), _yn(r["magnitude_equivalent"]), _yn(r["count_within_10pct"]),
        _yn(r["exit_parity_ok"]), _yn(r["ci_overlap"]), r["band"],
    ] for r in parity_rows]
    tbl = ax.table(cellText=table_data, colLabels=cols, loc="center", cellLoc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1, 1.6)
    for j, r in enumerate(parity_rows):
        color = {"CONSISTENT": "#d5f5e3", "INCONCLUSIVE": "#fdebd0",
                 "INCONSISTENT": "#fadbd8"}.get(r["band"], "#ffffff")
        tbl[(j + 1, len(cols) - 1)].set_facecolor(color)
    sig = "OK" if signal_5m_ok else "DIVERGENT"
    ax.set_title(f"EXP-029 parity — overall disposition: {overall}  (signal-layer 5m: {sig})",
                 fontweight="bold", pad=14)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Save
# --------------------------------------------------------------------------- #
def save_outputs(primary_res, primary, parity_rows, overall, equity, exitparity,
                 signalrecon, signal_5m_ok, fixedh, diag, metadata) -> None:
    """Write all result CSVs, plots, and run metadata.

    ``metadata['_ref']`` (the EXP-028 comparison rows, plot-only) is consumed for
    the figures and removed before the metadata JSON is written.
    """
    ensure_output_dirs()
    ref = metadata.pop("_ref", {})
    write_rows(RESULTS_DIR / "event_level_results.csv", [
        {"domain": d, **{k: primary_res[d].get(k) for k in
         ("effect_bps", "ci_low", "ci_high", "ci_half_width", "raw_p", "holm_p",
          "sec_h1_bps", "sec_h6_bps", "n_events", "n_bull", "n_bear", "n_instruments", "verdict")}}
        for d in DOMAINS])
    write_rows(RESULTS_DIR / "parity_comparison.csv", parity_rows)
    write_rows(RESULTS_DIR / "event_diagnostics.csv", [
        {"domain": d, "n_events": primary.filter(pl.col("domain") == d).height,
         "n_bull": primary.filter((pl.col("domain") == d) & (pl.col("direction") == 1)).height,
         "n_bear": primary.filter((pl.col("domain") == d) & (pl.col("direction") == -1)).height,
         "n_pyramid": primary.filter((pl.col("domain") == d) & pl.col("is_pyramid_bounce")).height,
         "n_nonpyramid": primary.filter((pl.col("domain") == d) & ~pl.col("is_pyramid_bounce")).height,
         "fixedh_h1_bps": fixedh.get(d, {}).get(SEC_LOW_HORIZON),
         "fixedh_h3_bps": fixedh.get(d, {}).get(3),
         "fixedh_h6_bps": fixedh.get(d, {}).get(SEC_HIGH_HORIZON)}
        for d in DOMAINS])
    write_rows(RESULTS_DIR / "exit_parity.csv", exitparity)
    write_rows(RESULTS_DIR / "signal_reconciliation.csv", signalrecon)
    write_rows(RESULTS_DIR / "equity_companion.csv", [{"domain": d, **equity[d]} for d in DOMAINS])
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(metadata, indent=2, default=str))

    plot_effect_forest(primary_res, ref, PLOTS_DIR / "effect_forest.png")
    plot_count_diagnostic(primary, ref, diag, PLOTS_DIR / "event_count_diagnostic.png")
    plot_parity_table(parity_rows, overall, signal_5m_ok, PLOTS_DIR / "parity_alignment_table.png")
    LOGGER.info("Wrote results to %s and plots to %s", RESULTS_DIR, PLOTS_DIR)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    configure_logging()
    LOGGER.info("=" * 70)
    LOGGER.info("EXP-029: cTrader Per-Bar Streaming Parity for Faithful AVWAP Strategy")
    LOGGER.info("=" * 70)
    ensure_output_dirs()

    # Step 0 — integrity guards (D3) + frozen-method identity vs EXP-028 (F05).
    frozen_hash = verify_frozen_inference()
    exp028_meta = load_json(EXP028_RESULTS / "run_metadata.json")
    exp028_hash = str(exp028_meta.get("frozen_inference_hash", ""))
    if frozen_hash != EXP028_FROZEN_HASH or frozen_hash != exp028_hash:
        raise ValueError(
            "FROZEN_INFERENCE_MISMATCH (F05): the inference tail must be byte-identical to "
            f"the one EXP-028 used. local={frozen_hash} predeclared={EXP028_FROZEN_HASH} "
            f"exp028_recorded={exp028_hash}. A CONSISTENT parity result is only meaningful "
            "if both runs use the same calibrated EXP-027 method — hard abort."
        )
    cm_pass = verify_control_matching()
    deps = check_dependencies()
    ref = load_exp028_reference()
    ref_pyramid = load_ref_pyramid()

    # Step 1/2 — locate corrected cTrader runs and build cTrader-feed frames (D1, D5).
    run_index = discover_corrected_runs()
    missing = [f"{i}/{d}" for i in INSTRUMENTS for d in DOMAINS if (i, d) not in run_index]
    if missing:
        raise FileNotFoundError(
            "Missing corrected EXP-029 cTrader runs (with avwap_events.parquet) for cells: "
            f"{missing}. Run tools/ctrader-cli/run-exp029-backtests.sh first (the corrected "
            "pyramid-inclusive AvwapBounceModel). The EXP-023 avwap_baseline_* runs are NOT "
            "reusable (pyramid-suppressed, no event-detail table)."
        )

    frames: dict[tuple[str, str], dict[str, Any]] = {}
    lifetime_rows: list[dict[str, Any]] = []
    fh_rows: list[dict[str, Any]] = []
    event_detail_5m_frames: list[pl.DataFrame] = []  # for the F03 signal-layer reconciliation
    analysis_end_seen: dict[str, str] = {}
    cell_counts: dict[str, Any] = {}
    for (inst, domain), run_dir in tqdm(sorted(run_index.items()), desc="cTrader cells"):
        frame = load_cell_frame(run_dir, inst)
        frames[(inst, domain)] = frame
        analysis_end_seen[inst] = ANALYSIS_END[inst]
        cell_counts[f"{inst}/{domain}"] = {"n_bars": frame["n"],
                                           "max_source_close_time": str(frame["max_source_close_time"])}
        events_cell = load_event_detail(run_dir, inst, domain, frame)  # Step 3 (D4, D6)
        if domain == "5m":
            event_detail_5m_frames.append(events_cell.select(
                "instrument", "domain", "trigger_time",
                "favorable_target_at_trigger", "adverse_target_at_trigger"))
        regimes_cell = build_regimes_cell(frame, events_cell)
        lr, fr, _ = build_cell_lifetimes(inst, domain, events_cell, regimes_cell, frame)  # Step 4 (D2)
        lifetime_rows.extend(lr)
        fh_rows.extend(fr)

    lifetime = pl.DataFrame(lifetime_rows)
    fh = pl.DataFrame(fh_rows) if fh_rows else pl.DataFrame(
        schema={"instrument": pl.Utf8, "domain": pl.Utf8, "horizon": pl.Int64,
                "direction": pl.Int64, "paired_diff_bps": pl.Float64, "reportable": pl.Boolean})

    # Step 4 aggregation + Step 5 inference (D2, frozen tail).
    primary, diag = build_primary_excess(lifetime, frames)
    fixedh = fixed_horizon_effects(fh)
    primary_res = run_primary(primary, fixedh)

    # Step 4b — grade the corrected C# completion code per event (F01/F06).
    exitparity_rows, exit_parity_ok = build_exit_parity(lifetime)

    # Step 3b — 5m signal-layer reconciliation vs the EXP-020 substrate (F03).
    event_detail_5m = (pl.concat(event_detail_5m_frames, how="vertical_relaxed")
                       if event_detail_5m_frames else pl.DataFrame())
    signalrecon_rows, signal_5m_ok = reconcile_signal_layer(event_detail_5m)

    # Step 6 — parity vs EXP-028 (binding gates: magnitude F02, pyramid F04,
    # exit-parity F01, signal-layer F03).
    ref_pyr_total = exp028_meta.get("pyramid_split")
    diag["ref_pyramid_split"] = ref_pyr_total
    parity_rows, overall = compare_parity(primary_res, primary, ref, ref_pyramid,
                                          exit_parity_ok, signal_5m_ok)

    # Step 7 — diagnostics (non-binding).
    equity = equity_companion(primary)

    consequence = {
        "CONSISTENT": "EXP-028 EVAL_SUPPORTED upgraded to cTrader-confirmed.",
        "INCONCLUSIVE": "EXP-028 Python-only verdict stands as-is (discrepancy documented).",
        "INCONSISTENT": "EXP-028 downgraded to EVAL_UNCONFIRMED pending root-cause.",
    }[overall]

    metadata = {
        "experiment": EXPERIMENT_ID,
        "title": "cTrader Per-Bar Streaming Parity for Faithful AVWAP Strategy",
        "overall_parity_disposition": overall,
        "per_domain_band": {r["domain"]: r["band"] for r in parity_rows},
        "exp028_status_consequence": consequence,
        "binding_estimand": "PRIMARY_symmetric_own_exit_lifetime_excess (same as EXP-028)",
        "returns_basis": "cTrader RealClose (own feed)",
        "frozen_inference_hash": frozen_hash,
        "frozen_inference_hash_matches_exp028": True,  # hard-asserted in main (F05)
        "control_matching_equivalence_pass": bool(cm_pass),
        "dependencies": deps,
        "exp029_primary_per_domain": {d: primary_res[d].get("verdict") for d in DOMAINS},
        "exp028_primary_per_domain": {d: ref.get(d, {}).get("verdict") for d in DOMAINS},
        "reconciliation_bad": diag["reconciliation_bad"],
        # F01 exit-parity: did the corrected C# completion code reproduce the Python scan?
        "exit_parity_ok_per_domain": exit_parity_ok,
        "exit_parity_match_rate": {row["domain"]: row["match_rate"] for row in exitparity_rows},
        # F03 signal-layer: does the C# 5m event set reproduce the EXP-020 substrate?
        "signal_layer_5m_ok": signal_5m_ok,
        "pyramids_included": True,
        "pyramid_split": {"pyramid": diag["n_pyramid"], "non_pyramid": diag["n_nonpyramid"]},
        "exp028_pyramid_split": ref_pyr_total,
        "exp028_pyramid_per_domain": ref_pyramid,  # F04 per-domain pyramid count gate
        "analysis_end_per_instrument": analysis_end_seen,
        "cell_counts": cell_counts,
        "run_directories": {f"{i}/{d}": str(p) for (i, d), p in sorted(run_index.items())},
        "parameters": {"domains": list(DOMAINS), "instruments": list(INSTRUMENTS),
                       "alpha": ALPHA, "n_boot": N_BOOT, "n_perm": N_PERM,
                       "horizons": list(HORIZONS), "min_reportable_events": MIN_REPORTABLE_EVENTS,
                       "min_direction_events": MIN_DIRECTION_EVENTS,
                       "count_tol_consistent": COUNT_TOL_CONSISTENT,
                       "count_tol_inconclusive": COUNT_TOL_INCONCLUSIVE,
                       "disposition_min_domains": DISPOSITION_MIN_DOMAINS},
        # Predeclared agreement margins / gates (F01/F02/F03; D8 no goalpost-moving).
        "agreement_margins": {
            "effect_equiv_abs_bps": EFFECT_EQUIV_ABS_BPS, "effect_equiv_rel": EFFECT_EQUIV_REL,
            "effect_divergent_rel": EFFECT_DIVERGENT_REL, "exit_parity_min": EXIT_PARITY_MIN,
            "exit_parity_bps_tol": EXIT_PARITY_BPS_TOL, "signal_match_min": SIGNAL_MATCH_MIN,
            "signal_target_rel": SIGNAL_TARGET_REL},
        "seeds": {"convention": "seed_for(EXPERIMENT_ID, role, domain)"},
        "_ref": ref,
    }
    save_outputs(primary_res, primary, parity_rows, overall, equity, exitparity_rows,
                 signalrecon_rows, signal_5m_ok, fixedh, diag, metadata)

    LOGGER.info("=" * 70)
    LOGGER.info("Parity disposition: %s  (signal-layer 5m ok=%s)", overall, signal_5m_ok)
    for r in parity_rows:
        LOGGER.info("  %s band=%s | EXP-029=%s eff=%s CI=[%s,%s] | EXP-028=%s | exit_parity=%s",
                    r["domain"], r["band"], r["exp029_verdict"], r["exp029_effect_bps"],
                    r["exp029_ci_low"], r["exp029_ci_high"], r["exp028_verdict"], r["exit_parity_ok"])
    LOGGER.info("Consequence: %s", consequence)
    LOGGER.info("=" * 70)


if __name__ == "__main__":
    main()
