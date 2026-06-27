"""EXP-083 — TRAIN-only candidate screen behind the separability gate (Phase 018, CF-CAPGEO-001).

HYP-004a (D0-amendment-001 split). For every member substrate-cell (4 frozen substrates x 46
EXP-080-READY instrument x domain cells) this applies the 3 frozen derived exits (D1/D2/D3, via the
sha256-pinned ``xen.capgeo_exits.derive_barriers``) **and** the full enumerated benchmark exit grid to
the frozen-entry held positions on the **TRAIN region only**, then runs the cheap **G-018a** gross screen
(expectancy + median + matched-random excess) and the binding **separability gate** (S1 attribution ∧ S2
tail non-residual). It emits, freezes, and **sha256-hash-pins** the surviving valid-candidate set + the
pre-declared Holm rule as the binding hand-off artifact for the deferred counted-read confirmation
(EXP-084). **No TEST stratum is sliced, no holdout touched, 0 counted reads, frozen referee suite not
invoked here.** Verdict in {SCREEN_DELIVERED (>=1 survivor), ALL_CANDIDATES_FAIL (empty set)}.

Cost treatment: GROSS (operator decision 2026-06-22); cost layer deferred to a conditional follow-up.
ASS is a non-binding disclosure overlay (G-017). All returns on real prices, ATR units; per-stratum
default (no pooling as a binding statistic, LESSON-001).

Read region: TRAIN sub-split ``[0, int(analysis_rows*0.7))`` of the first-70% analysis set (== EXP-081's
region). The analysis-TEST stratum and the final-30% global holdout are never sliced.

Run:
    cd python && python experiments/EXP-083/code/run_experiment.py
    # optional smoke subset:  EXP083_MAX_CELLS=3 EXP083_N_BOOT=2000 python experiments/EXP-083/code/run_experiment.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                       # noqa: E402
import polars as pl                      # noqa: E402
import seaborn as sns                    # noqa: E402
from tqdm.auto import tqdm               # noqa: E402

import xen.capgeo_exits as capgeo_exits  # noqa: E402  (sha256-pinned derivation; asserted at runtime)
from xen.capgeo_exits import CellStats, derive_barriers  # noqa: E402
from xen.capgeo_screen import (          # noqa: E402
    DELTA,
    EVENT_FLOOR,
    N_S2_FLOOR,
    TAU_TAIL,
    GateRow,
    Resolution,
    gate_row_dict,
    m_cell_margin,
    one_sided_lo,
    resolve_fixed_horizon,
    resolve_partial_two_leg,
    resolve_static_barrier,
    resolve_struct_trail,
    resolve_trailing,
    s2_tail_residual,
    two_sample_diff_lo,
)
from xen.capgeo_geometry import DIP_ALPHA, K_TAIL  # noqa: E402
from xen.capgeo_substrates import (      # noqa: E402
    ATR_PERIOD,
    SUB_AVWAP,
    SUB_HARAMI_PARTIAL_V2A,
    SUB_RANDOM,
    _ma_segment_moves,
    _real_ohlc,
    avwap_entries,
    harami_native_entries,
    random_entries,
)
from xen.domain_bars import build_domain_bars   # noqa: E402
from xen.expectancy import (             # noqa: E402
    adaptive_time_caps_by_epoch,
    live_in_progress_state,
)
from xen.favourable_targets import volume_profile_levels  # noqa: E402
from xen.zigzag import wilder_atr        # noqa: E402

LOGGER = logging.getLogger("EXP-083")

# --------------------------------------------------------------------------- #
# Path setup + upstream reuse
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-083"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
EXPERIMENT_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
_VAL005_CODE = PROJECT_ROOT / "python" / "experiments" / "VAL-005" / "code" / "run_experiment.py"
_EXP080_READY_MAP = PROJECT_ROOT / "python" / "experiments" / "EXP-080" / "results" / "ready_map.csv"
_EXP081_SUMMARY = PROJECT_ROOT / "python" / "experiments" / "EXP-081" / "results" \
    / "substrate_cell_summary.parquet"
_EXP081_META = PROJECT_ROOT / "python" / "experiments" / "EXP-081" / "results" / "run_metadata.json"
_EXP082_META = PROJECT_ROOT / "python" / "experiments" / "EXP-082" / "results" / "run_metadata.json"
_DERIVE_PIN = "34d03f45"   # EXP-082-pinned derive_barriers sha256 prefix (full asserted below)


def _load_val005():
    """Import the VAL-005 module (import-safe: constants/functions only, main guarded)."""
    spec = importlib.util.spec_from_file_location("val005_capgeo_083", _VAL005_CODE)
    if spec is None or spec.loader is None:                       # pragma: no cover - defensive
        raise ImportError(f"Could not load VAL-005 from {_VAL005_CODE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------- #
# Constants (frozen at G0/D9; seeds + bootstrap budgets recorded in run_metadata.json)
# --------------------------------------------------------------------------- #
SEED_RANDOM = 20260621             # matched-random control master seed (== EXP-080/081)
SEED_BOOT = 20260622               # bootstrap master seed (D10)
DOMAIN_LABEL = {15: "15m", 60: "1h", 240: "4h"}
DOMAIN_ORDER = ["15m", "1h", "4h"]
# C1 audit fix (2026-06-22): the two registered harami substrates (PARTIAL-V2A / V2A-ADVNONE) share
# ONE byte-identical entry population and differ only by a downstream exit arm. This screen applies the
# full candidate surface to every substrate, so the two harami substrates were fully redundant — scored
# on identical returns but against *different* random nulls (control seeded by substrate index), which
# let control-draw noise flip a survivor's valid flag between them. They are deduped here to a single
# canonical harami stratum (3 screened substrates, not 4); `_SUMMARY_SUBSTRATE` maps it back to the
# entry-identical PARTIAL-V2A EXP-081 summary row for the cell statistics.
SUB_HARAMI_V2A = "SUB-HARAMI-V2A"
SUBSTRATE_ORDER = [SUB_AVWAP, SUB_HARAMI_V2A, SUB_RANDOM]
_SUMMARY_SUBSTRATE = {SUB_AVWAP: SUB_AVWAP, SUB_HARAMI_V2A: SUB_HARAMI_PARTIAL_V2A,
                      SUB_RANDOM: SUB_RANDOM}
COVERAGE_EXCLUDED = {("US500", "4h"), ("JP225", "4h")}
# Bootstrap budgets — binding edge-call / CI resamples default to the frozen 10_000 (scope §Frozen
# Constants); EXP083_N_BOOT lets a manual run lower it for tractability (value recorded in metadata).
N_BOOT = int(os.environ.get("EXP083_N_BOOT", "10000"))
NULL_REPS = int(os.environ.get("EXP083_NULL_REPS", "200"))   # m_cell synthetic-null replications
N_BOOT_NULL = int(os.environ.get("EXP083_N_BOOT_NULL", "1000"))  # inner bootstrap for m_cell
MAX_CELLS = int(os.environ.get("EXP083_MAX_CELLS", "0"))     # >0 => smoke subset of member cells
# Frozen benchmark surface (enumerated; conventional / data-anchored — scope §Candidate surface)
RR_RATIOS = (1.0, 1.5, 2.0, 3.0)
TRAIL_ATR_K = (1.0, 2.0, 3.0)
VP_BIN_FRAC = 0.25                 # VP bin width = VP_BIN_FRAC * ATR(entry-median) (real prices)


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class PathInputs:
    """Per-substrate-cell real-OHLC forward-path inputs for exit resolution (TRAIN region)."""

    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    volume: np.ndarray | None
    n_bars: int
    entry_idx: np.ndarray
    direction: np.ndarray
    atr_entry: np.ndarray
    cap: np.ndarray            # adaptive time cap (bars) per kept event


# --------------------------------------------------------------------------- #
# Pure helpers — entries / directions / adaptive cap (mirror EXP-080/081 plumbing)
# --------------------------------------------------------------------------- #
def _segment_state(ohlc: dict, entry_idx: np.ndarray):
    seg = _ma_segment_moves(ohlc)
    if entry_idx.shape[0] == 0 or seg["confirm_epoch"].shape[0] == 0:
        return seg, None
    state = live_in_progress_state(
        ohlc["epoch"][entry_idx], ohlc["close"][entry_idx], seg["confirm_epoch"],
        seg["end_price"], seg["end_epoch"], seg["direction"])
    return seg, state


def _harami_random_direction(entry_idx: np.ndarray, state) -> np.ndarray:
    """Per-event regime direction (live in-progress MA-segment move); 0 = warmup-equivalent."""
    m = int(entry_idx.shape[0])
    if m == 0 or state is None:
        return np.zeros(m, dtype=np.int64)
    rd = state.rd.astype(np.int64).copy()
    rd[~state.valid] = 0
    return rd


def _avwap_directions(frame: pl.DataFrame, instrument: str, domain: str, es) -> np.ndarray:
    """AVWAP per-event direction aligned to the EntrySet trigger order."""
    from xen.avwap import (
        BAND_MULTIPLIER, FAST_MA, SLOW_MA, VOLUME_EXPONENT, generate_avwap_events)
    if int(es.entry_idx.shape[0]) == 0:
        return np.empty(0, dtype=np.int64)
    ev = generate_avwap_events(frame, instrument=instrument, domain=domain,
                               band_multiplier=BAND_MULTIPLIER, volume_exponent=VOLUME_EXPONENT,
                               fast_ma=FAST_MA, slow_ma=SLOW_MA).events
    trig = ev.get_column("trigger_time").dt.epoch("s").to_numpy().astype(np.int64)
    direction = ev.get_column("direction").to_numpy().astype(np.int64)
    return direction[np.argsort(trig, kind="stable")]


def _adaptive_cap(entry_idx: np.ndarray, ohlc: dict, seg: dict) -> tuple[np.ndarray, np.ndarray]:
    if entry_idx.shape[0] == 0 or seg["confirm_epoch"].shape[0] == 0:
        n = int(entry_idx.shape[0])
        return np.zeros(n, dtype=np.int64), np.ones(n, dtype=bool)
    return adaptive_time_caps_by_epoch(ohlc["epoch"][entry_idx], seg["confirm_epoch"],
                                       seg["confirm_idx"])


def _path_inputs(bars: pl.DataFrame, instrument: str, domain: str, substrate: str,
                 es, ohlc: dict, atr: np.ndarray) -> PathInputs:
    """Kept-event entry indices, directions, ATR, and adaptive cap for one substrate-cell."""
    n_bars = int(bars.height)
    entry_idx = es.entry_idx
    seg, state = _segment_state(ohlc, entry_idx)
    if substrate == SUB_AVWAP:
        direction = _avwap_directions(bars, instrument, domain, es)
    else:
        direction = _harami_random_direction(entry_idx, state)
    cap, warmup = _adaptive_cap(entry_idx, ohlc, seg)
    keep = (~warmup) & (direction != 0) if entry_idx.shape[0] else np.empty(0, dtype=bool)
    g_idx = entry_idx[keep] if entry_idx.shape[0] else entry_idx
    g_dir = direction[keep] if entry_idx.shape[0] else direction
    g_cap = cap[keep] if entry_idx.shape[0] else cap
    g_atr = atr[g_idx] if g_idx.shape[0] else np.empty(0, dtype=np.float64)
    vol = ohlc.get("volume")
    return PathInputs(high=ohlc["high"], low=ohlc["low"], close=ohlc["close"], volume=vol,
                      n_bars=n_bars, entry_idx=g_idx, direction=g_dir, atr_entry=g_atr, cap=g_cap)


def make_entrysets(bars: pl.DataFrame, instrument: str, domain: str, cell_index: int) -> dict:
    """Three substrate entry sets for one cell on the TRAIN slice (EXP-080/081 plumbing/seed).

    The harami pair is deduped to one canonical stratum (``SUB_HARAMI_V2A``; see the C1 note at
    ``SUBSTRATE_ORDER``). ``SUB-RANDOM`` is the matched-random attribution null, sized to the harami
    entry count (the family's standard control size).
    """
    avwap = avwap_entries(bars, instrument=instrument, domain=domain)
    harami = harami_native_entries(bars, instrument=instrument, domain=domain)
    hcount = int(harami.entry_idx.shape[0])
    rnd = random_entries(bars, instrument=instrument, domain=domain, n_target=hcount,
                         rng=np.random.default_rng([SEED_RANDOM, cell_index, hcount]))
    return {SUB_AVWAP: avwap, SUB_HARAMI_V2A: harami, SUB_RANDOM: rnd}


# --------------------------------------------------------------------------- #
# Pure computation — frozen enumerated candidate surface (per cell -> resolvers)
# --------------------------------------------------------------------------- #
def _vp_fav_distance(pin: PathInputs, atr_med: float) -> np.ndarray:
    """Per-event favourable ATR distance to the cell volume-profile POC (real prices, TickVolume).

    Cell-level VP (disclosed screen-stage simplification): a single profile over the TRAIN bars; the
    favourable distance is ``rd*(POC - C)/ATR`` per event (non-positive -> invalid, excluded by the
    resolver's favourable-target guard). Returns all-NaN when volume is unavailable.
    """
    n = int(pin.entry_idx.shape[0])
    if pin.volume is None or n == 0 or not np.isfinite(atr_med) or atr_med <= 0.0:
        return np.full(n, np.nan)
    vp = volume_profile_levels(pin.low, pin.high, pin.volume, bin_width=VP_BIN_FRAC * atr_med)
    if not vp.defined:
        return np.full(n, np.nan)
    c0 = pin.close[pin.entry_idx]
    a = pin.atr_entry
    with np.errstate(invalid="ignore"):
        dist = pin.direction * (vp.poc - c0) / a
    return np.where(np.isfinite(dist) & (dist > 0.0), dist, np.nan)


def build_candidates(pin: PathInputs, stats: CellStats, atr_med: float) -> dict:
    """Frozen candidate -> ``(full, nostop)`` Resolution pair for one substrate-cell (TRAIN region).

    ``full`` is the candidate's realized exit; ``nostop`` is the **same candidate's favourable-target +
    time-cap with the adverse leg removed** — the per-candidate S1 ``X_fav`` reference (so ``X_tail =
    X_full - X_fav`` is that candidate's own stop-truncation contribution). For a trailing arm the stop
    *is* the exit mechanism, so its no-stop reference is hold-to-cap (fixed horizon); for the no-stop
    arms (V2A-ADVNONE, AVWAP-FH) ``nostop == full`` (``X_tail = 0``). Derived (D1/D2/D3) come from the
    sha256-pinned ``derive_barriers``; benchmarks are the enumerated conventional grid. Distances ATR,
    caps bars; all resolvers read only entry+1..cap real OHLC (causal, adverse-first fill).
    """
    n = int(pin.entry_idx.shape[0])
    cap_q75 = np.full(n, max(1, int(round(stats.ttp_q75))), dtype=np.int64)
    mae = stats.mae_q90
    inf = np.full(n, np.inf)

    def static(tf, sa, cap):
        return resolve_static_barrier(pin.high, pin.low, pin.close, pin.atr_entry, pin.entry_idx,
                                      pin.direction, tf, sa, cap, pin.n_bars)

    def fh(cap):
        return resolve_fixed_horizon(pin.close, pin.atr_entry, pin.entry_idx, pin.direction,
                                     cap, pin.n_bars)

    bars_d = derive_barriers(stats)
    out: dict = {}
    # --- derived (frozen, pinned): nostop = same target+cap, stop removed ---
    for cid, b in bars_d.items():
        tf, cap = np.full(n, b.t_fav), np.full(n, b.h_cap, dtype=np.int64)
        out[cid] = (static(tf, np.full(n, b.s_adv), cap), static(tf, inf, cap))
    # --- /EXIT-RR (R*MAE_q90 target, MAE_q90 stop, TTP_q75 cap) ---
    for r in RR_RATIOS:
        tf = np.full(n, r * mae)
        out[f"RR-{r:g}"] = (static(tf, np.full(n, mae), cap_q75), static(tf, inf, cap_q75))
    # --- /EXIT-VP (cell POC target, MAE_q90 stop) ---
    vp = _vp_fav_distance(pin, atr_med)
    out["VP-POC"] = (static(vp, np.full(n, mae), cap_q75), static(vp, inf, cap_q75))
    # --- /EXIT-TRAIL (ATR k=1,2,3 + structure swing); nostop reference = hold-to-cap (FH) ---
    for k in TRAIL_ATR_K:
        full = resolve_trailing(pin.high, pin.low, pin.close, pin.atr_entry, pin.entry_idx,
                                pin.direction, k, cap_q75, pin.n_bars)
        out[f"TRAIL-ATR{k:g}"] = (full, fh(cap_q75))
    out["TRAIL-STRUCT"] = (resolve_struct_trail(pin.high, pin.low, pin.close, pin.atr_entry,
                                                pin.entry_idx, pin.direction,
                                                max(2, int(round(stats.ttp_med))), cap_q75,
                                                pin.n_bars), fh(cap_q75))
    # --- /EXIT-PARTIAL (PARTIAL-V2A 2-leg, V2A-ADVNONE no-stop, AVWAP-FH fixed horizon) ---
    mfe = np.full(n, stats.mfe_med)
    out["PARTIAL-V2A"] = (resolve_partial_two_leg(
        pin.high, pin.low, pin.close, pin.atr_entry, pin.entry_idx, pin.direction,
        mfe, np.full(n, mae), cap_q75, pin.n_bars, leg_frac=0.5), static(mfe, inf, cap_q75))
    nostop_v2a = static(mfe, inf, cap_q75)
    out["V2A-ADVNONE"] = (nostop_v2a, nostop_v2a)          # already no stop -> X_tail = 0
    fh_res = fh(cap_q75)
    out["AVWAP-FH"] = (fh_res, fh_res)                     # no stop -> X_tail = 0
    return out


CANDIDATE_BRANCH = {
    "D1-MEDIAN-CAPTURE": "EXIT-DERIVED", "D2-TAIL-ROBUST": "EXIT-DERIVED",
    "D3-CAPTURE-EFFICIENT": "EXIT-DERIVED",
    **{f"RR-{r:g}": "EXIT-RR" for r in RR_RATIOS}, "VP-POC": "EXIT-VP",
    **{f"TRAIL-ATR{k:g}": "EXIT-TRAIL" for k in TRAIL_ATR_K}, "TRAIL-STRUCT": "EXIT-TRAIL",
    "PARTIAL-V2A": "EXIT-PARTIAL", "V2A-ADVNONE": "EXIT-PARTIAL", "AVWAP-FH": "EXIT-PARTIAL",
}


# --------------------------------------------------------------------------- #
# Pure computation — gate evaluation for one {substrate x cell x candidate}
# --------------------------------------------------------------------------- #
def evaluate_gate(
    cand_res: Resolution, ctrl_res: Resolution, nostop_res: Resolution,
    nostop_ctrl_res: Resolution, m_cell: float, rng: np.random.Generator,
) -> GateRow:
    """G-018a (gross exp/med + matched-random excess) + S1 (X_fav attribution) + S2 (tail residual)."""
    cand = cand_res.ret[cand_res.resolved]
    ctrl = ctrl_res.ret[ctrl_res.resolved]
    n_res = int(cand.shape[0])
    nan = float("nan")
    if n_res < EVENT_FLOOR or ctrl.shape[0] < EVENT_FLOOR:
        return GateRow(n_usable=int(cand_res.ret.shape[0]), n_resolved=n_res, gross_exp=nan,
                       gross_exp_lo=nan, gross_med=nan, gross_med_lo=nan, matched_exp_excess_lo=nan,
                       matched_med_excess_lo=nan, g018a_pass=False, guard_i_defer=False, x_full=nan,
                       x_fav=nan, x_tail=nan, x_fav_excess_lo=nan, m_cell=m_cell, s1_pass=False,
                       tailmass_post=nan, q05_post=nan, q05_control=nan, s2_pass=False,
                       s2_deferred=False, valid=False, fail_leg="underpowered")
    # G-018a gross legs
    exp, exp_lo = one_sided_lo(cand, rng, "mean", n_boot=N_BOOT)
    med, med_lo = one_sided_lo(cand, rng, "median", n_boot=N_BOOT)
    me_lo = two_sample_diff_lo(cand, ctrl, rng, "mean", n_boot=N_BOOT)
    mm_lo = two_sample_diff_lo(cand, ctrl, rng, "median", n_boot=N_BOOT)
    guard_i = bool(n_res <= 60)                      # D6 Guard (i): defer expectancy to median
    exp_leg = med_lo > 0.0 if guard_i else (exp_lo > 0.0 and med_lo > 0.0)
    excess_leg = (mm_lo > 0.0) if guard_i else (me_lo > 0.0 and mm_lo > 0.0)
    g018a = bool(exp_leg and excess_leg)
    # S1 attribution: X_fav (no-stop) beats matched-random by > m_cell
    x_full = exp
    nostop = nostop_res.ret[nostop_res.resolved]
    nostop_ctrl = nostop_ctrl_res.ret[nostop_ctrl_res.resolved]
    x_fav = float(np.mean(nostop)) if nostop.shape[0] else nan
    x_tail = x_full - x_fav if np.isfinite(x_fav) else nan
    xfav_excess_lo = two_sample_diff_lo(nostop, nostop_ctrl, rng, "mean", n_boot=N_BOOT) \
        if nostop.shape[0] >= EVENT_FLOOR and nostop_ctrl.shape[0] >= EVENT_FLOOR else nan
    s1 = bool(np.isfinite(xfav_excess_lo) and np.isfinite(m_cell) and xfav_excess_lo > m_cell)
    # S2 tail non-residual
    tm, q05, q05c, s2_raw = s2_tail_residual(cand, ctrl, tau_tail=TAU_TAIL, delta=DELTA, k_tail=K_TAIL)
    s2_def = bool(n_res < N_S2_FLOOR)
    s2 = bool(s2_raw) and not s2_def
    valid = bool(g018a and s1 and (s2 or s2_def))
    fail = "" if valid else ("g018a" if not g018a else "s1" if not s1 else "s2")
    return GateRow(n_usable=int(cand_res.ret.shape[0]), n_resolved=n_res, gross_exp=exp,
                   gross_exp_lo=exp_lo, gross_med=med, gross_med_lo=med_lo,
                   matched_exp_excess_lo=me_lo, matched_med_excess_lo=mm_lo, g018a_pass=g018a,
                   guard_i_defer=guard_i, x_full=x_full, x_fav=x_fav, x_tail=x_tail,
                   x_fav_excess_lo=xfav_excess_lo, m_cell=m_cell, s1_pass=s1, tailmass_post=tm,
                   q05_post=q05, q05_control=q05c, s2_pass=s2, s2_deferred=s2_def, valid=valid,
                   fail_leg=fail)


# --------------------------------------------------------------------------- #
# Orchestration — one cell
# --------------------------------------------------------------------------- #
def _cell_stats_from_summary(row: dict) -> CellStats:
    return CellStats(mfe_med=row["mfe_med"], mfe_q40=row["mfe_q40"], ttp_med=row["ttp_med"],
                     ttp_q75=row["ttp_q75"], mae_q90=row["mae_q90"], m_anti=row["m_anti"])


def process_cell(frame: pl.DataFrame, instrument: str, period: int, cell_index: int,
                 summary: pl.DataFrame) -> list[dict]:
    """Screen all candidates on all 4 substrates for one (instrument x domain) cell."""
    domain = DOMAIN_LABEL[period]
    bars = build_domain_bars(frame, period)
    ohlc = _real_ohlc(bars)
    if "TickVolume" in bars.columns:
        ohlc["volume"] = bars.get_column("TickVolume").to_numpy().astype(np.float64)
    atr = wilder_atr(ohlc["high"], ohlc["low"], ohlc["close"], ATR_PERIOD)
    es = make_entrysets(bars, instrument, domain, cell_index)

    records: list[dict] = []
    for s_i, sub in enumerate(SUBSTRATE_ORDER):
        srow = summary.filter((pl.col("instrument") == instrument) & (pl.col("domain") == domain)
                              & (pl.col("substrate") == _SUMMARY_SUBSTRATE[sub]))
        if srow.height == 0:
            continue
        stats = _cell_stats_from_summary(srow.row(0, named=True))
        pin = _path_inputs(bars, instrument, domain, sub, es[sub], ohlc, atr)
        atr_med = float(np.median(pin.atr_entry)) if pin.atr_entry.size else float("nan")
        # matched-random control sized to this substrate's kept-event count, same regime direction.
        # Post C1 dedup each screened stratum is a distinct entry population, so seeding the control by
        # s_i is now a per-entry-population key (no two strata share an identical entry set).
        ctrl_pin = _matched_control(bars, instrument, domain, ohlc, atr, pin, cell_index, s_i)

        cand_map = build_candidates(pin, stats, atr_med)        # cid -> (full, nostop)
        ctrl_map = build_candidates(ctrl_pin, stats, atr_med)
        n_keep = int(pin.entry_idx.shape[0])

        for c_i, cid in enumerate(cand_map):
            cand_full, cand_nostop = cand_map[cid]
            ctrl_full, ctrl_nostop = ctrl_map[cid]
            # W1 audit fix (2026-06-22): m_cell is calibrated PER CANDIDATE from that candidate's own
            # no-stop control reference, so the synthetic null is scaled to each arm's favourable-target
            # distance (the prior per-cell reuse of the mfe_med-target margin was anti-conservative for
            # the larger-target RR arms). NaN when the candidate's control base is sub-floor.
            ctrl_base = ctrl_nostop.ret[np.isfinite(ctrl_nostop.ret)]
            rng_m = np.random.default_rng([SEED_BOOT, cell_index, s_i, c_i, 999])
            m_cell = (m_cell_margin(ctrl_base, n_keep, rng_m, "mean",
                                    null_reps=NULL_REPS, n_boot=N_BOOT_NULL)
                      if ctrl_base.shape[0] >= EVENT_FLOOR else float("nan"))
            rng = np.random.default_rng([SEED_BOOT, cell_index, s_i, c_i])
            row = evaluate_gate(cand_full, ctrl_full, cand_nostop, ctrl_nostop, m_cell, rng)
            records.append(gate_row_dict(instrument, domain, sub, cid, row))
    return records


def _matched_control(bars, instrument, domain, ohlc, atr, pin, cell_index, s_i) -> PathInputs:
    """Random-entry control sized to this substrate's kept-event count; same regime direction/cap."""
    n_keep = int(pin.entry_idx.shape[0])
    rng = np.random.default_rng([SEED_RANDOM, cell_index, s_i, 7])
    es = random_entries(bars, instrument=instrument, domain=domain,
                        n_target=max(n_keep, EVENT_FLOOR), rng=rng)
    return _path_inputs(bars, instrument, domain, SUB_RANDOM, es, ohlc, atr)


# --------------------------------------------------------------------------- #
# Plotting (bounded; from the collected screen table only)
# --------------------------------------------------------------------------- #
def _status(row: dict) -> str:
    if row["valid"]:
        return "valid"
    if row["fail_leg"] == "underpowered":
        return "underpowered"
    if row["s2_deferred"] and row["g018a_pass"] and row["s1_pass"]:
        return "s2_deferred"
    return f"fail@{row['fail_leg']}"


def plot_survivor_map(df: pl.DataFrame, path: Path) -> None:
    """Plot 1 — candidate x (substrate,domain) outcome heatmap."""
    sns.set_theme(style="white")
    cats = ["valid", "s2_deferred", "fail@s2", "fail@s1", "fail@g018a", "underpowered"]
    cmap = {c: i for i, c in enumerate(cats)}
    cands = sorted(df.get_column("candidate").unique().to_list())
    cols = [f"{s.replace('SUB-', '')}/{d}" for s in SUBSTRATE_ORDER for d in DOMAIN_ORDER]
    mat = np.full((len(cands), len(cols)), np.nan)
    lut = {(r["candidate"], f"{r['substrate'].replace('SUB-','')}/{r['domain']}"): _status(r)
           for r in df.iter_rows(named=True)}
    for i, c in enumerate(cands):
        for j, col in enumerate(cols):
            st = lut.get((c, col))
            if st is not None:
                mat[i, j] = cmap[st]
    fig, ax = plt.subplots(figsize=(16, 8))
    im = ax.imshow(mat, aspect="auto", cmap="RdYlGn_r", vmin=0, vmax=len(cats) - 1)
    ax.set_xticks(range(len(cols)), cols, rotation=90, fontsize=6)
    ax.set_yticks(range(len(cands)), cands, fontsize=8)
    cbar = fig.colorbar(im, ax=ax, ticks=range(len(cats)))
    cbar.ax.set_yticklabels(cats)
    ax.set_title("EXP-083 survivor map — candidate x (substrate/domain)")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_s1(df: pl.DataFrame, path: Path) -> None:
    """Plot 2 — S1 X_fav vs X_tail decomposition by substrate."""
    sns.set_theme(style="whitegrid")
    sub = df.filter(pl.col("x_fav").is_finite() & pl.col("x_tail").is_finite())
    fig, ax = plt.subplots(figsize=(8, 6))
    for s in SUBSTRATE_ORDER:
        d = sub.filter(pl.col("substrate") == s)
        ax.scatter(d.get_column("x_fav"), d.get_column("x_tail"), s=14, alpha=0.6,
                   label=s.replace("SUB-", ""))
    ax.axvline(0, color="grey", ls=":")
    ax.axhline(0, color="grey", ls=":")
    ax.set_xlabel("X_fav (favourable+timecap, ATR)")
    ax.set_ylabel("X_tail (stop-truncation, ATR)")
    ax.set_title("EXP-083 S1 attribution decomposition")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_s2(df: pl.DataFrame, path: Path) -> None:
    """Plot 3 — S2 post-exit tailmass vs relative-q05 with frozen thresholds."""
    sns.set_theme(style="whitegrid")
    d = df.filter(pl.col("tailmass_post").is_finite() & pl.col("q05_post").is_finite())
    rel = d.get_column("q05_post") - d.get_column("q05_control")
    fig, ax = plt.subplots(figsize=(8, 6))
    colours = ["tab:green" if v else "tab:red" for v in d.get_column("s2_pass")]
    ax.scatter(d.get_column("tailmass_post"), rel, c=colours, s=14, alpha=0.6)
    ax.axvline(TAU_TAIL, color="black", ls="--", label=f"tau_tail={TAU_TAIL}")
    ax.axhline(-DELTA, color="purple", ls="--", label=f"-delta={-DELTA}")
    ax.set_xlabel("post-exit tailmass")
    ax.set_ylabel("q05_post - q05_control (ATR)")
    ax.set_title("EXP-083 S2 tail non-residual (green=pass)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_gross(df: pl.DataFrame, path: Path) -> None:
    """Plot 4 — gross expectancy & median CI_low vs matched-random excess by candidate."""
    sns.set_theme(style="whitegrid")
    g = df.group_by("candidate").agg(
        pl.col("gross_exp").median().alias("exp"),
        pl.col("matched_exp_excess_lo").median().alias("me_lo")).sort("candidate")
    fig, ax = plt.subplots(figsize=(10, 6))
    y = np.arange(g.height)
    ax.barh(y - 0.2, g.get_column("exp"), height=0.4, label="median gross exp (ATR)")
    ax.barh(y + 0.2, g.get_column("me_lo"), height=0.4, label="median matched-excess CI_low")
    ax.axvline(0, color="grey", ls=":")
    ax.set_yticks(y, g.get_column("candidate").to_list(), fontsize=8)
    ax.set_title("EXP-083 gross edge vs matched-random by candidate")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_failleg(df: pl.DataFrame, path: Path) -> None:
    """Plot 5 — fail-leg attribution counts by candidate branch (where candidates die)."""
    sns.set_theme(style="whitegrid")
    d = df.with_columns(pl.col("candidate").replace_strict(CANDIDATE_BRANCH, default="?")
                        .alias("branch"))
    piv = (d.group_by(["branch", "fail_leg"]).len()
           .pivot(values="len", index="branch", on="fail_leg").fill_null(0).sort("branch"))
    legs = [c for c in piv.columns if c != "branch"]
    fig, ax = plt.subplots(figsize=(10, 6))
    bottom = np.zeros(piv.height)
    for leg in legs:
        vals = piv.get_column(leg).to_numpy()
        ax.bar(piv.get_column("branch"), vals, bottom=bottom, label=leg or "valid")
        bottom += vals
    ax.set_title("EXP-083 outcome attribution by candidate branch")
    ax.set_ylabel("count of {substrate x cell x candidate}")
    ax.legend(fontsize=8)
    plt.xticks(rotation=30, ha="right")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration — provenance, member set, freeze, main
# --------------------------------------------------------------------------- #
def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assert_provenance() -> dict:
    """Assert the pinned derive_barriers hash + EXP-080/081/082 fingerprints (HALT on mismatch)."""
    derive_sha = _hash_file(PROJECT_ROOT / "python/src/xen/capgeo_exits.py")
    e81 = json.loads(_EXP081_META.read_text())
    e82 = json.loads(_EXP082_META.read_text())
    if e81.get("verdict") != "CHARACTERISATION_DELIVERED" or e81.get("n_substrate_cells") != 184:
        raise RuntimeError("EXP-081 provenance mismatch (verdict / cell count)")
    if not e81.get("holdout_untouched", False) or e81.get("counted_test_reads") != 0:
        raise RuntimeError("EXP-081 holdout/test-read provenance mismatch")
    if e82.get("verdict") != "DERIVATION_DELIVERED":
        raise RuntimeError("EXP-082 provenance mismatch (verdict)")
    pin82 = str(e82.get("derive_barriers_module_sha256", ""))
    if not pin82 or pin82 != derive_sha:
        raise RuntimeError(f"derive_barriers sha256 != EXP-082 pin ({derive_sha[:12]} vs "
                           f"{pin82[:12]})")
    if not derive_sha.startswith(_DERIVE_PIN):
        raise RuntimeError(f"derive_barriers sha256 prefix != {_DERIVE_PIN} ({derive_sha[:8]})")
    return {"derive_barriers_sha256": derive_sha, "exp081_verdict": e81.get("verdict"),
            "exp082_verdict": e82.get("verdict"), "capgeo_exits_module": capgeo_exits.__name__}


def _member_set() -> set:
    rm = pl.read_csv(_EXP080_READY_MAP)
    ready = (rm.filter(pl.col("readiness_status") == "READY")
             .select(["instrument", "domain"]).unique())
    return {(r["instrument"], r["domain"]) for r in ready.iter_rows(named=True)} - COVERAGE_EXCLUDED


def _freeze_valid_set(df: pl.DataFrame) -> dict:
    """Canonicalize the surviving {candidate x stratum} set + Holm rule and sha256-hash-pin it."""
    valid = (df.filter(pl.col("valid")).select(
        ["substrate", "instrument", "domain", "candidate", "n_resolved",
         "gross_exp", "s2_deferred"]).sort(["substrate", "instrument", "domain", "candidate"]))
    members = valid.to_dicts()
    holm_rule = ("Holm-Bonferroni at one-sided alpha=0.05 across the full frozen "
                 "{valid-candidate x stratum} grid; applied at EXP-084 on the WF verdict p-values.")
    canonical = json.dumps({"members": members, "holm_rule": holm_rule}, sort_keys=True, default=str)
    return {"n_valid": int(valid.height), "holm_rule": holm_rule, "members": members,
            "sha256": hashlib.sha256(canonical.encode()).hexdigest()}


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGGER.info("EXP-083 — TRAIN-only candidate screen (HYP-004a); N_BOOT=%d", N_BOOT)
    provenance = _assert_provenance()

    val005 = _load_val005()
    found, _missing = val005.discover_infr003_files()
    members = _member_set()
    summary = pl.read_parquet(_EXP081_SUMMARY)
    LOGGER.info("member set: %d instrument x domain cells; %d EXP-081 summary rows",
                len(members), summary.height)

    instruments = [s for s in val005.TARGET_SYMBOLS if s in found]
    loaded: dict[str, object] = {}
    for inst in instruments:
        li, _seal, status = val005.load_first70(found[inst])
        if li is not None:
            loaded[inst] = li
    instruments = [s for s in instruments if s in loaded]
    if not instruments:
        raise RuntimeError("no instruments loaded; cannot screen")

    full_grid = [(inst, p) for inst in instruments for p in val005.DOMAINS]
    member_grid = [(ci, inst, p) for ci, (inst, p) in enumerate(full_grid)
                   if (inst, DOMAIN_LABEL[p]) in members]
    if MAX_CELLS > 0:
        member_grid = member_grid[:MAX_CELLS]
        LOGGER.info("SMOKE subset: first %d member cells", len(member_grid))

    all_records: list[dict] = []
    train_cutoffs: dict[str, int] = {}
    for ci, inst, period in tqdm(member_grid, desc="screen cells"):
        li = loaded[inst]
        analysis_rows = int(li.frame.height)
        train_cutoff = int(analysis_rows * 0.7)
        train_frame = li.frame.slice(0, train_cutoff)
        if not train_frame.get_column("CloseTime").is_sorted():
            raise RuntimeError(f"{inst}-{DOMAIN_LABEL[period]}: TRAIN frame not CloseTime-sorted")
        train_cutoffs[inst] = train_cutoff
        all_records.extend(process_cell(train_frame, inst, period, ci, summary))

    df = pl.DataFrame(all_records)
    valid_set = _freeze_valid_set(df)
    n_valid = valid_set["n_valid"]
    verdict = "SCREEN_DELIVERED" if n_valid > 0 else "ALL_CANDIDATES_FAIL"

    # Determinism replay (second pass over the member grid; compare the screen table fingerprint).
    replay: list[dict] = []
    for ci, inst, period in member_grid:
        li = loaded[inst]
        train_frame = li.frame.slice(0, int(int(li.frame.height) * 0.7))
        replay.extend(process_cell(train_frame, inst, period, ci, summary))
    determinism_ok = _fingerprint(all_records) == _fingerprint(replay)

    df.write_parquet(RESULTS_DIR / "screen_results.parquet")
    df.write_csv(RESULTS_DIR / "screen_results.csv")
    (RESULTS_DIR / "valid_candidate_set.json").write_text(json.dumps(
        {"verdict": verdict, **valid_set,
         "note": "Frozen, hash-pinned valid-candidate set + Holm rule — the binding EXP-084 hand-off "
                 "(D4.1). EXP-084 imports this verbatim and asserts sha256 before any TEST row.",
         "provenance": provenance}, indent=2, default=str))
    _write_metadata(df, verdict, valid_set, provenance, train_cutoffs, determinism_ok, len(members),
                    len(member_grid))

    plot_survivor_map(df, PLOTS_DIR / "01_survivor_map.png")
    plot_s1(df, PLOTS_DIR / "02_s1_decomposition.png")
    plot_s2(df, PLOTS_DIR / "03_s2_tail_residual.png")
    plot_gross(df, PLOTS_DIR / "04_gross_vs_matched.png")
    plot_failleg(df, PLOTS_DIR / "05_fail_attribution.png")

    LOGGER.info("verdict=%s rows=%d valid=%d determinism_ok=%s",
                verdict, df.height, n_valid, determinism_ok)
    LOGGER.info("valid-set sha256=%s", valid_set["sha256"])
    LOGGER.info("results -> %s", RESULTS_DIR)


def _fingerprint(records: list[dict]) -> str:
    def _round(v):
        return round(v, 9) if isinstance(v, float) and np.isfinite(v) else v
    recs = sorted(({k: _round(v) for k, v in r.items()} for r in records),
                  key=lambda d: (d["substrate"], d["instrument"], d["domain"], d["candidate"]))
    return hashlib.sha256(json.dumps(recs, sort_keys=True, default=str).encode()).hexdigest()


def _write_metadata(df, verdict, valid_set, provenance, train_cutoffs, determinism_ok,
                    n_members, n_screened) -> None:
    meta = {
        "experiment": EXPERIMENT_ID, "hypothesis": "HYP-004a (D0-amendment-001 split)",
        "generated_at": datetime.now(timezone.utc).isoformat(), "verdict": verdict,
        "n_rows": int(df.height), "n_valid_candidates": int(valid_set["n_valid"]),
        "valid_set_sha256": valid_set["sha256"], "holm_rule": valid_set["holm_rule"],
        "n_member_cells": n_members, "n_screened_cells": n_screened,
        "candidate_branches": CANDIDATE_BRANCH,
        "read_region": "TRAIN sub-split [0, int(analysis_rows*0.7)); analysis-TEST + holdout never "
                       "sliced", "train_cutoffs": train_cutoffs,
        "cost_treatment": "GROSS (operator 2026-06-22); cost layer deferred to conditional follow-up",
        "ass_binding": False,
        "seeds": {"SEED_RANDOM": SEED_RANDOM, "SEED_BOOT": SEED_BOOT},
        "bootstrap_budgets": {"N_BOOT": N_BOOT, "NULL_REPS": NULL_REPS, "N_BOOT_NULL": N_BOOT_NULL,
                              "note": "N_BOOT default 10_000 (scope freeze); EXP083_N_BOOT may lower "
                                      "it for a manual screen run — value recorded here."},
        "frozen_constants": {"K_TAIL": K_TAIL, "TAU_TAIL": TAU_TAIL, "DELTA": DELTA,
                             "N_S2_FLOOR": N_S2_FLOOR, "EVENT_FLOOR": EVENT_FLOOR,
                             "DIP_ALPHA": DIP_ALPHA, "ATR_PERIOD": ATR_PERIOD,
                             "RR_RATIOS": list(RR_RATIOS), "TRAIL_ATR_K": list(TRAIL_ATR_K),
                             "VP_BIN_FRAC": VP_BIN_FRAC},
        "module_hashes": {
            "capgeo_exits": provenance["derive_barriers_sha256"],
            "capgeo_screen": _hash_file(PROJECT_ROOT / "python/src/xen/capgeo_screen.py"),
            "capgeo_substrates": _hash_file(PROJECT_ROOT / "python/src/xen/capgeo_substrates.py"),
            "capgeo_geometry": _hash_file(PROJECT_ROOT / "python/src/xen/capgeo_geometry.py"),
            "domain_bars": _hash_file(PROJECT_ROOT / "python/src/xen/domain_bars.py")},
        "provenance": provenance, "determinism_ok": bool(determinism_ok),
        "holdout_untouched": True, "test_stratum_touched": False,
        "counted_test_reads": 0, "candidate_slots": 0,
        "deviations": [
            "GROSS screen + suite floors deferred (operator 2026-06-22).",
            "/SIZE-VOLADJ is non-distinct in the ATR-normalized metric frame (returns already "
            "vol-normalized) -> reported as a disclosure, not a separate gate candidate.",
            "/EXIT-VP uses a cell-level TickVolume profile (POC target) rather than a per-event "
            "reference-move profile (screen-stage simplification, disclosed); skipped where domain "
            "bars carry no TickVolume.",
            "/EXIT-TRAIL structure arm uses a rolling swing-window trail as a ZigZag-pivot proxy "
            "(disclosed, screen-stage).",
            "C1 audit fix (2026-06-22): the entry-identical harami pair (PARTIAL-V2A / V2A-ADVNONE) is "
            "deduped to ONE canonical screened stratum 'SUB-HARAMI-V2A' (3 screened substrates, not 4); "
            "the multiplicity-registry harami count is consolidated accordingly. Removes the prior "
            "control-draw inconsistency that flipped a survivor between the two identical substrates.",
            "W1 audit fix (2026-06-22): m_cell is now calibrated PER CANDIDATE from each arm's own "
            "no-stop control reference (scaled to its favourable-target distance), replacing the prior "
            "per-cell reuse of the mfe_med-target margin (anti-conservative for large-target RR arms); "
            "binding N_BOOT=10_000 honored on the edge-call CIs."],
    }
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(meta, indent=2, default=str))


if __name__ == "__main__":
    main()
