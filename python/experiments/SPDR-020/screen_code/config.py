"""SPDR-020 frozen constants — every value traces to design.md.

Phase (a) only. No L5. TRAIN only. Gross only. Mirror null.
Parent object: SPDR-014. L4 M1 exits: SPDR-019 fills module (imported, not reimplemented).
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------- paths ----

EXP_DIR = Path(__file__).resolve().parents[1]
SCREEN_CODE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"


def _repo_root() -> Path:
    p = Path(__file__).resolve()
    for parent in p.parents:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("repo root not found")


REPO_ROOT = _repo_root()
EXPERIMENTS_DIR = REPO_ROOT / "python" / "experiments"
CATALOG_BAR_DIR = REPO_ROOT / "data" / "catalog" / "data" / "bar"
BAR_TYPE_SUFFIX = "-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL"

UNIVERSE_PIN_FAMILY = (
    REPO_ROOT / "docs" / "signal-registry" / "candidate-families" / "cf-voldir-001-universe.json"
)
UNIVERSE_PIN_PREDECL = EXPERIMENTS_DIR / "SPDR-014" / "results" / "universe_recomputed.json"

PARENT_014_RESULTS = EXPERIMENTS_DIR / "SPDR-014" / "results"
PARENT_014_CODE = EXPERIMENTS_DIR / "SPDR-014" / "screen_code"
PARENT_015_RESULTS = EXPERIMENTS_DIR / "SPDR-015" / "results"
PARENT_015_CODE = EXPERIMENTS_DIR / "SPDR-015" / "screen_code"
PARENT_019_CODE = EXPERIMENTS_DIR / "SPDR-019" / "screen_code"
ZVOL_SCALE_PATH = PARENT_014_RESULTS / "zvol_scale.json"

# --------------------------------------------------------------- bands ----

DESIGN_START = datetime(2021, 6, 29, 6, 53, tzinfo=timezone.utc)
DESIGN_END = datetime(2023, 3, 1, tzinfo=timezone.utc)  # exclusive
CONFIRM_START = DESIGN_END
CONFIRM_END = datetime(2023, 12, 18, tzinfo=timezone.utc)  # exclusive == train_end
TRAIN_END = CONFIRM_END
HOLDOUT_START = datetime(2025, 1, 8, tzinfo=timezone.utc)

NS = 1_000_000_000
DAY_NS = 86_400 * NS

TRAIN_END_NS = int(TRAIN_END.timestamp() * NS)
HOLDOUT_START_NS = int(HOLDOUT_START.timestamp() * NS)
DESIGN_START_NS = int(DESIGN_START.timestamp() * NS)
DESIGN_END_NS = int(DESIGN_END.timestamp() * NS)
CONFIRM_END_NS = int(CONFIRM_END.timestamp() * NS)

BANDS = {
    "DESIGN": (DESIGN_START, DESIGN_END),
    "CONFIRM": (CONFIRM_START, CONFIRM_END),
    "TRAIN": (DESIGN_START, CONFIRM_END),
}

EFFECTIVE_COVERAGE_MULTI_SYMBOL_START = datetime(2022, 7, 14, tzinfo=timezone.utc)
EFFECTIVE_COVERAGE_START_NS = int(EFFECTIVE_COVERAGE_MULTI_SYMBOL_START.timestamp() * NS)

# ------------------------------------------------------------ universe ----

UNIVERSE_N = 25
UNIVERSE_METRIC = "sum(close*volume) over 1m bars"
UNIVERSE_WINDOW_START = datetime(2023, 11, 18, tzinfo=timezone.utc)
UNIVERSE_WINDOW_END = datetime(2023, 12, 18, tzinfo=timezone.utc)

# Z-VOL coverage: 8 symbols lack s_symbol (design §7 / §10)
ZVOL_NAN_SYMBOLS = frozenset({
    "ORDIUSDT", "TIAUSDT", "BIGTIMEUSDT", "1000PEPEUSDT",
    "SEIUSDT", "WLDUSDT", "PYTHUSDT", "1000RATSUSDT",
})
ZVOL_COVERED_N = 17


def universe_symbols() -> tuple[str, ...]:
    """Return the frozen universe pin in its declared order."""
    import json

    payload = json.loads(UNIVERSE_PIN_FAMILY.read_text())
    return tuple(payload["symbols"])

# --------------------------------------------------------------- clocks ----

CLOCKS: dict[str, dict] = {
    "H1": {"minutes": 60, "truncate": "1h", "min_minutes": 48, "warmup_bars": 60},
    "H4": {"minutes": 240, "truncate": "4h", "min_minutes": 192, "warmup_bars": 60},
}
CLOCKS_RUN = ("H1", "H4")
PRIMARY_CLOCK = "H1"

# ----------------------------------------------------------- event grammar ----
# SPDR-014 inherited (design §2)

EWMA_LAMBDA = 0.94
ZVOL_WARMUP_BARS = 60
ZVOL_EPS = 1e-12
Z_VALUES = (1.5, 2.0, 2.5, 3.0)
H_VALUES = (4, 12, 24)
H_PRIMARY = 12
H_POST = (4, 12, 24)
SOURCES = ("Z-VOL", "Z-MAG", "Z-MAG-SENS")
SOURCE_PRIMARY = "Z-VOL"
EVENT_TYPES = ("E-TOUCH", "E-CLOSE", "E-HORIZON")
POLICIES = ("P-MOMO", "P-MR")

ATR_PERIOD = 14
ZZ_REVERSAL_ATR = 2.0
RIDGE_ALPHA = 1.0
ZZ_MIN_TRAIN_SWINGS = 20
ZMAG_FLOOR_BPS = 1.0
ZMAG_SENSITIVITY_DIV = 2.0

DEADBAND_BPS = 5.0  # SPDR-014 flat deadband, verbatim
PARITY_TOL = 1e-9
PARITY_SLICE = {
    "z": 1.5, "H": 12, "h": 12, "event": "E-TOUCH", "source": "Z-VOL", "band": "DESIGN",
}

# ------------------------------------------------------------- L4 grid ----
# design §4 — holds in parent's frozen h bars; target/trail as SPDR-019

L4_TARGET_A = (1, 2, 3)
L4_TRAIL_B = (1, 2)
L4_HOLD_BARS = (4, 12, 24)
SIZE_CLIP = (0.25, 4.0)
MOD_HOLD_MIN_PRIOR_TRANS = 30
E_RUN_CLIP = (1.0, 48.0)
H_MOD_CLIP_BARS = (1.0, 48.0)
H_MOD_DIVISOR = 20.0

# L1 central pairs (reused L4 rows; no extra physical rows)
L1_CENTRAL = frozenset({
    "L4_TARGET_A2_UNMOD", "L4_TARGET_A2_MOD",
    "L4_TRAIL_B1_UNMOD", "L4_TRAIL_B1_MOD",
    "L4_HOLD_12_UNMOD", "L4_HOLD_12_MOD",
})

# ------------------------------------------------------------- variants ----
# phase (a): L0 + L2 + L3 + L4. No L5.

VARIANT_IDS: tuple[str, ...] = (
    "L0_BASELINE",
    "L2_SHOCK_HMM",
    "L2_LEVEL_RMARKOV_K4",
    "L2_LEVEL_RMARKOV_K12",
    "L2_JOINT_HMM_HIGH_AND_K12_HIGH",
    "L2_INTERACTION_HMM_X_K12",
    "L3_TGTCUR_FIRES",
    "L3_TGTCUR_DOES_NOT_FIRE",
    "L4_TARGET_A1_UNMOD",
    "L4_TARGET_A1_MOD",
    "L4_TARGET_A2_UNMOD",
    "L4_TARGET_A2_MOD",
    "L4_TARGET_A3_UNMOD",
    "L4_TARGET_A3_MOD",
    "L4_TRAIL_B1_UNMOD",
    "L4_TRAIL_B1_MOD",
    "L4_TRAIL_B2_UNMOD",
    "L4_TRAIL_B2_MOD",
    "L4_HOLD_4_UNMOD",
    "L4_HOLD_4_MOD",
    "L4_HOLD_12_UNMOD",
    "L4_HOLD_12_MOD",
    "L4_HOLD_24_UNMOD",
    "L4_HOLD_24_MOD",
    "L4_SIZE_UNMOD",
    "L4_SIZE_MOD",
)

DERIVED_VARIANTS = frozenset({"L2_INTERACTION_HMM_X_K12"})
SIZING_VARIANTS = frozenset({"L4_SIZE_UNMOD", "L4_SIZE_MOD"})
TIME_EXIT_VARIANTS = frozenset({
    "L0_BASELINE",
    "L2_SHOCK_HMM", "L2_LEVEL_RMARKOV_K4", "L2_LEVEL_RMARKOV_K12",
    "L2_JOINT_HMM_HIGH_AND_K12_HIGH",
    "L3_TGTCUR_FIRES", "L3_TGTCUR_DOES_NOT_FIRE",
    "L4_HOLD_4_UNMOD", "L4_HOLD_4_MOD",
    "L4_HOLD_12_UNMOD", "L4_HOLD_12_MOD",
    "L4_HOLD_24_UNMOD", "L4_HOLD_24_MOD",
    "L4_SIZE_UNMOD", "L4_SIZE_MOD",
})

PARITY_EXEMPT_SYMBOLS = ZVOL_NAN_SYMBOLS

# --------------------------------------------------------------- costs ----

FEE_RT_BPS = 11.0
FUNDING_BPS_PER_STAMP = 1.0
ALLOWANCE_GOVERNING = 2.0
COST_FLOOR_BPS = 14.6  # mid of 13.1–16.1 partial; disclosure only
SPREAD_BPS_PROHIBITED = True

SPREAD_COST_DISCLOSURE = {
    "spread_cost_status": "UNAVAILABLE_NOT_CHARGED",
    "spread_rt_bps": None,
    "cost_scope": "PARTIAL_FEES_FUNDING_ONLY",
    "implication": (
        "reported cost understates total cost; reported net performance is overstated"
    ),
    "prohibited_claims": ["fully-net", "cost-complete", "tradable", "deployable"],
    "note_amendment_c5": (
        "cost enters NO estimand, threshold or comparison; p_be_net is DISCLOSED REFERENCE only"
    ),
}
PROHIBITED_CLAIMS = list(SPREAD_COST_DISCLOSURE["prohibited_claims"])

# --------------------------------------------------------- inference ----
# H1: SPDR-018 §6.2 verbatim. H4: {4,12,28}-day co-report (design §8.1).

BOOT_BLOCKS_DAYS_H1 = (1, 3, 7)
BOOT_BLOCKS_DAYS_H4 = (4, 12, 28)
BOOT_SEEDS = (101, 211, 307, 401, 503)
BOOT_RESAMPLES = 2_000
BOOT_CI_ALPHA = 0.05
IID_MDE_CONST = 2.8
MDE_SOURCE_FOR_BANDS = "block"
IDENTITY_RECONSTRUCTION_TOL_BPS = 0.01

LADDER_RUNGS = (0.02, 0.03, 0.05, 0.075, 0.10, 0.15)
LADDER_PLANT_N = BOOT_RESAMPLES

# --------------------------------------------------------- controls ----

DERANGE_SEEDS = tuple(range(31000, 33000))
TIMING_SEEDS = tuple(range(41000, 43000))
MAGMATCH_SEEDS = tuple(range(71000, 73000))
PLANT_CURVE_BPS = (5.0, 10.0, 20.0, 40.0)
PLANT_CURVE_SIGMA = (0.068, 0.137, 0.274, 0.548)

CONTROL_PRIMARY = {
    "clock": "H1",
    "source": "Z-VOL",
    "z": 1.5,
    "H": 12,
    "h": 12,
    "event_type": "E-TOUCH",
    "policy": "P-MOMO",
    "variant_id": "L0_BASELINE",
    "band": "TRAIN",
    "scope": "POOLED",
}


def execution_manifest() -> dict:
    """Exact execution-grade plan; developer subsets never satisfy it."""
    return {
        "smoke": False,
        "subset": False,
        "primary_only": False,
        "symbols": list(universe_symbols()),
        "clocks": list(CLOCKS_RUN),
        "sources": list(SOURCES),
        "H": list(H_VALUES),
        "z": list(Z_VALUES),
        "h": list(H_POST),
        "event_types": list(EVENT_TYPES),
        "variants": list(VARIANT_IDS),
        "n_boot": BOOT_RESAMPLES,
        "expected_primary_cells": 1584,
        "expected_full_cells": 28512,
    }

# ------------------------------------------------ predeclaration pins ----
# design: consume, never regenerate

RESOLUTION_BASIS_SHA256 = (
    "23d5f5bf1eb16d00f42d07f67865416955c66a73ff3497ca85d96f68287703c9"
)
EXPECTED_RESOLUTION_SHA256 = (
    "f174eaf655be0ef7bcf376618d1d82ff49bed2b49cc1cca1f6ab9e4f95b19341"
)
EXPECTED_RESOLUTION_ROW_COUNT = 1296

# §12 HARD checks — expected count 29, reconciled by name
HARD_CHECK_NAMES: tuple[str, ...] = (
    "check-count reconciliation",
    "TRIPWIRE-1",
    "TRIPWIRE-2",
    "TRAIN fence",
    "holdout",
    "causality",
    "breach detection",
    "EXIT FILL CAUSALITY",
    "parent parity",
    "universe pin",
    "identity reconstruction",
    "log R definition",
    "cost isolation",
    "MDE column",
    "BLOCK RULE",
    "s_symbol PROVENANCE",
    "UNDECIDED accounting",
    "M-4 effective coverage",
    "p_event NON-APPLICATION",
    "NO ADEQUACY FLAG",
    "LADDER EMITTED",
    "LADDER PLANT OPERATOR",
    "L-51 SELECTION CHECK",
    "log R never unaccompanied",
    "PREDECLARED vs REALISED resolution",
    "NO LOCAL ACCOUNTING",
    "derangement fixed-point count",
    "golden traces",
    "determinism",
)
EXPECTED_HARD_CHECK_COUNT = 29
assert len(HARD_CHECK_NAMES) == EXPECTED_HARD_CHECK_COUNT

BLOCK_RULE_CLAUSES_H1 = (
    "per-calendar-day sufficient statistics",
    "day-blocks of {1, 3, 7}",
    "minimum block = 1 day = 24 H1 bars",
    "min/max envelope over blocks x seeds",
    "xen.evaluation.block_bootstrap_ci",
    "effective block capped < n",
)
BLOCK_RULE_CLAUSES_H4 = (
    "day-blocks of {4, 12, 28}",
    "horizon-scaled",
)

DEVIATIONS: list[str] = []
