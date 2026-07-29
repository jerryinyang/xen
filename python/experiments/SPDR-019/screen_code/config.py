"""SPDR-019 frozen constants — every value traces to design.md.

Phase (a) only: 33 named variants of §4.1a. TRAIN-only. Gross-only. No L5, no phase (b).
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

PARENT_015_RESULTS = EXPERIMENTS_DIR / "SPDR-015" / "results"
PARENT_015_CODE = EXPERIMENTS_DIR / "SPDR-015" / "screen_code"
PARENT_014_CODE = EXPERIMENTS_DIR / "SPDR-014" / "screen_code"

# --------------------------------------------------------------- bands ----
# design §10

DESIGN_START = datetime(2021, 6, 29, 6, 53, tzinfo=timezone.utc)
DESIGN_END = datetime(2023, 3, 1, tzinfo=timezone.utc)  # exclusive
CONFIRM_START = DESIGN_END
CONFIRM_END = datetime(2023, 12, 18, tzinfo=timezone.utc)  # exclusive == train_end
TRAIN_END = CONFIRM_END
TEST_START = CONFIRM_END  # never read
HOLDOUT_START = datetime(2025, 1, 8, tzinfo=timezone.utc)  # never read

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

# M-4 catalog history cap
EFFECTIVE_COVERAGE_MULTI_SYMBOL_START = datetime(2022, 7, 14, tzinfo=timezone.utc)
EFFECTIVE_COVERAGE_START_NS = int(EFFECTIVE_COVERAGE_MULTI_SYMBOL_START.timestamp() * NS)

# ------------------------------------------------------------ universe ----

UNIVERSE_N = 25
UNIVERSE_METRIC = "sum(close*volume) over 1m bars"
UNIVERSE_WINDOW_START = datetime(2023, 11, 18, tzinfo=timezone.utc)
UNIVERSE_WINDOW_END = datetime(2023, 12, 18, tzinfo=timezone.utc)

# --------------------------------------------------------------- clocks ----
# design §10: M15 primary capture clock; H1 co-report. s_hat always H1.

CLOCKS = {
    "M15": {"minutes": 15, "min_minutes": 12},
    "H1": {"minutes": 60, "min_minutes": 48},
}
CLOCKS_RUN = ("M15", "H1")
SHAT_CLOCK = "H1"

# ------------------------------------------------------------- entry ----
# design §2

DELTA_THRESHOLDS = (0.25, 0.5, 1.0)
L0_ACTIVE_HOLD_HOURS = 1.0
L0_INACTIVE_HOLD_HOURS = 2.0
ATR_PERIOD = 20
ATR_WARMUP = 20

# ------------------------------------------------------------- unit pin ----
# design §7 — IDENTICAL to SPDR-014 Z-VOL width

EWMA_LAMBDA = 0.94
SIGMA_WARMUP_BARS = 60
ZVOL_EPS = 1e-12
DECILE_WARMUP_SHAT = 250  # §4.1b L1 eligibility

# ------------------------------------------------------------- L4 grid ----
# design §4.2

L4_TARGET_A = (1, 2, 3)
L4_TRAIL_B = (1, 2)
L4_HOLD_HOURS = (1, 4, 12, 20)
SIZE_CLIP = (0.25, 4.0)
MOD_HOLD_MIN_PRIOR_TRANS = 30
E_RUN_CLIP = (1.0, 48.0)
H_MOD_CLIP = (1.0, 20.0)
H_MOD_DIVISOR = 20.0

# ------------------------------------------------------------- variants ----
# design §4.1a — 33 named identities. L5 excluded.

VARIANT_IDS: tuple[str, ...] = (
    "L0_BASELINE",
    "L1_SHAT_DECILE_GE5",
    "L1_SHAT_DECILE_GE7",
    "L1_SHAT_DECILE_GE9",
    "L1_SHAT_RANK_CONTINUOUS",
    "L2_SHOCK_HMM",
    "L2_LEVEL_RMARKOV_K4",
    "L2_LEVEL_RMARKOV_K12",
    "L2_JOINT_HMM_HIGH_AND_K12_HIGH",
    "L2_INTERACTION_HMM_X_K12",
    "L3_TGTCUR_FIRES",
    "L3_TGTCUR_DOES_NOT_FIRE",
    "L3_TGTMED5_CO_REPORT",
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
    "L4_HOLD_1H_UNMOD",
    "L4_HOLD_1H_MOD",
    "L4_HOLD_4H_UNMOD",
    "L4_HOLD_4H_MOD",
    "L4_HOLD_12H_UNMOD",
    "L4_HOLD_12H_MOD",
    "L4_HOLD_20H_UNMOD",
    "L4_HOLD_20H_MOD",
    "L4_SIZE_UNMOD",
    "L4_SIZE_MOD",
)
assert len(VARIANT_IDS) == 33

TIME_EXIT_VARIANTS = frozenset({
    "L0_BASELINE",
    "L1_SHAT_DECILE_GE5", "L1_SHAT_DECILE_GE7", "L1_SHAT_DECILE_GE9",
    "L1_SHAT_RANK_CONTINUOUS",
    "L2_SHOCK_HMM", "L2_LEVEL_RMARKOV_K4", "L2_LEVEL_RMARKOV_K12",
    "L2_JOINT_HMM_HIGH_AND_K12_HIGH",
    "L3_TGTCUR_FIRES", "L3_TGTCUR_DOES_NOT_FIRE", "L3_TGTMED5_CO_REPORT",
    "L4_HOLD_1H_UNMOD", "L4_HOLD_1H_MOD",
    "L4_HOLD_4H_UNMOD", "L4_HOLD_4H_MOD",
    "L4_HOLD_12H_UNMOD", "L4_HOLD_12H_MOD",
    "L4_HOLD_20H_UNMOD", "L4_HOLD_20H_MOD",
    "L4_SIZE_UNMOD", "L4_SIZE_MOD",
})

# interaction row has no episode population of its own
DERIVED_VARIANTS = frozenset({"L2_INTERACTION_HMM_X_K12"})

# sizing may not carry a log R claim (SoT §4.4)
SIZING_VARIANTS = frozenset({"L4_SIZE_UNMOD", "L4_SIZE_MOD"})

# R-MARKOV parity-exempt symbols (design §4.1a)
PARITY_EXEMPT_SYMBOLS = frozenset({
    "1000PEPEUSDT", "1000RATSUSDT", "BIGTIMEUSDT", "ORDIUSDT",
    "PYTHUSDT", "SEIUSDT", "TIAUSDT", "WLDUSDT",
})

# --------------------------------------------------------------- costs ----
# AMENDMENT-C5: disclosure only. Never in estimand/threshold/band.

FEE_RT_BPS = 11.0
FUNDING_BPS_PER_STAMP = 1.0
ALLOWANCE_GOVERNING = 2.0
COST_FLOOR_BPS = 13.5  # partial; spread NOT charged
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
# design §8.1 — inherited SPDR-018 §6.2 verbatim

BOOT_BLOCKS_DAYS = (1, 3, 7)
BOOT_SEEDS = (101, 211, 307, 401, 503)
BOOT_RESAMPLES = 2_000
BOOT_CI_ALPHA = 0.05
IID_MDE_CONST = 2.8
MDE_SOURCE_FOR_BANDS = "block"
IDENTITY_RECONSTRUCTION_TOL_BPS = 0.01

LADDER_RUNGS = (0.02, 0.03, 0.05, 0.075, 0.10, 0.15)
LADDER_PLANT_N = 200  # detection rate samples per rung (descriptive)

# --------------------------------------------------------- controls ----

DERANGE_SEEDS = tuple(range(31000, 33000))  # 2000 side-derangement
TIMING_SEEDS = tuple(range(41000, 43000))   # 2000 entry-timing
MAGMATCH_SEEDS = tuple(range(71000, 73000))  # 2000 magnitude-matched
# control battery is PINNED at 2000, independent of --n-boot (R9-05 / design §6)
CONTROL_N_SEEDS = 2000
assert len(DERANGE_SEEDS) >= CONTROL_N_SEEDS
assert len(TIMING_SEEDS) >= CONTROL_N_SEEDS
assert len(MAGMATCH_SEEDS) >= CONTROL_N_SEEDS
# golden-trace / tripwire anchor — never selected by whether a HARD clause already holds (R9-10)
TRIPWIRE_SYMBOL = "BTCUSDT"
PLANT_CURVE_BPS = (5.0, 10.0, 20.0, 40.0)
PLANT_CURVE_SIGMA = (0.068, 0.137, 0.274, 0.548)  # at pooled sigma-hat=73 bps; re-derived at run
MAGMATCH_DECILES = 10

# primary control cells (disclosure grid gets collapse from these where shared)
CONTROL_PRIMARY = {
    "clock": "H1",
    "delta": 0.5,
    "variant_id": "L0_BASELINE",
    "band": "TRAIN",
    "scope": "POOLED",
}

# ------------------------------------------------ predeclaration pins ----
# design non-negotiable: consume, never regenerate

RESOLUTION_BASIS_SHA256 = (
    "23d5f5bf1eb16d00f42d07f67865416955c66a73ff3497ca85d96f68287703c9"
)
EXPECTED_RESOLUTION_SHA256 = (
    "e3247798edc9ab90389b2eb42c138a2f9961e3fcb6a117ac2908db21dafa3502"
)
RESOLUTION_BASIS_GENERATOR_SHA256 = (
    "72c6b1f953cae24cd6886099576a605acbc6be7074e25e0c1a251ccaaa6e2e5c"
)

# §12 HARD checks — expected count 28, reconciled by name
HARD_CHECK_NAMES: tuple[str, ...] = (
    "check-count reconciliation",
    "TRIPWIRE-1",
    "TRIPWIRE-2",
    "TRAIN fence",
    "holdout",
    "causality",
    "fill causality",
    "universe pin",
    "identity reconstruction",
    "log R definition",
    "cost isolation",
    "derangement fixed-point count",
    "golden traces",
    "determinism",
    "BLOCK RULE",
    "L4 COMPARATOR IDENTITY",
    "PARENT-GATE PROVENANCE",
    "PARENT-GATE PARITY",
    "DECILE CAUSALITY",
    "EXIT-MATCHED NULLS",
    "L1 FIXED-ENTRY SUBSET",
    "MOD-HOLD ELIGIBILITY",
    "PREDECLARATION PRESENT",
    "BASIS POPULATION",
    "UNIVERSE FILE EQUALITY",
    "L-51 SELECTION CHECK",
    "log R never unaccompanied",
    "PREDECLARED vs REALISED resolution",
)
EXPECTED_HARD_CHECK_COUNT = 28
assert len(HARD_CHECK_NAMES) == EXPECTED_HARD_CHECK_COUNT

# source_ci_rule clauses (§8.1) — checked clause-by-clause, not string equality
BLOCK_RULE_CLAUSES = (
    "per-calendar-day sufficient statistics",
    "day-blocks of {1, 3, 7}",
    "minimum block = 1 day = 24 H1 bars",
    "min/max envelope over blocks x seeds",
    "xen.evaluation.block_bootstrap_ci",
    "effective block capped < n",
)

# DEVIATIONS: none authorised at implementation start
DEVIATIONS: list[str] = []
