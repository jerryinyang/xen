"""SPDR-013 frozen constants — every value traces to design.md / checkpoint-017 / RAW.

Direction expectancy (SMA + ZigZag) under frozen TF capture geometry. TRAIN-only SPDR screen.

DEVIATIONS: NONE authorised. Ambiguity resolutions that weaken no clause live in
``INTERPRETATION_NOTES`` (IN-1..). All are reproduced in results/integrity_selfcheck.json and
results/compliance_trace.md.
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
# design §0 scope fence. DESIGN primary; CONFIRM one TRAIN-internal verify; TEST/holdout never.

DESIGN_START = datetime(2021, 6, 29, 6, 53, tzinfo=timezone.utc)
DESIGN_END = datetime(2023, 3, 1, tzinfo=timezone.utc)       # exclusive
CONFIRM_START = DESIGN_END
CONFIRM_END = datetime(2023, 12, 18, tzinfo=timezone.utc)    # exclusive == train_end_utc
TEST_START = CONFIRM_END            # never read
HOLDOUT_START = datetime(2025, 1, 8, tzinfo=timezone.utc)    # never read

BANDS = {
    "DESIGN": (DESIGN_START, DESIGN_END),
    "CONFIRM": (CONFIRM_START, CONFIRM_END),
}
PRIMARY_BAND = "DESIGN"   # design §0: DESIGN primary; CONFIRM = one TRAIN-internal verify

NS = 1_000_000_000

# ------------------------------------------------------------ universe ----
# design §0.1 UNIVERSE-PIN (AMENDMENT-U1). Recomputed at run time and asserted equal.

UNIVERSE_METRIC = "sum(close*volume) over 1m bars"
UNIVERSE_WINDOW_START = datetime(2023, 11, 18, tzinfo=timezone.utc)
UNIVERSE_WINDOW_END = datetime(2023, 12, 18, tzinfo=timezone.utc)   # exclusive; == train_end
UNIVERSE_N = 25

# --------------------------------------------------------------- clocks ----
# design §0 / §3.1 / §4: H1 and M15 — both mandatory first-pass.

CLOCKS: dict[str, dict] = {
    "H1": {"minutes": 60, "truncate": "1h", "min_minutes": 48,
           "time_cap_bars": 48, "warmup_bars": 120},
    "M15": {"minutes": 15, "truncate": "15m", "min_minutes": 12,
            "time_cap_bars": 192, "warmup_bars": 240},
}
CLOCK_ORDER = ("H1", "M15")

# --------------------------------------------------------- indicators ----
# design §3.1 / §3.2 / §3.3.

ATR_PERIOD = 14                    # Wilder ATR(14), per-clock, lagged [t-1]
SMA_PERIODS = (14, 25, 50)         # design §3.2 all mandatory; 200-SMA FORBIDDEN
SMA_ANGLE_MODES = ("off", "on")    # design §3.2 both mandatory
SMA_ANGLE_LOOKBACK = 3             # |SMA_t - SMA_{t-3}|
SMA_ANGLE_THRESHOLD_ATR = 0.15     # design §3.2: >= 0.15 else flat
ZZ_REVERSAL_ATR = 2.0              # design §3.3 reversal threshold 2.0 x ATR(14)

# --------------------------------------------------- capture geometry ----
# design §4 (TF — frozen, both arms). Cut losers quickly; let winners run.

INITIAL_STOP_ATR = 1.5             # adverse excursion >= 1.5 x ATR[entry-1]
TRAIL_TRIGGER_ATR = 1.0            # favourable open-to-open excursion >= 1.0 x ATR
TRAIL_LOCK_ATR = 0.5               # trail to entry + 0.5 x ATR x side
TRAIL_RATCHET_ATR = 2.0            # then ratchet by HWM - 2.0 x ATR (long) / + (short)
# time_cap_bars: H1 48 (~48h), M15 192 (~48h) — in CLOCKS above.

# --------------------------------------------------- exit modes (A3) ----
# AMENDMENT-A3 (operator-directed 2026-07-23): the frozen §4 stack is the `combined` arm; each
# termination rule is ALSO isolated so its contribution is diagnosable (exploratory screen). For
# D-ZZ, `signalflip` == the full structural leg (hold open-after-confirm -> open-after-next-confirm,
# no risk cuts). Non-exhaustive of every subset by design intent — the four single-rule isolations
# + the combined stack are the operator-specified set.

EXIT_MODES: dict[str, dict] = {
    "combined":   {"use_stop": True,  "use_trail": True,  "use_time": True,  "use_signalflip": True},
    "stop":       {"use_stop": True,  "use_trail": False, "use_time": False, "use_signalflip": False},
    "trail":      {"use_stop": False, "use_trail": True,  "use_time": False, "use_signalflip": False},
    "time":       {"use_stop": False, "use_trail": False, "use_time": True,  "use_signalflip": False},
    "signalflip": {"use_stop": False, "use_trail": False, "use_time": False, "use_signalflip": True},
}
# matched-random uses the arm's stop geometry (time cap is always its terminal — random has no
# signal): map each exit mode to (use_stop, use_trail) for the batch engine.
EXIT_MODE_RANDOM_GEOM = {m: (v["use_stop"], v["use_trail"]) for m, v in EXIT_MODES.items()}
ZZ_STRUCTURAL_EXIT_MODE = "signalflip"   # D-ZZ__exit-signalflip IS the structural-leg arm

# --------------------------------------------------------------- costs ----
# design §4 partial cost. Fee RT 11.0 taker (Bybit), funding 1.0 bps/stamp, allowance 0/2/5.
# Fee + funding via xen.evaluation (no local accounting primitive); allowance subtracted here.

FEE_RT_BPS = 11.0                            # asserted == 2 * taker_bps_per_side (5.5)
FUNDING_BPS_PER_STAMP = 1.0                  # discrete 00:00/08:00/16:00 UTC stamps
ALLOWANCE_SENSITIVITY = (0.0, 2.0, 5.0)      # design §4 report 0/2/5
ALLOWANCE_GOVERNING = 2.0                    # design §4 governing 2.0 bps
COST_FLOOR_BPS = 13.5                        # design §7.2 informative: 11 + ~0.5 + 2

SPREAD_COST_DISCLOSURE = {
    "spread_cost_status": "UNAVAILABLE_NOT_CHARGED",
    "spread_rt_bps": None,
    "cost_scope": "PARTIAL_FEES_FUNDING_ONLY",
    "implication": (
        "partial_net understates true cost; reported expectancy overstated vs full cost"
    ),
    "prohibited_claims": ["fully-net", "cost-complete", "tradable", "deployable"],
}

UNIT_PIN = {
    "gross_signed_oo_bps": "direction * (exit_open/entry_open - 1) * 1e4",
    "atr_object": (
        "per-clock Wilder ATR(14)[t-1] in price; stops in price space from that clock's own "
        "ATR (design §3.1 'never mix H1 ATR into M15 stops or vice versa'; §4 UNIT-PIN '1h' "
        "is the H1 exemplar — see IN-1)"
    ),
    "expectancy_unit": "mean partial_net_bps per episode (bps of notional)",
}

# --------------------------------------------------------- inference ----
# design §7.1.

BOOT_BLOCKS = (1, 3, 7)                       # date-block lengths (days)
BOOT_SEEDS = (101, 211, 307, 401, 503)
BOOT_RESAMPLES = 10_000
BOOT_CI_ALPHA = 0.05
THIRDS_SIGN_MIN = 2                           # sign in >= 2/3 DESIGN thirds for SUPPORTED

# ----------------------------------------------------------- bands §7.2 ----
# labels only, never gates.

BAND_SUPPORTED_BPS = 5.0
BAND_WASH_ABS_BPS = 5.0
BAND_CONTRADICTED_BPS = -5.0
UNPOWERED_MIN_EPISODES = 80
UNPOWERED_MDE_CEILING_BPS = 10.0
UNPOWERED_MIN_DATES = 30

# --------------------------------------------------------- controls §6 ----

DERANGE_SEEDS = tuple(range(31000, 31200))         # >=200 DIRECTION-DERANGEMENT
MATCHED_RANDOM_SEEDS = tuple(range(41000, 41200))  # >=200 MATCHED-RANDOM-ENTRY
TRIPWIRE_SEEDS = tuple(range(52000, 52200))        # >=200 PATH-FUTURE-DESTROY
PLANT_EXPECTANCY_BPS = 20.0                        # bite/MDE plant, both controls
PLANT_TRIPWIRE_BPS = 30.0                          # design §6 tripwire synthetic plant

# --------------------------------------------- interpretation notes ----

INTERPRETATION_NOTES = [
    {
        "id": "IN-1",
        "clause": "design §4 UNIT-PIN 'ATR object: 1h Wilder ATR(14)[t-1]' vs §3.1 "
                  "'ATR of that clock ... never mix H1 ATR into M15 stops or vice versa'",
        "ambiguity": (
            "The §4 UNIT-PIN block names a '1h' ATR object, but §3.1 explicitly forbids mixing "
            "H1 ATR into M15 stops and §3.3 pins ZZ capture to 'ATR and bars native to that "
            "clock'. The §4 time-cap row also splits 48 (H1) / 192 (M15) native bars."
        ),
        "resolution": (
            "Each clock uses its OWN Wilder ATR(14)[t-1] for stops/trail/ZZ threshold. The §4 "
            "UNIT-PIN '1h' is read as the H1 exemplar of a block otherwise written in H1 terms; "
            "the explicit §3.1 'never mix' clause governs. Forced by the more specific clause; "
            "no clause is weakened (an H1-only ATR would itself VIOLATE §3.1 for the M15 arm)."
        ),
        "weakens_clause": False,
    },
    {
        "id": "IN-2",
        "clause": "design §4 initial-stop / winner-trail high-water-mark reference",
        "ambiguity": (
            "§4 defines the winner trail off 'favorable open-to-open excursion' and a "
            "'high-water mark' but does not state whether the HWM is measured on bar opens or "
            "bar highs/lows."
        ),
        "resolution": (
            "HWM = running extreme of bar OPENS (long: max open; short: min open), consistent "
            "with the explicit 'open-to-open excursion' trigger and the programme open-to-open "
            "discipline. The stop LEVEL is thus known at each bar open (causal); stop-TOUCH "
            "detection still uses that bar's high/low per §4. Conservative (a high/low HWM would "
            "trail tighter/earlier); no clause weakened."
        ),
        "weakens_clause": False,
    },
    {
        "id": "IN-3",
        "clause": "design §4 stop-touch exit price",
        "ambiguity": (
            "§4: 'exit next bar open after stop touch on high/low (conservative: if bar trades "
            "through stop, exit that bar's open if open already beyond stop, else next open)'."
        ),
        "resolution": (
            "Per bar j after entry, with stop level S (known at open j from data <= open j-1 + "
            "entry): if open_j is already beyond S -> exit at open_j; elif the bar's low(long)/"
            "high(short) breaches S -> exit at open_{j+1}. Pure open-to-open, no intrabar fill "
            "at the stop price. Literal reading of §4."
        ),
        "weakens_clause": False,
    },
    {
        "id": "IN-4",
        "clause": "design §0 band precedence (DESIGN primary; CONFIRM one TRAIN-internal verify)",
        "ambiguity": "Which band drives the primary bands/recommendation.",
        "resolution": (
            "DESIGN is the primary band for labels and the §7.3 recommendation; CONFIRM is "
            "computed and reported as the single TRAIN-internal verification (both emitted per "
            "cell, neither dropped). History cap: catalog 1m data starts 2022-07-15, so the "
            "DESIGN band is effectively [2022-07-15, 2023-03-01); sparse cells -> UNPOWERED, "
            "never silent-dropped (design §0.1)."
        ),
        "weakens_clause": False,
    },
]

DEVIATIONS: list[dict] = [
    {
        "id": "DEV-1",
        "clause": "design §6 TRIPWIRE PATH-FUTURE-DESTROY / §11 'tripwire collapse' HARD",
        "pinned": "HARD future-destroy gate on expectancy_partial of D-SMA14; a cell whose live "
                  "expectancy survives above the destroyed-null p95 fails integrity.",
        "implemented": "INFORMATIVE report layer — computed and reported per D-SMA14 cell "
                       "(live/null/collapse/plant + an applicability flag), but NOT gating "
                       "integrity all_pass (no PASS/FAIL effect).",
        "direction": "LOOSER (a hard gate is removed)",
        "made_after_seeing_outcomes": True,
        "rationale": (
            "An outcome-side path-destroy on a mean episode-P&L direction object cannot separate "
            "a look-ahead leak from a genuine CAUSAL timing association: a causal trend rule that "
            "avoids the worst random paths reads as 'surviving' the destroy even when its "
            "expectancy is negative/cost-losing (observed: SOL D-SMA14 H1 CONFIRM live -2.23 vs "
            "destroyed-null p95 -3.20, all 12 D-SMA14 live values negative — no positive surviving "
            "edge). Same class SPDR-012 hit (IN-8/DEV-1). Applicability logic retained: the "
            "future-destroy is only a hard-style CONCERN for a cell that CLAIMS a positive edge "
            "(SUPPORTED or live>0); for non-positive cells it is disclosure. No cell that claims "
            "positive edge may be waved through — that flag is reported."
        ),
        "known_limitation": (
            "No outcome-side destroy can prove absence of look-ahead. Causality for SPDR-013 rests "
            "on construction asserts (entry strictly after the signal bar; ATR[t-1]; TRAIN fence), "
            "engine parity (sequential==batch, max_rel 0.0), and the predictor-side controls "
            "(DIRECTION-DERANGEMENT sides fixed-point-free; MATCHED-RANDOM-ENTRY timing)."
        ),
        "operator_decision": (
            "2026-07-23 — operator directed 'follow the objectively-right steps but demote to "
            "informative only, not gating or effectual for PASS/FAIL, just like in SPDR-012', with "
            "the applicability refinement (HARD only when a positive edge is claimed)."
        ),
        "design_md_amendment": "AMENDMENT-T1 (design.md §6/§11), dated 2026-07-23",
        "operator_sign_off": "RECORDED 2026-07-23",
        "consequence": (
            "SPDR-013 integrity all_pass no longer depends on the future-destroy tripwire. The "
            "hard surface is fence + causal construction + engine parity + universe pin + golden "
            "traces. The tripwire numbers remain emitted per D-SMA14 cell in results/controls.json."
        ),
    },
]

AMENDMENTS: list[dict] = [
    {
        "id": "AMENDMENT-A3",
        "clause": "design §3 arm set / §4 single combined capture geometry",
        "change": (
            "Add EXIT-MODE decomposition: every direction signal (6 D-SMA cells + D-ZZ) is run "
            "under 5 exit modes {combined, stop, trail, time, signalflip} on both clocks and both "
            "bands. The frozen §4 stack is the `combined` arm (unchanged). D-ZZ `signalflip` is "
            "the full STRUCTURAL-LEG arm (hold open-after-confirm -> open-after-next-confirm, no "
            "stop/trail/time)."
        ),
        "direction": "NEUTRAL (pre-outcome completeness for the new arms; exploratory screen)",
        "operator_decision": "2026-07-23 — operator directed isolating each exit rule as its own "
                             "arm plus the ZZ structural-leg arm, to diagnose exit contribution.",
        "operator_sign_off": "RECORDED 2026-07-23",
    },
    {
        "id": "AMENDMENT-E1",
        "clause": "design §5 expectancy decomposition (mean-only)",
        "change": "Report MEDIAN alongside MEAN for avail_when_right / damage_when_wrong / "
                  "expectancy_gross / expectancy_partial so fat tails are visible (mean-vs-median "
                  "gap). Headline band still uses mean expectancy_partial (§7.2). Right/wrong stays "
                  "the trade GROSS-P&L split (§5); ZZ magnitude/path_noise features remain "
                  "forecasting-only, never the avail/damage object.",
        "direction": "NEUTRAL (disclosure enrichment)",
        "operator_decision": "2026-07-23 — operator directed reporting mean and median.",
        "operator_sign_off": "RECORDED 2026-07-23",
    },
]

PROHIBITED_CLAIMS = [
    "tradable", "deployable", "fully-net", "cost-complete",
    "combination", "SPDR-014", "family status change",
]
