"""SPDR-018B constants — the cTrader universe. Everything else is inherited from SPDR-018.

Named ``config18b`` rather than ``config`` on purpose: SPDR-018's own ``config`` module is
imported unchanged by the reused metrics / cells / controls layers, and a same-named module here
would shadow it (the exact failure that broke arm D in SPDR-018 — see that experiment's
``uniform_controls`` rename).
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

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
SPDR018_SCREEN_CODE = REPO_ROOT / "python" / "experiments" / "SPDR-018" / "screen_code"

# ------------------------------------------------------------------ catalog ----

CTRADER_BAR_DIR = REPO_ROOT / "data" / "catalog_ctrader" / "data" / "bar"
CTRADER_BAR_TYPE_SUFFIX = ".CTrader-1-MINUTE-LAST-EXTERNAL"
CTRADER_FENCE_PATH = (
    REPO_ROOT / "python" / "experiments" / "INFR-021" / "artifacts" / "fence-manifest.json"
)
CTRADER_FENCE_SHA256 = "4cdc7b01dd47200710d0d961639d55d52e1129ca89096e841eafd816b6061de0"
CTRADER_SYMBOLS = ("EURUSD", "XAUUSD", "USTEC")

# --------------------------------------------------------------------- bands ----
# design §2.1 — computed on cTrader's OWN TRAIN span, at the same proportion Bybit uses
# (Bybit DESIGN = 609d of a 901d TRAIN span = 0.676172).

CTRADER_DESIGN_START = datetime(2021, 6, 2, 0, 1, tzinfo=timezone.utc)
CTRADER_DESIGN_END = datetime(2023, 2, 2, tzinfo=timezone.utc)      # exclusive
CTRADER_CONFIRM_START = CTRADER_DESIGN_END
CTRADER_CONFIRM_END = datetime(2023, 11, 22, tzinfo=timezone.utc)   # exclusive == train_end
CTRADER_HOLDOUT_START = datetime(2024, 12, 13, tzinfo=timezone.utc)  # never queried

BYBIT_DESIGN_FRACTION = 0.676172   # provenance of the split above

NS = 1_000_000_000
CTRADER_DESIGN_START_NS = int(CTRADER_DESIGN_START.timestamp() * NS)
CTRADER_DESIGN_END_NS = int(CTRADER_DESIGN_END.timestamp() * NS)
CTRADER_TRAIN_END_NS = int(CTRADER_CONFIRM_END.timestamp() * NS)
CTRADER_HOLDOUT_START_NS = int(CTRADER_HOLDOUT_START.timestamp() * NS)

BANDS = {
    "DESIGN": (CTRADER_DESIGN_START, CTRADER_DESIGN_END),
    "CONFIRM": (CTRADER_CONFIRM_START, CTRADER_CONFIRM_END),
    "TRAIN": (CTRADER_DESIGN_START, CTRADER_CONFIRM_END),
}

# ---------------------------------------------------------------------- cost ----
# design §3 — a BORROWED model, operator-directed. NOT a cTrader cost measurement.

COST_MODEL_PROVENANCE = {
    "source": ("SPDR-014 screen_code/costs.py -> xen.evaluation (Bybit taker fee 11.0 bps round "
               "trip + discrete funding stamps + 2.0 bps allowance)"),
    "applied_to": list(CTRADER_SYMBOLS),
    "status": "BORROWED",
    "operator_directive": "2026-07-25 — reuse the crypto universe's cost model for simplicity",
    "what_it_supports": ("comparability of net figures ACROSS the two universes on one common "
                         "yardstick — and nothing else"),
    "what_it_is_not": ("a cTrader cost model, a cTrader cost measurement, or grounds for any "
                       "tradability claim. Perp funding does not exist on these instruments and "
                       "the fee schedule is a different broker's."),
    "gross_is_primary": True,
    "vol_scaling": ("costs are SCALED by the measured sigma ratio (cTrader/crypto) so the charge "
                    "is equivalent in volatility units across the two universes — operator "
                    "directive 2026-07-25. BOTH legs are emitted per cell: the vol-scaled net "
                    "(headline) and the unscaled borrowed net (companion). Gross remains primary."),
    "doubly_synthetic": ("this cost is BORROWED and RESCALED. It is not any instrument's real "
                         "cost and supports exactly one claim: cross-universe comparability in "
                         "volatility units."),
    "spread": "UNAVAILABLE_NOT_CHARGED — per-symbol spread pin remains blocking for a money read",
}

SPDR018_UNIT_PIN = REPO_ROOT / "python" / "experiments" / "SPDR-018" / "results" / "unit_pin.json"


def vol_scale_ratio() -> dict:
    """cTrader sigma / crypto sigma — COMPUTED AT RUN from both measured unit pins.

    Operator directive 2026-07-25: scale the borrowed cost model by the volatility-scale
    difference between the universes. Rationale: a flat bps cost is not comparable across
    universes whose sigma differs 5.6x — the same 13.5 bps is a far heavier drag in sigma units
    on the lower-vol book, which would make any cross-universe net comparison an artifact of the
    cost model rather than of the data.

    Neither sigma is asserted: crypto's is read from SPDR-018's EMITTED unit_pin.json (a measured
    artifact), cTrader's is measured in this run.
    """
    import json
    crypto = json.loads(SPDR018_UNIT_PIN.read_text())["pooled_median_sigma_bps"]
    return {"crypto_sigma_bps": float(crypto), "provenance_crypto": str(SPDR018_UNIT_PIN),
            "provenance_ctrader": "measured in this run (results/unit_pin.json)"}


SPREAD_COST_DISCLOSURE = {
    "spread_cost_status": "UNAVAILABLE_NOT_CHARGED",
    "spread_rt_bps": None,
    "cost_scope": "PARTIAL_FEES_FUNDING_ONLY (BORROWED MODEL)",
    "implication": "reported cost understates total cost; reported net performance is overstated",
    "prohibited_claims": ["fully-net", "cost-complete", "tradable", "deployable",
                          "this is the cTrader cost"],
}

# ------------------------------------------------------------------- power ----
# design §7 — 3 instruments against 25. Pooling is far weaker; predeclared.

N_SYMBOLS = len(CTRADER_SYMBOLS)
POWER_NOTE = (
    "3 instruments against 25. Cells powered on crypto may be NOT_RESOLVABLE here purely on n. "
    "That is a statement about this universe's size, NEVER evidence against the crypto result "
    "(B-5). An unpowered non-replication says nothing."
)

# ------------------------------------------------------------------ parity ----
# design §5 — parent parity cannot exist here; the substitute is a cross-universe identity guard.

IDENTITY_GUARD = {
    "check": "CROSS-UNIVERSE OBJECT IDENTITY",
    "severity": "HARD",
    "statement": ("the retargeted code path, run on a BYBIT symbol, must reproduce SPDR-018's "
                  "emitted cells for that symbol exactly — proving the retarget changed the DATA "
                  "and not the OBJECT"),
    "tolerance_bps": 0.01,
    "guard_symbol": "BTCUSDT",
}

PROHIBITED_CLAIMS = [
    "tradable", "deployable", "fully-net", "cost-complete",
    "this is the cTrader cost", "pooled with crypto", "cTrader as power",
    "p > 0.5", "family status change", "XENA", "graduation",
    "unpowered non-replication as a negative",
]

DEVIATIONS: list[dict] = []
INTERPRETATION_NOTES: list[dict] = [
    {
        "id": "IN-B1",
        "clause": "design §4 — objects rebuilt from parent code rather than re-scored",
        "resolution": (
            "No parent screen ever ran on cTrader, so there is no emitted panel to re-score. Each "
            "arm drives its parent's own modules against cTrader bars, with catalog and band "
            "constants rebound across every loaded parent module (retarget.py). Parent source is "
            "never edited. The claim that this changed the DATA and not the OBJECT is checked by "
            "the §5 cross-universe identity guard, not asserted."
        ),
        "weakens_clause": False,
    },
    {
        "id": "IN-B2",
        "clause": "design §3 — borrowed cost model",
        "resolution": (
            "Operator-directed simplification. Every net figure on this universe carries the "
            "BORROWED label in the emission, and gross is reported alongside net on every cell. "
            "No cTrader net figure may be cited as that instrument's cost."
        ),
        "weakens_clause": False,
    },
]
