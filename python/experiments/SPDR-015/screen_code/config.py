"""SPDR-015 frozen constants — design.md + O3-SOT (Group 2 conditioner science).

TRAIN-only. No tradability claim. Shock ≠ regime. Headline 2a metric = Δ vs persistence.
DEVIATIONS: NONE authorised.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------- paths ----

EXP_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"


def _repo_root() -> Path:
    p = Path(__file__).resolve()
    for parent in p.parents:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("repo root not found")


REPO_ROOT = _repo_root()
CATALOG_BAR_DIR = REPO_ROOT / "data" / "catalog" / "data" / "bar"
UNIVERSE_PIN_FAMILY = (
    REPO_ROOT / "docs" / "signal-registry" / "candidate-families" / "cf-voldir-001-universe.json"
)
UNIVERSE_PIN_RESULTS = RESULTS_DIR / "universe_top25.json"

BAR_TYPE_SUFFIX = "-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL"

# --------------------------------------------------------------- bands ----
# design §0 scope fence.

DESIGN_START = datetime(2021, 6, 29, 6, 53, tzinfo=timezone.utc)
DESIGN_END = datetime(2023, 3, 1, tzinfo=timezone.utc)  # exclusive
CONFIRM_START = DESIGN_END
CONFIRM_END = datetime(2023, 12, 18, tzinfo=timezone.utc)  # exclusive == train_end_utc
TEST_START = CONFIRM_END  # never read
HOLDOUT_START = datetime(2025, 1, 8, tzinfo=timezone.utc)  # never read

NS = 1_000_000_000

# ------------------------------------------------------------ universe ----

UNIVERSE_METRIC = "sum(close*volume) over 1m bars"
UNIVERSE_WINDOW_START = datetime(2023, 11, 18, tzinfo=timezone.utc)
UNIVERSE_WINDOW_END = datetime(2023, 12, 18, tzinfo=timezone.utc)
UNIVERSE_N = 25

# --------------------------------------------------------------- clocks ----
# design §0: H1 primary; H4 co-report full 2a; D1 optional disclosure R-MARKOV stickiness only.

CLOCKS: dict[str, dict] = {
    "H1": {"minutes": 60, "truncate": "1h", "min_minutes": 48, "warmup_bars": 60},
    "H4": {"minutes": 240, "truncate": "4h", "min_minutes": 192, "warmup_bars": 40},
    "D1": {"minutes": 1440, "truncate": "1d", "min_minutes": 1000, "warmup_bars": 40},
}
CLOCK_PRIMARY = "H1"
CLOCKS_2A = ("H1", "H4")  # full 2a metrics
CLOCK_D1_DISCLOSURE = "D1"  # R-MARKOV stickiness only

# ---------------------------------------------------------- estimation ----

RV_WINDOW = 20
EWMA_LAMBDA = 0.94  # Parkinson EWMA λ
RIDGE_ALPHA = 1.0
LOGIT_RIDGE_ALPHA = 1.0
INITIAL_FIT_FRACTION = 0.40
REFIT_CADENCE = "monthly"
HORIZONS_K = (1, 4, 12)
RUN_LEN_CAP = 48
DUR_CAP = 48
N_HIGH_K = (4, 12)

# State models (design §2.1)
STATE_MODELS = ("R-MARKOV", "R-HMM-RV", "R-SHOCK")
# Forecast methods for s_{t+1} / s_{t+k} (design §2.4)
FORECAST_METHODS = ("persistence", "empirical_p", "logistic_ridge")

# ---------------------------------------------------------- ZZ ordinal ----
# design §3; H1 primary.

ZZ_CLOCK = "H1"
ATR_PERIOD = 14
ZZ_REVERSAL_ATR = 2.0
ZZ_MEDIAN_K = (5, 10)
ZZ_MIN_TRAIN = 20
ZZ_FEATURES = (
    "magnitude_bps", "direction", "angle_bps_per_bar", "path_noise_atr", "bars_in_swing"
)
ORDINAL_MODELS = ("ar1_threshold", "ridge_cont", "logit_ridge")
ORDINAL_TARGETS = ("T-GT-CUR", "T-GT-MED5", "T-GT-MED10")

# ---------------------------------------------------------- inference ----

BOOT_BLOCKS = (1, 3, 7)
BOOT_SEEDS = (101, 211, 307, 401, 503)
BOOT_RESAMPLES = 2000  # screen-scale; full 10k optional
BOOT_CI_ALPHA = 0.05
DERANGE_SEEDS = tuple(range(31000, 31200))  # 200 seeds
MIN_ORIGINS = 80
MIN_DATES = 30
MIN_TRANS = 50
MIN_SWINGS = 80

# bands 2a (labels only)
# SUPPORTED: Δ Brier < 0 AND CI high on Δ Brier < 0
# 2b: hit ≥ base+0.05 AND CI low > base OR Brier skill with CI

# ------------------------------------------------ cost disclosure ----

SPREAD_COST_DISCLOSURE = {
    "spread_cost_status": "UNAVAILABLE_NOT_CHARGED",
    "spread_rt_bps": None,
    "cost_scope": "PARTIAL_FEES_FUNDING_ONLY",
    "implication": (
        "any optional money overlay understates true cost; "
        "no fully-net/tradable/deployable claim"
    ),
    "prohibited_claims": ["fully-net", "cost-complete", "tradable", "deployable"],
}

PROHIBITED_CLAIMS = [
    "tradable", "deployable", "fully-net", "cost-complete",
    "shock as regime", "stickiness as transition skill",
    "family status change", "silent 014 rewrite",
]

O3_SOT = {
    "path": ".ignore/what-next/alts/cf-voldir-o3-zone-event-sequence.md",
    "role": "BINDING substance Group 2",
    "hard_object": (
        "2a level-regime + transition skill BEATS persistence; "
        "2b ordinal next-swing size; shock ≠ regime"
    ),
}

DEVIATIONS: list[dict] = []

INTERPRETATION_NOTES = [
    {
        "id": "IN-1",
        "clause": "design §2.4 logistic-ridge monthly walk-forward",
        "resolution": (
            "Initial fit = first 40% of scored DESIGN origins (per symbol×clock); "
            "monthly expanding re-fit thereafter (same catalog-cap reading as SPDR-012 IN-1)."
        ),
        "weakens_clause": False,
    },
    {
        "id": "IN-2",
        "clause": "design §2.1 R-HMM-RV on raw rv20",
        "resolution": "Observation = raw rv20 (not log); HIGH = larger-mean state on rv20.",
        "weakens_clause": False,
    },
    {
        "id": "IN-3",
        "clause": "design §5 T1 TARGET-FUTURE-DESTROY informative",
        "resolution": (
            "Construction asserts carry HARD causality (HMM fit end < origin; "
            "ZZ features ≤ confirm). Label derangement is informative collapse fraction."
        ),
        "weakens_clause": False,
    },
    {
        "id": "IN-4",
        "clause": "design §2.5/§3.4 band CI + §5 blocks 1/3/7 multi-seed",
        "resolution": (
            "Δ-Brier (2a) and hit/Δ-Brier (2b) CIs use the canonical circular block bootstrap "
            "(xen.evaluation.block_bootstrap_ci): blocks 1/3/7 (days for 2a origins, swings for "
            "2b) × 5-seed envelope (base 101) × 2000 resamples. 2a day-blocks are converted to "
            "origin-positions and floored at H=k so block≥H on every cell (fixes the H4 k=12 "
            "under-blocking). The SUPPORTED band uses the CONSERVATIVE envelope across the sweep "
            "(2a: max ci_hi<0; 2b: min hit ci_lo>base or max Δ-Brier ci_hi<0), so block-fragile "
            "inference cannot earn SUPPORTED. Tightens, never loosens, the frozen band."
        ),
        "weakens_clause": False,
    },
    {
        "id": "IN-5",
        "clause": "design §4 CONTROL LABEL-SHUFFLE (destroy_form DERANGEMENT, bite/MDE)",
        "resolution": (
            "Collapse uses a true L-28 zero-fixed-point index derangement "
            "(xen.xena.controls.make_derangement), asserted per seed, over the 200-seed "
            "DERANGE_SEEDS battery read as a percentile (collapse_frac). Run on BOTH 2a "
            "(level-regime × fitted method × horizon) and 2b (target × model) powered cells. "
            "A +0.05 hit-rate bite plant verifies the test detects a small real edge. Replaces "
            "the QA-flagged plain rng.shuffle (2b-only, single seed, no bite)."
        ),
        "weakens_clause": False,
    },
]
