"""SPDR-017 frozen constants — independent predicted-price mispricing (O3 Group 3b / HYP-D4).

TRAIN-only SPDR screen. Design freeze: python/experiments/SPDR-017/design.md.
No hard start gate on 014 residual. DEVIATIONS: none authorised at implement time.
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
# design §0: DESIGN primary; CONFIRM verify; TEST/holdout never.

DESIGN_START = datetime(2021, 6, 29, 6, 53, tzinfo=timezone.utc)
DESIGN_END = datetime(2023, 3, 1, tzinfo=timezone.utc)       # exclusive
CONFIRM_START = DESIGN_END
CONFIRM_END = datetime(2023, 12, 18, tzinfo=timezone.utc)    # exclusive == train_end_utc
TEST_START = CONFIRM_END
HOLDOUT_START = datetime(2025, 1, 8, tzinfo=timezone.utc)

BANDS = {
    "DESIGN": (DESIGN_START, DESIGN_END),
    "CONFIRM": (CONFIRM_START, CONFIRM_END),
}
PRIMARY_BAND = "DESIGN"
TRAIN_END = CONFIRM_END
NS = 1_000_000_000

# ------------------------------------------------------------ universe ----

UNIVERSE_METRIC = "sum(close*volume) over 1m bars"
UNIVERSE_WINDOW_START = datetime(2023, 11, 18, tzinfo=timezone.utc)
UNIVERSE_WINDOW_END = datetime(2023, 12, 18, tzinfo=timezone.utc)
UNIVERSE_N = 25

# --------------------------------------------------------------- clocks ----

CLOCKS: dict[str, dict] = {
    "H1": {"minutes": 60, "truncate": "1h", "min_minutes": 48, "warmup_bars": 60},
}
PRIMARY_CLOCK = "H1"

# ----------------------------------------------------------- Z-VOL / ZZ ----

EWMA_LAMBDA = 0.94
ZVOL_WARMUP_BARS = 60
ZVOL_EPS = 1e-12
Z_VALUES = (1.0, 1.5, 2.0)
H_VALUES = (4, 12, 24)
H_POST = (4, 12, 24)
H_STAR = 12                          # error-dynamics window (design §2.2)
EVENT_TYPES = ("E-TOUCH", "E-CLOSE", "E-HORIZON")
PRIMARY_EVENT = "E-TOUCH"

ATR_PERIOD = 14
ZZ_REVERSAL_ATR = 2.0
RIDGE_ALPHA = 1.0
ZZ_MIN_TRAIN_SWINGS = 20
ZMAG_FLOOR_BPS = 1.0
SMA_PERIOD = 25
SMA_ANGLE_LOOKBACK = 5
SMA_ANGLE_ATR_MULT = 0.25

# ---------------------------------------------------- model / ablation ----

ABLATIONS = ("A0", "A1", "A2")
PRIMARY_ABLATION = "A2"
MODELS = ("M-RIDGE", "M-GBM")
PRIMARY_MODEL = "M-RIDGE"
MIN_TRAIN_ROWS = 80
MONTH_REFIT = True                   # walk-forward monthly refit
GBM_DEPTH = 3
GBM_N_EST = 40          # ≤100 design cap; 40 for TRAIN screen runtime
GBM_MIN_LEAF = 50
GBM_LR = 0.05
GBM_SEED = 17

SOURCES = ("M-ZONE", "M-SIGN-ERR", "Z-VOL")   # Z-VOL = 014 co-baseline
PRIMARY_SOURCE = "M-ZONE"

# Feature column names by layer
PROVEN_COLS = (
    "ewma_park", "lvl_pct", "zz_mag_hat", "slow_reg", "shock",
)
DERIVED_COLS = (
    "pred_move_bps", "real_move_bps", "err_abs", "err_signed",
    "d_err", "d_vol", "err_z",
)
WEAK_DIR_COLS = (
    "sma25_sign", "sma25_angle_on", "zz_next_leg_sign",
)

FEATURE_LAYERS = {
    "A0": PROVEN_COLS,
    "A1": PROVEN_COLS + DERIVED_COLS,
    "A2": PROVEN_COLS + DERIVED_COLS + WEAK_DIR_COLS,
}

# ------------------------------------------------ residual / labels ----

DEADBAND_BPS = 5.0
STOP_ATR_MULT = 1.5

# ----------------------------------------------------------- money subset ----
# P-MOMO / P-MR on E-TOUCH × z=1.5 × H=12 × h=12 × M-ZONE × A2 × M-RIDGE

MONEY_Z = 1.5
MONEY_H = 12
MONEY_H_POST = 12
MONEY_EVENT = "E-TOUCH"
MONEY_SOURCE = "M-ZONE"
MONEY_ABLATION = "A2"
MONEY_MODEL = "M-RIDGE"
MONEY_POLICIES = ("P-MOMO", "P-MR")

# --------------------------------------------------------------- costs ----

FEE_RT_BPS = 11.0
FUNDING_BPS_PER_STAMP = 1.0
ALLOWANCE_GOVERNING = 2.0

SPREAD_COST_DISCLOSURE = {
    "spread_cost_status": "UNAVAILABLE_NOT_CHARGED",
    "spread_rt_bps": None,
    "cost_scope": "PARTIAL_FEES_FUNDING_ONLY",
    "implication": "partial_net overstated vs full cost",
    "prohibited_claims": ["fully-net", "cost-complete", "tradable", "deployable"],
}

# --------------------------------------------------------- inference ----

BOOT_BLOCKS = (1, 3, 7)
BOOT_SEEDS = (101, 211, 307, 401, 503)
BOOT_RESAMPLES = 5_000
BOOT_CI_ALPHA = 0.05
THIRDS_SIGN_MIN = 2

BAND_SUPPORTED_BPS = 5.0
BAND_WASH_ABS_BPS = 5.0
BAND_CONTRADICTED_BPS = -5.0
UNPOWERED_MIN_EVENTS = 80
UNPOWERED_MIN_DATES = 30
UNPOWERED_MDE_CEILING_BPS = 10.0

# --------------------------------------------------------- controls ----

TIME_SHUFFLE_SEEDS = tuple(range(61000, 61200))
MATCHED_RANDOM_SEEDS = tuple(range(71000, 71200))
FEATURE_SHUFFLE_SEEDS = tuple(range(81000, 81050))  # 50 seeds; model-skill control
TRIPWIRE_SEEDS = tuple(range(91000, 91200))
PLANT_BPS = 20.0
CONTROL_PRIMARY_CELL = {
    "source": "M-ZONE", "z": 1.5, "H": 12, "event": "E-TOUCH", "h": 12,
    "ablation": "A2", "model": "M-RIDGE",
}

# --------------------------------------------------------- O3 pins ----

O3_SOT_PATH = ".ignore/what-next/alts/cf-voldir-o3-zone-event-sequence.md"
PROHIBITED_CLAIMS = [
    "tradable", "deployable", "fully-net", "cost-complete",
    "signed vol×direction product", "shock-as-regime",
    "family status change", "XENA", "014 residual start gate",
]

DEVIATIONS: list[dict] = [
    {
        "id": "DEV-1",
        "clause": "design §2.4 M-GBM (sklearn not in project venv)",
        "resolution": (
            "Pure-numpy depth-limited residual tree ensemble (depth≤3, n_est≤100, "
            "min_leaf≥50, lr=0.05) — same hyperparams; sensitivity only."
        ),
        "weakens_clause": False,
    },
]
INTERPRETATION_NOTES: list[dict] = [
    {
        "id": "IN-1",
        "clause": "design §2.1 optional hmm_rv / ord_gt_cur (SPDR-015)",
        "resolution": "SPDR-015 design-only at implement time — optional features omitted.",
        "weakens_clause": False,
    },
    {
        "id": "IN-2",
        "clause": "design §3.1 return head primary",
        "resolution": "ŷ = next H-bar open-to-open return (bps) from anchor open[t+1].",
        "weakens_clause": False,
    },
    {
        "id": "IN-3",
        "clause": "design §6 own residual pin (not 016)",
        "resolution": (
            "Emit results/017_residual_pin.json parallel schema to 014; residual_status "
            "NONE unless ≥1 powered SUPPORTED cell. No hard gate on 014 pin."
        ),
        "weakens_clause": False,
    },
]
