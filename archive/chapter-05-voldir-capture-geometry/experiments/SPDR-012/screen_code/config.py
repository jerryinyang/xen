"""SPDR-012 frozen constants — every value traces to design.md / checkpoint-017 / RAW.

DEVIATIONS: ONE (``DEVIATIONS`` below). DEV-1 removes the design §5 HARD future-destroy
tripwire and reports it as a layer instead — operator decision 2026-07-23, recorded as
AMENDMENT-T1 in design.md §5. Ambiguity resolutions that weaken no clause are separate and
live in ``INTERPRETATION_NOTES`` (IN-1..IN-9). Both are reproduced in
results/integrity_selfcheck.json and results/compliance_trace.md.
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
DESIGN_END = datetime(2023, 3, 1, tzinfo=timezone.utc)      # exclusive
CONFIRM_START = DESIGN_END
CONFIRM_END = datetime(2023, 12, 18, tzinfo=timezone.utc)   # exclusive == train_end_utc
TEST_START = CONFIRM_END           # never read
HOLDOUT_START = datetime(2025, 1, 8, tzinfo=timezone.utc)   # never read

NS = 1_000_000_000

# ------------------------------------------------------------ universe ----
# design §0.1 UNIVERSE-PIN (AMENDMENT-U1). Recomputed at run time and asserted equal.

UNIVERSE_METRIC = "sum(close*volume) over 1m bars"
UNIVERSE_WINDOW_START = datetime(2023, 11, 18, tzinfo=timezone.utc)
UNIVERSE_WINDOW_END = datetime(2023, 12, 18, tzinfo=timezone.utc)  # exclusive; == train_end
UNIVERSE_N = 25

# --------------------------------------------------------------- clocks ----
# design §0: H1, H4, D1 — all three PRIMARY (AMENDMENT-A2).

CLOCKS: dict[str, dict] = {
    "H1": {"minutes": 60, "truncate": "1h", "min_minutes": 48, "warmup_bars": 120},
    "H4": {"minutes": 240, "truncate": "4h", "min_minutes": 192, "warmup_bars": 60},
    "D1": {"minutes": 1440, "truncate": "1d", "min_minutes": 1000, "warmup_bars": 60},
}
CLOCK_ORDER = ("H1", "H4", "D1")

# design §0 warm-up: ">= max(60 D1 bars, 60 H4 bars, 120 H1 bars) of complete history".
# The calendar-dominant term is 60 D1 bars = 60 days; applied to every clock in addition
# to the per-clock bar count above.
WARMUP_DAYS = 60

# ---------------------------------------------------------- estimation ----
# design §6.2 OOS protocol.

INITIAL_FIT_FRACTION = 0.40      # first 40% of the symbol's scored DESIGN origins
REFIT_CADENCE = "monthly"        # walk-forward re-fit each calendar month
EWMA_LAMBDA = 0.94               # design §4 V-LEVEL
RIDGE_ALPHA = 1.0                # design §4 V-LEVEL
RV_WINDOW = 20                   # design §3.2 rv20
HAR_MEANS = (6, 24)              # design §4 V-PERSIST rv20_mean_6 / rv20_mean_24
PERSIST_LAGS = (1, 2, 3, 5)      # design §4 V-PERSIST autocorr lags

# V-LEVEL primary forecast used for band assignment / tripwire metric.
# design §4 lists "OLS and ridge (alpha=1.0)"; ridge carries the pinned hyper-parameter.
# Declared before any outcome was read; OLS + EWMA reported alongside, never hidden.
V_LEVEL_PRIMARY_MODEL = "ridge"
V_LEVEL_PRIMARY_TARGET = "target_abs_oo"
V_LEVEL_FEATURES = ("rv20", "ewma_vol", "parkinson", "gk")

# V-REGIME rolling-median split window (design §4 "rolling median split"; window not pinned
# in the design -> set equal to the per-clock warm-up bar count, the design's own scale).
REGIME_MEDIAN_WINDOW = {c: CLOCKS[c]["warmup_bars"] for c in CLOCK_ORDER}

# V-CLOCK session buckets (design §4): UTC 0-8 / 8-16 / 16-24.
SESSION_EDGES = (0, 8, 16, 24)

# ---------------------------------------------------------- inference ----
# design §6.2.

BOOT_BLOCKS = (1, 3, 7)                       # date-block lengths (days)
BOOT_SEEDS = (101, 211, 307, 401, 503)
BOOT_RESAMPLES = 10_000                       # design: 5k-10k, 10k preferred
# Band assignment uses the worst case over the (block x seed) grid: lowest CI low,
# highest CI high. Conservative and immune to block/seed cherry-picking (L-20 / INFR-004).
BOOT_CI_ALPHA = 0.05

# ---------------------------------------------------------- controls ----
# design §5.

SHUFFLE_SEEDS = tuple(range(101, 301))            # 200 seeds, CIRCULAR_SHIFT
DERANGE_SEEDS_MIN = tuple(range(31000, 31200))    # 200 seeds, DERANGEMENT
DERANGE_SEEDS_FULL = tuple(range(31000, 33000))   # 2000-seed upgrade if wall-clock < 30 min
PLANT_RANK_CORR = 0.25                            # bite/MDE plant, both controls

# ------------------------------------------------------------- bands ----
# design §6.3 interpretation bands (labels, NEVER gates).

BAND_IC_SUPPORTED = 0.10
BAND_IC_WASH_ABS = 0.05
BAND_IC_CONTRADICTED = -0.05
BAND_GAP_SUPPORTED_BPS = 15.0
BAND_GAP_WASH_BPS = 10.0
BAND_GAP_CONTRADICTED_BPS = -15.0
MIN_EFFECTIVE_DATES = 40
MDE_IC_CEILING = 0.10
MDE_GAP_CEILING_BPS = 15.0
MDE_IC_CONST = 1.5           # design §6.5: MDE(IC) ~ 1.5/sqrt(n_eff), n_eff ~ unique dates
POOLED_SIGN_AGREEMENT = 0.60

# ------------------------------------------------ cost disclosure ----
# design §0 SPREAD-COST-DISCLOSURE (chapter-05/06 no-spread amendment).

SPREAD_COST_DISCLOSURE = {
    "spread_cost_status": "UNAVAILABLE_NOT_CHARGED",
    "spread_rt_bps": None,
    "cost_scope": "PARTIAL_FEES_FUNDING_ONLY",
    "implication": (
        "any optional cost overlay understates true cost; "
        "no fully-net/tradable/deployable claim"
    ),
    "prohibited_claims": ["fully-net", "cost-complete", "tradable", "deployable"],
}

UNIT_PIN = {
    "primary_magnitude_target": "abs_oo = 1e4 * |O_{t+1}/O_t - 1| in bps on the decision clock",
    "rv_objects": "dimensionless (log-return scale); not annualised",
    "money_overlay_normaliser": "none - target already in bps; no ATR divisor",
}

# --------------------------------------------- interpretation notes ----

INTERPRETATION_NOTES = [
    {
        "id": "IN-1",
        "clause": "design §6.2 'first 40% DESIGN for initial fit'",
        "ambiguity": (
            "Calendar reading (first 40% of the DESIGN band = up to 2022-03-01) is empty for "
            "every symbol: the catalog carries a trailing 4-year history cap, so the earliest "
            "1m bar for all but MATICUSDT is 2022-07-15. The calendar reading yields no initial "
            "fit window and therefore no OOS forecast at all."
        ),
        "resolution": (
            "Initial fit = first 40% of each symbol x clock's own scored DESIGN origins "
            "(time-ordered); walk-forward monthly expanding re-fit thereafter, as specified."
        ),
        "weakens_clause": False,
    },
    {
        "id": "IN-2",
        "clause": "design §6.2 'chronological DESIGN thirds (equal elapsed time)'",
        "ambiguity": (
            "Literal calendar thirds of [2021-06-29, 2023-03-01) put the first third entirely "
            "before the catalog history cap (empty) for all symbols except MATICUSDT."
        ),
        "resolution": (
            "BOTH are computed and reported: thirds_calendar (literal, per design) and "
            "thirds_sample (equal elapsed time over the symbol x clock's own scored span). "
            "The literal read is never dropped."
        ),
        "weakens_clause": False,
    },
    {
        "id": "IN-3",
        "clause": "design §5 CONTROL TIME-SHUFFLE-PREDICTORS",
        "ambiguity": (
            "Whether the shuffled features must be re-fitted through the walk-forward model."
        ),
        "resolution": (
            "The OOS prediction series is a deterministic function of the feature rows, so a "
            "circular shift of the prediction series relative to the fixed target series is "
            "exactly the specified 'features no longer aligned to true past of the target' "
            "with the model held frozen. Applied at 200 seeds; the +0.25 rank-correlation "
            "plant is destroyed under the same operation as the bite check."
        ),
        "weakens_clause": False,
    },
    {
        "id": "IN-4",
        "clause": "design §6.3 bands / §6.2 block bootstrap",
        "ambiguity": "Which (block length, seed) CI assigns the band.",
        "resolution": (
            "Worst case: ci_low = min over the 3 blocks x 5 seeds, ci_high = max. The full "
            "15-cell grid is emitted (block_sensitivity + ci_low_seed_range, L-20)."
        ),
        "weakens_clause": False,
    },
    {
        "id": "IN-5",
        "clause": "design §3.3 'target = next bar'",
        "ambiguity": "Behaviour when the next COMPLETE bar is not the adjacent clock slot.",
        "resolution": (
            "The literal design text is implemented (next complete bar). A "
            "'next_contiguous' flag is emitted per origin and the contiguous fraction is "
            "disclosed per cell; no rows are dropped."
        ),
        "weakens_clause": False,
    },
    {
        "id": "IN-6",
        "clause": "design §4 V-REGIME-HMM 'on r or rv20'",
        "ambiguity": "Which sequence the 2-state Gaussian HMM is fitted to.",
        "resolution": (
            "Fitted to the clock log-return series r with state-specific (mu, sigma^2); "
            "HIGH = the larger-sigma state. Standard 2-state volatility-regime formulation "
            "and the RAW §5.1 'HMM on returns or RV' wording."
        ),
        "weakens_clause": False,
    },
    {
        "id": "IN-7",
        "clause": "design §3.2 vs §3.3 — target indexing",
        "ambiguity": (
            "§3.2 writes abs_oo_i = 1e4*|O_{i+1}/O_i - 1| and calls it the target for origin i, "
            "but O_{i+1} is the traded price AT the origin instant slot_end_i, so that quantity "
            "is already known at origin i. §3.3 says 'Target = next bar's abs_oo'."
        ),
        "resolution": (
            "The causal reading is forced by §3.3 and by §7.4 ('targets use next bar only'): the "
            "target for origin i is the move realised over bar i+1, entered at O_{i+1}, i.e. "
            "target_abs_oo_i = 1e4*|O_{i+2}/O_{i+1} - 1|. The origin-known variant is still "
            "emitted per row as oo_move for disclosure."
        ),
        "weakens_clause": False,
    },
    {
        "id": "IN-8",
        "clause": "design §5 TRIPWIRE TARGET-FUTURE-DESTROY — destroy form adjudicated",
        "ambiguity": (
            "§5 pins the tripwire destroy as 'another symbol-month deranged target (same as "
            "label derangement)'. Adjudicating COLLAPSE on that block-restricted form is "
            "self-defeating: deranging inside a calendar month cannot remove the between-month "
            "component, so its null median RISES with the strength of the true relationship "
            "(measured: block null median 0.109 vs live 0.259) and the strongest cells are "
            "flagged as leaks."
        ),
        "resolution": (
            "DEVIATION, NOT A NEUTRAL READING — see the DEVIATIONS block below. Resolved by "
            "OPERATOR DECISION 2026-07-23: the future-destroy read is demoted to a REPORT "
            "LAYER with no pass field (INFR-016 / L-32) rather than re-specified as a hard "
            "gate, because no outcome-side destroy can detect look-ahead and a green gate "
            "would report absence of evidence as evidence of absence. Both destroy forms are "
            "still run at 2000 seeds and reported per cell."
        ),
        "weakens_clause": True,
        "see": "DEVIATIONS[0]",
    },
    {
        "id": "IN-9",
        "clause": "design §6.3 UNPOWERED clause",
        "ambiguity": (
            "The clause fires on the PROSPECTIVE MDE (>0.10 => needs >=225 unique dates), which "
            "the realised DESIGN sample cannot clear: the catalog's trailing 4-year history cap "
            "leaves a median of 99-102 unique dates per DESIGN cell."
        ),
        "resolution": (
            "The literal design label is emitted as band_label and is the one that counts. A "
            "disclosure companion band_label_detected (UNPOWERED only when the observed effect "
            "is below its own detection floor) is emitted in a separate column. No cell is "
            "dropped or re-labelled. Which label rule and which band the §6.4 recommendation is "
            "computed from is an OPERATOR decision (QA F-4), not a code default."
        ),
        "weakens_clause": False,
    },
]

# ------------------------------------------------------------- deviations ----
# Recorded deviations from the frozen design. A deviation is NOT an interpretation: it
# changes what a clause tests. Each needs a dated amendment in design.md and operator
# sign-off (L-23 directional accounting).

DEVIATIONS = [
    {
        "id": "DEV-1",
        "clause": "design §5 TRIPWIRE TARGET-FUTURE-DESTROY",
        "pinned": (
            "HARD tripwire, collapse adjudicated on the symbol x calendar-month "
            "block-restricted derangement"
        ),
        "implemented": (
            "REPORT LAYER with no pass field (observed / ideal / interpretation), reporting "
            "both the unrestricted and the block-restricted destroy per cell"
        ),
        "direction": "LOOSER (a hard gate was removed)",
        "made_after_seeing_outcomes": True,
        "rationale": (
            "The pinned block form retains the between-month component by construction, so its "
            "null median scales with the true relationship; adjudicating collapse on it failed "
            "33/90 cells and would have flagged the strongest cells as leaks."
        ),
        "known_limitation": (
            "The replacement gate is effectively unfailable: E[Spearman(pred, deranged y)] = 0 "
            "for any fixed pred, so it is a null-centring sanity check, NOT a look-ahead leak "
            "test. Restated: "
            "fixed pred, so it is a null-centring sanity check, NOT a look-ahead leak test. No "
            "target-side destroy can detect look-ahead. The operative non-vacuity device for "
            "this screen is the predictor-side CIRCULAR_SHIFT control plus the construction-"
            "level causality asserts (design §7.4)."
        ),
        "operator_decision": (
            "2026-07-23 — operator chose 'demote it to a report layer' over (a) signing an "
            "amendment that kept a hard gate, and (b) reverting to the frozen block-restricted "
            "gate that would have failed 33/90 cells for an artifact of its own destroy form."
        ),
        "design_md_amendment": "AMENDMENT-T1 (design.md §5), dated 2026-07-23",
        "operator_sign_off": "RECORDED 2026-07-23",
        "consequence": (
            "SPDR-012 ships with NO hard leak gate. The hard integrity surface is the "
            "construction-level causality checks (§7.1/7.1b/7.2/7.3/7.3b/7.4/7.5), which an "
            "independent fresh-context QA pass re-derived and confirmed. The predictor-side "
            "CIRCULAR_SHIFT control is the operative non-vacuity device."
        ),
    },
]

# --------------------------------------------------- prohibited claims ----

PROHIBITED_CLAIMS = [
    "tradable", "deployable", "fully-net", "cost-complete",
    "direction", "combination", "family status change",
]
