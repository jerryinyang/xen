"""SPDR-018 frozen constants — every value traces to design.md / SoT `opportunity.md`.

Powering sweep over the complete checkpoint-017 residue (CF-VOLDIR-001 / HYP-D5).
TRAIN-only SPDR screen. Four arms, each inheriting its parent screen's mechanism, object and
estimand VERBATIM (design §1). Nothing here re-specifies a parent object.

DEVIATIONS: see ``DEVIATIONS`` at the bottom of this module (raised before implementation).
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

# Bybit (primary, powered estimate)
CATALOG_BAR_DIR = REPO_ROOT / "data" / "catalog" / "data" / "bar"
BAR_TYPE_SUFFIX = "-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL"
UNIVERSE_PIN_FAMILY = (
    REPO_ROOT / "docs" / "signal-registry" / "candidate-families" / "cf-voldir-001-universe.json"
)

# cTrader (replication ONLY — never pooled; AMENDMENT-C1 / design §10)
CTRADER_BAR_DIR = REPO_ROOT / "data" / "catalog_ctrader" / "data" / "bar"
CTRADER_BAR_TYPE_SUFFIX = ".CTrader-1-MINUTE-LAST-EXTERNAL"
CTRADER_FENCE_PATH = (
    REPO_ROOT / "python" / "experiments" / "INFR-021" / "artifacts" / "fence-manifest.json"
)
CTRADER_FENCE_SHA256 = "4cdc7b01dd47200710d0d961639d55d52e1129ca89096e841eafd816b6061de0"
CTRADER_SYMBOLS = ("EURUSD", "XAUUSD", "USTEC")
CTRADER_TRAIN_END = datetime(2023, 11, 22, tzinfo=timezone.utc)     # exclusive
CTRADER_HOLDOUT_START = datetime(2024, 12, 13, tzinfo=timezone.utc)  # never queried

PARENTS = ("SPDR-012", "SPDR-013", "SPDR-014", "SPDR-015")

# --------------------------------------------------------------- bands ----
# design §10 — identical to 012/013/014/015. Both bands scored explicitly (D8, lever 3).

DESIGN_START = datetime(2021, 6, 29, 6, 53, tzinfo=timezone.utc)
DESIGN_END = datetime(2023, 3, 1, tzinfo=timezone.utc)        # exclusive
CONFIRM_START = DESIGN_END
CONFIRM_END = datetime(2023, 12, 18, tzinfo=timezone.utc)     # exclusive == train_end_utc
TRAIN_END = CONFIRM_END
TEST_START = CONFIRM_END                                      # never read
HOLDOUT_START = datetime(2025, 1, 8, tzinfo=timezone.utc)     # never read

BANDS = {
    "DESIGN": (DESIGN_START, DESIGN_END),
    "CONFIRM": (CONFIRM_START, CONFIRM_END),
    "TRAIN": (DESIGN_START, CONFIRM_END),   # power lever 2 — the full-span pooled band
}
NS = 1_000_000_000

TRAIN_END_NS = int(TRAIN_END.timestamp() * NS)
HOLDOUT_START_NS = int(HOLDOUT_START.timestamp() * NS)
CTRADER_TRAIN_END_NS = int(CTRADER_TRAIN_END.timestamp() * NS)
CTRADER_HOLDOUT_START_NS = int(CTRADER_HOLDOUT_START.timestamp() * NS)

# M-4: the DESIGN band is one symbol deep before this date (catalog history cap).
EFFECTIVE_COVERAGE_MULTI_SYMBOL_START = datetime(2022, 7, 14, tzinfo=timezone.utc)
EFFECTIVE_COVERAGE_START_NS = int(EFFECTIVE_COVERAGE_MULTI_SYMBOL_START.timestamp() * NS)

# ------------------------------------------------------------ universe ----

UNIVERSE_N = 25
UNIVERSE_METRIC = "sum(close*volume) over 1m bars"
UNIVERSE_WINDOW_START = datetime(2023, 11, 18, tzinfo=timezone.utc)
UNIVERSE_WINDOW_END = datetime(2023, 12, 18, tzinfo=timezone.utc)

# design §9 — retained as explicit UNPOWERED rows, never silently dropped.
NEVER_DROP_SYMBOLS = ("1000BONKUSDT", "BLURUSDT")

# ------------------------------------------------------------- unit pin ----
# design §4.3 CONVERSION-PIN. The divisor object, stated exactly. Its VALUE is COMPUTED AT RUN
# (results/unit_pin.json) and never recalled or asserted.

UNIT_PIN = {
    "divisor_object": (
        "sigma_t = LTF H1 Parkinson EWMA(lambda=0.94), 60 H1-bar warm-up, causal <= t-1, in bps; "
        "horizon-scaled sigma_t*sqrt(h). Identical object to SPDR-014's Z-VOL width."
    ),
    "indicator": "Parkinson range estimator",
    "smoother": "EWMA",
    "lambda": 0.94,
    "timeframe": "H1",
    "warmup_bars": 60,
    "lag": "t-1 (causal; the decision bar is excluded)",
    "units": "bps",
    "horizon_scaling": "sigma_t * sqrt(h)",
    "measured_value": "COMPUTED AT RUN -> results/unit_pin.json (never asserted)",
    "primary_reporting_unit": "bps",
    "sigma_unit_role": (
        "buys power for pooling only; never a headline in sigma units, never compared to the "
        "cost floor (P-15 / L-21 / design §4.3)"
    ),
}
EWMA_LAMBDA = 0.94
SIGMA_WARMUP_BARS = 60
SIGMA_CLOCK = "H1"
CLOCKS = {
    "M15": {"minutes": 15, "min_minutes": 12},
    "H1": {"minutes": 60, "min_minutes": 48},
    "H4": {"minutes": 240, "min_minutes": 192},
    "D1": {"minutes": 1440, "min_minutes": 1000},
}

# --------------------------------------------------------------- costs ----
# design §4.2 — xen.evaluation overlay ONLY. fees + discrete funding + 2.0 bps allowance.
# spread_bps is PROHIBITED as a cost input (P-20 / L-36).

FEE_RT_BPS = 11.0
FUNDING_BPS_PER_STAMP = 1.0
ALLOWANCE_GOVERNING = 2.0
COST_FLOOR_BPS = 13.5          # partial; spread NOT charged -> the true floor is higher
SPREAD_BPS_PROHIBITED = True

SPREAD_COST_DISCLOSURE = {
    "spread_cost_status": "UNAVAILABLE_NOT_CHARGED",
    "spread_rt_bps": None,
    "cost_scope": "PARTIAL_FEES_FUNDING_ONLY",
    "implication": "reported cost understates total cost; reported net performance is overstated",
    "prohibited_claims": ["fully-net", "cost-complete", "tradable", "deployable"],
}

# --------------------------------------------------------- inference ----
# design §6.2 (BINDING). Day-block bootstrap on per-calendar-day sufficient statistics.
# min block = 1 day = 24 H1 bars >= every horizon in scope. Envelope = min/max over blocks x seeds.

BOOT_BLOCKS_DAYS = (1, 3, 7)
BOOT_SEEDS = (101, 211, 307, 401, 503)
BOOT_RESAMPLES = 2_000
BOOT_CI_ALPHA = 0.05
MAX_HORIZON_HOURS_IN_SCOPE = 24     # asserted against every arm's horizons at run

TRIM_FRACTION = 0.10                 # design §6.1 — 10% trimmed mean (two-sided)

# The iid form is a LABELLED COMPANION COLUMN ONLY and may never drive a band label (M-1).
IID_MDE_CONST = 2.8
MDE_SOURCE_FOR_BANDS = "block"       # asserted in the self-check

# --------------------------------------------------------- controls ----
# design §7. >=2000 seeds on the uniform controls (L-19 / L-32).

DERANGE_SEEDS = tuple(range(31000, 33000))          # 2000 — SIDE-DERANGEMENT
MAGMATCH_SEEDS = tuple(range(71000, 73000))         # 2000 — MAGNITUDE-MATCHED-COMPARATOR
TRIPWIRE_SEEDS = tuple(range(91000, 93000))         # 2000 — FORWARD-PATH DERANGEMENT
PLANT_CURVE_BPS = (5.0, 10.0, 20.0, 40.0)           # design §7 MDE curve
MAGMATCH_DECILES = 10
MAGMATCH_NEIGHBOURHOOD = 1                          # live rows +-1 bar excluded from the draw

# ------------------------------------------------ target precision ----
# design §9 — INHERITED PER ARM from each parent's own registered precision rule.

TARGETS = {
    "A": {
        "rule": "SPDR-012 §6.3: MDE(IC) = 1.5/sqrt(n_dates) <= 0.10  =>  n_dates >= 225",
        "mde_ic_const": 1.5,
        "mde_ic_ceiling": 0.10,
        "min_dates": 225,
        "gap_mde_ceiling_bps": 15.0,
    },
    "B": {
        "rule": "SPDR-013: MDE <= 10 bps AND n_dates >= 30 AND thirds-stable",
        "mde_ceiling_bps": 10.0,
        "min_dates": 30,
        "min_episodes": 80,
        "thirds_sign_min": 2,
    },
    "C": {
        "rule": "SPDR-014 §8.1: n_events >= 80 AND n_dates >= 30 AND MDE <= 10 bps",
        "min_events": 80,
        "min_dates": 30,
        "mde_ceiling_bps": 10.0,
    },
    "D": {
        "rule": "SPDR-015: n_origins >= 80 AND n_dates >= 30",
        "min_origins": 80,
        "min_dates": 30,
        "min_trans": 50,
        "min_swings": 80,
    },
    "uniform_edge": {
        "rule": "block MDE on p below the cell's own |edge|",
    },
}

# ------------------------------------------------------------- bands ----
# design §8 — LABELS, NEVER GATES. No `pass` field is emitted anywhere (INFR-016 / L-32).

BAND_MEAN_SUPPORTED_BPS = 10.0
BAND_MEAN_WASH_ABS_BPS = 10.0
BAND_MEAN_CONTRADICTED_BPS = -10.0
BAND_MEAN_MDE_CEILING_BPS = 10.0

BAND_LABELS = (
    "SUPPORTED", "WASH", "CONTRADICTED", "UNPOWERED", "NOT_RESOLVABLE",
)
NO_PASS_FIELD = True

# --------------------------------------------------- parent parity ----
# design §12 — the anti-drift check. Tolerances are DECLARED here, before the run.

PARITY_TOL = {
    "mean_bps": 0.01,        # re-derived cell mean vs parent published mean
    "rate": 1e-6,            # rates / probabilities
    "ic": 1e-6,
    "n": 0,                  # counts must match exactly
    "brier": 1e-9,
}
PARITY_MIN_CELLS_PER_ARM = 20   # how many published parent cells each arm must reproduce

IDENTITY_RECONSTRUCTION_TOL_BPS = 0.01   # |p*W - (1-p)*L - mean| < 0.01 bps  (HARD)

# ------------------------------------------------------- prohibitions ----

PROHIBITED_CLAIMS = [
    "tradable", "deployable", "fully-net", "cost-complete",
    "p > 0.5", "win-rate as the direction metric",
    "family status change", "XENA", "graduation", "sizing improves expectancy",
    "straddle as a strategy branch",
]

# --------------------------------------------------------- deviations ----

DEVIATIONS: list[dict] = []

INTERPRETATION_NOTES: list[dict] = [
    {
        "id": "IN-1",
        "clause": "design §1.1 / §15 'reuse the parents' screen_code; arm runners importing "
                  "the parent modules'",
        "resolution": (
            "Each arm imports its parent's modules for constants, band rules, control seeds, cost "
            "constants and pure helper functions (screen_code/parents.py, isolated sys.path "
            "loader), and re-scores the parent's OWN emitted row-level panel "
            "(012 vol_reliability/xs_panel, 013 episodes, 014 post_event/straddle, "
            "015 regime_states/zz_ordinal). Those panels already span the full TRAIN fence with a "
            "band column, so power levers 1-4 apply without re-specifying any object. Where a "
            "parent never computed a band at all (D8: SPDR-015 masked is_origin to DESIGN), the "
            "parent's own module is RE-RUN on the CONFIRM origins. Parent parity (§12) is asserted "
            "against each parent's published values, which is what makes the re-score verifiable."
        ),
        "weakens_clause": False,
    },
    {
        "id": "IN-2",
        "clause": "design §7 uniform controls at >=2000 seeds",
        "resolution": (
            "The three uniform controls run on each arm's DESIGNATED PRIMARY CELLS (its parent's "
            "own registered CONTROL_PRIMARY_CELL, plus the arm's pooled cell and its powered "
            "cells), not on every one of the several thousand grid cells — the parents' own "
            "control blocks are scoped the same way. The scope is emitted in controls.json so "
            "nothing is hidden; no cell is dropped from the metrics table."
        ),
        "weakens_clause": False,
    },
    {
        "id": "IN-3",
        "clause": "design §6.2 'xen.evaluation.block_bootstrap_ci'",
        "resolution": (
            "Called with the per-calendar-day sufficient statistics as the resampled series "
            "(x[i] = [sum_i, count_i] for day i) and a stat that recovers the count-weighted mean, "
            "so the day-block resample is exact for a weighted mean. Blocks are in DAYS, so the "
            "minimum block (1 day = 24 H1 bars) is >= every horizon in scope, as §6.2 requires. "
            "For the mean/p/W/L/W_L/edge family the resample loop is vectorised so all six "
            "statistics come out of ONE pass per (block, seed) — the index construction is "
            "identical to block_bootstrap_ci's (same rng, same circular full-range starts, same "
            "cap to [1, n-1]) and equality with the canonical implementation is ASSERTED at run "
            "in the integrity self-check (metrics.assert_canonical_equivalence; measured "
            "|diff| <= 2e-14). It is a speed path over the same referee, not a second referee. "
            "Median and 10% trimmed mean, which need the raw rows, keep the canonical call."
        ),
        "weakens_clause": False,
    },
    {
        "id": "IN-5",
        "clause": "design §6.1 — 'mean, median, 10% trimmed mean ... block-bootstrap CI on each, "
                  "all three always co-reported'",
        "resolution": (
            "All three point statistics are emitted on EVERY cell, always. Their block-bootstrap "
            "CIs are computed on the cells whose band label can depend on them — the "
            "levers-exhausted (pooled, sigma-normalised, full-TRAIN) cells, which are the ones "
            "that decide RESOLVED vs NOT_RESOLVABLE. The mean family (mean/p/W/L/W_L/edge) "
            "carries its envelope CI on every cell without exception, because it decomposes into "
            "per-day sufficient statistics; median and trimmed mean do not decompose and cost "
            "~190s per large pooled cell even fully vectorised, so bootstrapping them across all "
            "~30k grid cells is not tractable. Scope is emitted per cell "
            "(`median_ci_low`/`median_ci_high` present or absent), never hidden."
        ),
        "weakens_clause": False,
        "raised_to_operator": True,
    },
    {
        "id": "IN-4",
        "clause": "design §2 arm B item B3 — 'the 125 positive-mean cells, every one UNPOWERED'",
        "resolution": (
            "The count 125 does not reconcile against SPDR-013's published "
            "expectancy_by_cell.parquet under any slice: positive expectancy_partial AND "
            "band_label==UNPOWERED gives 830 cells grid-wide (352 on DESIGN, 187 on DESIGN x H1, "
            "284 on CONFIRM x H1, 471 on H1 across both bands); on gross it is 1237. Since the "
            "mandate forbids narrowing the residue, B3 is tagged as the SUPERSET — all 830 "
            "positive-mean UNPOWERED cells — so no cell the SoT could have meant is dropped. "
            "The discrepancy is RAISED to the operator, not silently resolved."
        ),
        "weakens_clause": False,
        "raised_to_operator": True,
    },
]


def assert_no_spread_cost_input(**kwargs) -> None:
    """P-20 / L-36: raw SpreadBps may never enter a cost figure."""
    for k in kwargs:
        if "spread" in k.lower():
            raise ValueError(
                f"spread is not a cost input in this programme (P-20 / L-36): got {k!r}"
            )
