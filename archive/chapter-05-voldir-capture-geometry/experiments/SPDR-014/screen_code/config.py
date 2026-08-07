"""SPDR-014 frozen constants — every value traces to design.md / O3 SoT / checkpoint-017.

Zone → mispricing event → post-event MOMO vs MR characterisation (Group 1 / HYP-D1).
TRAIN-only SPDR screen. DEVIATIONS: none authorised at implement time.
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
    "H4": {"minutes": 240, "truncate": "4h", "min_minutes": 192, "warmup_bars": 60},
}
PRIMARY_CLOCK = "H1"

# ----------------------------------------------------------- Z-VOL / Z-MAG ----

EWMA_LAMBDA = 0.94
ZVOL_WARMUP_BARS = 60                 # design §2.2 first 60 complete H1 in DESIGN
ZVOL_EPS = 1e-12
Z_VALUES = (1.0, 1.5, 2.0)
H_VALUES = (4, 12, 24)
H_POST = (4, 12, 24)
SOURCES = ("Z-VOL", "Z-MAG")
EVENT_TYPES = ("E-TOUCH", "E-CLOSE", "E-HORIZON")
PRIMARY_EVENT = "E-TOUCH"

ATR_PERIOD = 14
ZZ_REVERSAL_ATR = 2.0
RIDGE_ALPHA = 1.0
ZZ_MIN_TRAIN_SWINGS = 20
ZMAG_FLOOR_BPS = 1.0
ZMAG_SENSITIVITY_DIV = 2.0            # co-report σ = predicted_mag / 2

# ------------------------------------------------ residual / labels ----

DEADBAND_BPS = 5.0                    # design §4.2 c = 5 bps
STOP_ATR_MULT = 1.5                   # design §5 stop 1.5 × ATR(14)[entry-1]

# ----------------------------------------------------------- money subset ----
# P-MOMO + P-MR on E-TOUCH × h=12 × z=1.5 × {Z-VOL,Z-MAG} only

MONEY_Z = 1.5
MONEY_H_ZONE = None                   # money residual hold h=12; zone H still varies? design:
# "P-MOMO + P-MR on E-TOUCH × h=12 × z=1.5 × {Z-VOL,Z-MAG} only"
# does not pin H for money — use H=12 as the co-report primary freeze sketch row
MONEY_H = 12
MONEY_H_POST = 12
MONEY_EVENT = "E-TOUCH"
MONEY_SOURCES = ("Z-VOL", "Z-MAG")
MONEY_POLICIES = ("P-MOMO", "P-MR")

# H4 co-report: Z-VOL, z=1.5, H=12, E-TOUCH, h=12, P-NONE only
H4_SLICE = {
    "source": "Z-VOL", "z": 1.5, "H": 12, "event": "E-TOUCH", "h": 12, "policy": "P-NONE",
}

# DA-STRADDLE × Z-VOL × z=1.5 × H∈{4,12,24}
STRADDLE_SOURCE = "Z-VOL"
STRADDLE_Z = 1.5
STRADDLE_HS = (4, 12, 24)

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

TIME_SHUFFLE_SEEDS = tuple(range(61000, 61200))       # >=200
MATCHED_RANDOM_SEEDS = tuple(range(71000, 71200))     # >=200
GATE_SHUFFLE_SEEDS = tuple(range(81000, 81200))
TRIPWIRE_SEEDS = tuple(range(91000, 91200))
PLANT_BPS = 20.0
CONTROL_PRIMARY_CELL = {
    "source": "Z-VOL", "z": 1.5, "H": 12, "event": "E-TOUCH", "h": 12,
}

# --------------------------------------------------------- O3 pins ----

O3_SOT_PATH = ".ignore/what-next/alts/cf-voldir-o3-zone-event-sequence.md"
PROHIBITED_CLAIMS = [
    "tradable", "deployable", "fully-net", "cost-complete",
    "signed vol×direction product", "shock-as-regime", "straddle-only headline",
    "family status change", "XENA",
]

DEVIATIONS: list[dict] = []
INTERPRETATION_NOTES: list[dict] = [
    {
        "id": "IN-1",
        "clause": "design §5 money subset does not pin zone H",
        "resolution": (
            "Money policies use z=1.5, h=12, E-TOUCH, Z-VOL|Z-MAG, and zone H=12 "
            "(O3 freeze sketch primary H)."
        ),
        "weakens_clause": False,
    },
    {
        "id": "IN-2",
        "clause": "design §2.2 Z-MAG 'ridge walk-forward monthly refit (013 recipe)'",
        "resolution": (
            "Use expanding walk-forward ridge on completed swings (SPDR-013 recipe). "
            "Monthly refit ≡ retrain at each new swing with all prior swings (expanding)."
        ),
        "weakens_clause": False,
    },
    {
        "id": "IN-3",
        "clause": "design §4.4 last-k state (O3 'last-k states / last X labels')",
        "resolution": (
            "HIGH/LOW label == slow_regime (SPDR-012 V-REGIME rolling-median split of rv20 — "
            "the only HIGH/LOW regime series the design defines; O3 'slow Markov'). Per "
            "AMENDMENT-S2 (2026-07-24), emit the ORDERED label sequence over the last K bars "
            "(last_k_state_1/2/3; operator-directed K∈{1,2,3}; chronological oldest→newest; "
            "'H'/'L'/'?'=NaN; decision bar = last char; causal ≤t) — preserves order + run-length "
            "that O3 §2.1/§2.2 requires. Supersedes the earlier count-of-HIGH (K∈{4,12}) reading. "
            "Emitted on zones/events/post_event."
        ),
        "weakens_clause": False,
    },
    {
        "id": "IN-4",
        "clause": "design §8.3 residual_status semantics (pin builder)",
        "resolution": (
            "residual_status reflects the POWERED residual object only: NONE unless ≥1 cell clears "
            "the full §8.1 SUPPORTED gate (MDE≤10, |Δ|≥5, CI-excl-0, median-sign, thirds≥2). A "
            "per-cell rate lean with 0 powered cells is disclosure-only (rate_lean / "
            "n_rate_*_suggestive), never promoted to *_DOMINANT. Faithful tightening of the §8.3 "
            "gate rule (016_start only if status≠NONE AND ≥1 powered cell); operator ratifiable."
        ),
        "weakens_clause": False,
    },
]
