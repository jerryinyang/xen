"""Experiment EXP-040: HYP-001 Direct AVWAP Line Support/Resistance Test.

Implements scope.md / analysis-plan.md (Phase 010 Track B; mechanism science,
0 slots, no gate consequence). Binding question: is
``P(bounce | approach to AVWAP) > P(bounce | approach to matched control
levels)`` on the 1h / 4h domains, analysis set, gross real prices?

Framing (Phase 007 design §8, binding): the event is an *approach* — close
enters the eps-neighborhood (eps = 0.25 x live MAD band width) of a level
from beyond the 2x-eps hysteresis radius; the outcome is whether the episode
exits the neighborhood on its entry side (bounce) within 24 bars. The same
detector (``xen.line_approach``) runs verbatim over three arms: the live
AVWAP line; frozen horizontal control levels snapshotted at
``AVWAP(t0) + delta x BW(t0)`` (|delta| ~ U[1.5, 3.5], random sign, one per
25 bars, alive 100 bars; the binding control); and shifted MOVING copies
``AVWAP(t) + delta x BW(t)`` with the identical construction (descriptive
secondary control, design §11/8 — isolates the moving-vs-static kinematic
confound). The EXP-020 bounce-trigger machinery appears nowhere in any
metric path (EXP-025 conflation inadmissible).

Binding inference: per-domain stratum-weighted rate difference (percentage
points) AVWAP vs the STATIC control with cluster bootstrap CI (AVWAP arm
clusters = anchor segments; control arm clusters = levels) and a one-sided
cluster-label permutation p, Holm across the 2 domains at alpha = 0.05.
Per-instrument cells and the AVWAP-vs-moving-copy contrast Delta_m
(bootstrap CI only; no permutation, no Holm) are descriptive.

The final 30% global holdout is never loaded.

Run:
    cd <project-root> && python python/experiments/EXP-040/code/run_experiment.py
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402  (backend must be set first)
import numpy as np  # noqa: E402
import polars as pl  # noqa: E402
from tqdm.auto import tqdm  # noqa: E402

# --------------------------------------------------------------------------- #
# Path setup
# --------------------------------------------------------------------------- #
PROJECT_ROOT = Path(__file__).resolve().parents[4]

from xen.avwap import BAND_MULTIPLIER, compute_band_trace, generate_avwap_events  # noqa: E402
from xen.line_approach import (  # noqa: E402
    BOUNCE,
    PASS_THROUGH,
    UNRESOLVED,
    detect_episodes,
    spawn_control_levels,
)
from xen.referee_calibration import (  # noqa: E402
    build_domain_frames,
    list_timebar_files,
    load_analysis_data,
    seed_for,
)

LOGGER = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants (Stage-2 frozen parameters; see analysis-plan.md)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-040"
DATA_DIR = PROJECT_ROOT / "data"
EXP_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"

EXP020_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-020" / "results"

DOMAINS: tuple[str, ...] = ("1h", "4h")
INSTRUMENTS: tuple[str, ...] = ("BTCUSD", "EURUSD", "USTEC", "XAUUSD")

EPS_MULT = 0.25                  # eps = 0.25 x MAD band width
HYSTERESIS_MULT = 2.0            # new episode requires |dist| > 2 x eps first
EPISODE_CAP_BARS = 24
MATERIALITY_PP = 2.0             # AGAINST-as-immaterial band
DELTA_RANGE = (1.5, 3.5)         # control offsets in BW units (random sign)
CONTROL_SPACING_BARS = 25
CONTROL_LIFETIME_BARS = 100
CONTROL_LINE_CLEARANCE_BW = 1.0  # drop control episodes opening within 1 BW of the line
SPEED_LOOKBACK_BARS = 5
ATR_PERIOD = 14
VOL_WINDOW_DAYS = 90
VOL_WINDOW_BARS: dict[str, int] = {"1h": 24 * VOL_WINDOW_DAYS, "4h": 6 * VOL_WINDOW_DAYS}
TERCILE_EDGES = (1.0 / 3.0, 2.0 / 3.0)

MIN_STRATUM_EPISODES = 5
FLOOR_EPISODES_PER_ARM = 100
N_BOOT = 1000
N_PERM = 2000
CI_PERCENTILES = (2.5, 97.5)
ALPHA = 0.05
DETERMINISM_TOL = 1e-12

STRATA_COLS = ["instrument", "entry_side", "vol_terc", "speed_terc"]


# --------------------------------------------------------------------------- #
# I/O helpers
# --------------------------------------------------------------------------- #
def configure_logging() -> None:
    """Configure concise INFO logging for the manual run."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                        datefmt="%H:%M:%S")


def ensure_output_dirs() -> None:
    """Create ``results/`` and ``plots/`` (orchestration-time only)."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write dict rows to CSV (empty-safe)."""
    if not rows:
        path.write_text("")
        return
    pl.DataFrame(rows).write_csv(path)


# --------------------------------------------------------------------------- #
# Substrate: domain bars, AVWAP regimes, causal vol percentile
# --------------------------------------------------------------------------- #
def build_cells() -> dict[tuple[str, str], dict[str, Any]]:
    """Rebuild first-70% domain bars + AVWAP regimes for the scoped domains.

    Reconciles the regenerated event/bar counts against the EXP-020 artifacts
    (hard gate) so the line/band state is byte-identical to the registered
    definition before any episode is detected.
    """
    expected = pl.read_csv(EXP020_RESULTS / "analysis_metadata.csv")
    expected_by_cell = {(str(r["instrument"]), str(r["domain"])): r
                        for r in expected.to_dicts()}
    exp020_events = pl.read_csv(EXP020_RESULTS / "avwap_events.csv")
    sources = set(expected.get_column("source_file").unique().to_list())
    files = [p for p in list_timebar_files(DATA_DIR) if p.name in sources]
    missing = sorted(sources.difference({p.name for p in files}))
    if missing:
        raise FileNotFoundError(f"missing EXP-020 source files: {missing}")
    cells: dict[tuple[str, str], dict[str, Any]] = {}
    for path in tqdm(files, desc="rebuild substrate"):
        data = load_analysis_data(path)
        for domain, frame in build_domain_frames(data.frame).items():
            if domain not in DOMAINS:
                continue
            exp = expected_by_cell[(data.instrument, domain)]
            if frame.height != int(exp["domain_bars"]):
                raise ValueError(f"domain bar mismatch {data.instrument}/{domain}")
            result = generate_avwap_events(frame, instrument=data.instrument,
                                           domain=domain)
            n_expected = exp020_events.filter(
                (pl.col("instrument") == data.instrument)
                & (pl.col("domain") == domain)).height
            if result.events.height != n_expected:
                raise ValueError(
                    f"AVWAP event-count mismatch {data.instrument}/{domain}: "
                    f"{result.events.height} != EXP-020 {n_expected}")
            cells[(data.instrument, domain)] = {
                "frame": frame,
                "close": frame.get_column("Close").to_numpy().astype(float),
                "high": frame.get_column("High").to_numpy().astype(float),
                "low": frame.get_column("Low").to_numpy().astype(float),
                "close_time": frame.get_column("CloseTime").to_numpy()
                .astype("datetime64[ns]"),
                "regimes": result.regimes,
                "vol_pct": causal_vol_percentile(frame, VOL_WINDOW_BARS[domain]),
            }
    LOGGER.info("Substrate reconciliation PASS for %d cells", len(cells))
    return cells


def causal_vol_percentile(frame: pl.DataFrame, window_bars: int) -> np.ndarray:
    """Trailing percentile of ATR(14) within a trailing window (causal).

    ``pct[k]`` = fraction of the previous ``window_bars`` ATR values (bars
    ``<= k``) at or below ``ATR[k]``; NaN during ATR warmup. Chunked sliding
    windows bound memory.
    """
    high = frame.get_column("High").to_numpy().astype(float)
    low = frame.get_column("Low").to_numpy().astype(float)
    close = frame.get_column("Close").to_numpy().astype(float)
    n = close.size
    tr = np.empty(n)
    tr[0] = high[0] - low[0]
    prev_c = close[:-1]
    tr[1:] = np.maximum(high[1:] - low[1:],
                        np.maximum(np.abs(high[1:] - prev_c), np.abs(low[1:] - prev_c)))
    atr = np.full(n, np.nan)
    if n >= ATR_PERIOD:
        kernel = np.ones(ATR_PERIOD) / ATR_PERIOD
        atr[ATR_PERIOD - 1:] = np.convolve(tr, kernel, mode="valid")
    pct = np.full(n, np.nan)
    chunk = 4000
    for lo in range(ATR_PERIOD - 1, n, chunk):
        hi = min(lo + chunk, n)
        for k in range(lo, hi):
            w0 = max(ATR_PERIOD - 1, k - window_bars + 1)
            window = atr[w0 : k + 1]
            pct[k] = float(np.mean(window <= atr[k]))
    return pct


def tercile(value: float, edges: tuple[float, float]) -> int:
    """Bin a value in [0, 1] (or a generic scalar vs cut points) into 0/1/2."""
    if not np.isfinite(value):
        return -1
    if value <= edges[0]:
        return 0
    return 1 if value <= edges[1] else 2


# --------------------------------------------------------------------------- #
# Episode collection (both arms, identical detector)
# --------------------------------------------------------------------------- #
def collect_episodes(cells: dict[tuple[str, str], dict[str, Any]]) -> pl.DataFrame:
    """Run the shared detector over all three arms for every cell.

    Per regime: the band trace supplies the live line and band width; the
    AVWAP arm watches the moving line, the static control arm watches frozen
    horizontal levels spawned inside the regime window, and the secondary
    arm (``control_moving``, design §11/8) watches shifted moving copies of
    the line. Static control episodes opening within
    ``CONTROL_LINE_CLEARANCE_BW`` band widths of the live line are dropped
    (disclosed); moving copies are clear by construction (|delta| >= 1.5 BW).
    """
    rows: list[dict[str, Any]] = []
    clearance_dropped = 0
    for (inst, domain), cell in tqdm(cells.items(), desc="collect episodes"):
        close, ct = cell["close"], cell["close_time"]
        n = close.size
        vol_pct = cell["vol_pct"]
        for reg in cell["regimes"].to_dicts():
            a, c0, e0 = int(reg["anchor_idx"]), int(reg["confirm_idx"]), int(
                reg["regime_end_idx"])
            if e0 <= c0 + 1:
                continue
            trace = compute_band_trace(cell["frame"], a, e0)
            avwap_abs = np.full(n, np.nan)
            bw_abs = np.full(n, np.nan)
            avwap_abs[a : e0 + 1] = trace["avwap"]
            bw_abs[a : e0 + 1] = (np.asarray(trace["upper"])
                                  - np.asarray(trace["avwap"])) / BAND_MULTIPLIER
            eps_abs = EPS_MULT * bw_abs
            rid = int(reg["regime_id"])

            def emit(eps: np.ndarray, level: np.ndarray, arm: str, level_id: str,
                     lo: int, hi: int) -> None:
                nonlocal clearance_dropped
                for epi in detect_episodes(close, level, eps, lo, hi,
                                           EPISODE_CAP_BARS, HYSTERESIS_MULT):
                    k = int(epi["open_idx"])
                    if arm == "control":
                        gap = abs(level[k] - avwap_abs[k])
                        if np.isfinite(gap) and bw_abs[k] > 0 and (
                                gap < CONTROL_LINE_CLEARANCE_BW * bw_abs[k]):
                            clearance_dropped += 1
                            continue
                    speed = (abs(close[k] - close[k - SPEED_LOOKBACK_BARS]) / bw_abs[k]
                             if k - SPEED_LOOKBACK_BARS >= 0 and bw_abs[k] > 0
                             else float("nan"))
                    rows.append({
                        "instrument": inst, "domain": domain, "arm": arm,
                        "regime_id": rid, "level_id": level_id,
                        "open_idx": k, "open_ns": int(ct[k].astype(np.int64)),
                        "entry_side": int(epi["entry_side"]),
                        "vol_pct": float(vol_pct[k]),
                        "vol_terc": tercile(float(vol_pct[k]), TERCILE_EDGES),
                        "speed": speed, "outcome": epi["outcome"],
                        "bars_in": int(epi["bars_in"]),
                    })

            emit(eps_abs, avwap_abs, "avwap", f"line:{rid}", c0 + 1, e0)
            rng = np.random.default_rng(seed_for(EXPERIMENT_ID, "ctrl", inst,
                                                 domain, rid))
            for lvl in spawn_control_levels(avwap_abs, bw_abs, c0 + 1, e0,
                                            CONTROL_SPACING_BARS,
                                            CONTROL_LIFETIME_BARS,
                                            DELTA_RANGE[0], DELTA_RANGE[1], rng):
                level_arr = np.full(n, lvl["level_value"])
                emit(eps_abs, level_arr, "control", f"ctrl:{rid}:{lvl['spawn_idx']}",
                     int(lvl["alive_start"]), int(lvl["alive_end"]))
            # Secondary arm (design §11/8): shifted MOVING copies of the line.
            # Same spawn grid / delta draw / lifetime; the spawn helper's delta
            # is applied contemporaneously so the copy moves with the line.
            # |delta| >= 1.5 BW keeps the copy clear of the line's eps- and
            # hysteresis-neighborhoods at every bar, so no clearance filter.
            rng_m = np.random.default_rng(seed_for(EXPERIMENT_ID, "mctrl", inst,
                                                   domain, rid))
            for lvl in spawn_control_levels(avwap_abs, bw_abs, c0 + 1, e0,
                                            CONTROL_SPACING_BARS,
                                            CONTROL_LIFETIME_BARS,
                                            DELTA_RANGE[0], DELTA_RANGE[1], rng_m):
                level_arr = avwap_abs + float(lvl["delta"]) * bw_abs
                emit(eps_abs, level_arr, "control_moving",
                     f"mctrl:{rid}:{lvl['spawn_idx']}",
                     int(lvl["alive_start"]), int(lvl["alive_end"]))
    frame = pl.DataFrame(rows)
    LOGGER.info("Episodes collected: %d (control clearance-dropped: %d)",
                frame.height, clearance_dropped)
    frame = frame.with_columns(pl.lit(clearance_dropped).alias("_clearance_dropped"))
    return frame


def assign_speed_terciles(episodes: pl.DataFrame) -> pl.DataFrame:
    """Speed terciles from pooled AVWAP-arm episodes per domain (both arms binned)."""
    out = []
    for domain in DOMAINS:
        sub = episodes.filter(pl.col("domain") == domain)
        ref = sub.filter((pl.col("arm") == "avwap") & pl.col("speed").is_finite())
        if ref.height == 0:
            out.append(sub.with_columns(
                pl.lit(-1).cast(pl.Int64).alias("speed_terc")))
            continue
        cuts = (float(ref.get_column("speed").quantile(TERCILE_EDGES[0])),
                float(ref.get_column("speed").quantile(TERCILE_EDGES[1])))
        out.append(sub.with_columns(
            pl.when(~pl.col("speed").is_finite()).then(-1)
            .when(pl.col("speed") <= cuts[0]).then(0)
            .when(pl.col("speed") <= cuts[1]).then(1)
            .otherwise(2).cast(pl.Int64).alias("speed_terc")))
    return pl.concat(out)


# --------------------------------------------------------------------------- #
# Matching and the binding contrast
# --------------------------------------------------------------------------- #
def match_controls(
    resolved: pl.DataFrame, domain: str, rng: np.random.Generator,
    control_arm: str = "control",
) -> tuple[pl.DataFrame, list[dict[str, Any]]]:
    """Covariate-match one control arm to the AVWAP arm per stratum.

    Strata = (instrument, entry_side, vol_terc, speed_terc); strata with
    fewer than ``MIN_STRATUM_EPISODES`` in either arm are excluded
    (disclosed). Controls are randomly subsampled per stratum to the AVWAP
    stratum proportions. ``control_arm`` selects the arm being matched
    (``control`` = binding static arm; ``control_moving`` = descriptive
    moving-copy arm, design §11/8); rows from any other arm are ignored.
    """
    sub = resolved.filter((pl.col("domain") == domain)
                          & (pl.col("vol_terc") >= 0) & (pl.col("speed_terc") >= 0))
    av_parts = sub.filter(pl.col("arm") == "avwap").partition_by(
        STRATA_COLS, as_dict=True)
    ct_parts = sub.filter(pl.col("arm") == control_arm).partition_by(
        STRATA_COLS, as_dict=True)
    valid = sorted(s for s, f in av_parts.items()
                   if f.height >= MIN_STRATUM_EPISODES
                   and s in ct_parts and ct_parts[s].height >= MIN_STRATUM_EPISODES)
    balance: list[dict[str, Any]] = []
    if not valid:
        return pl.DataFrame(), balance
    n_av_total = sum(av_parts[s].height for s in valid)
    n_target = min(int(np.floor(ct_parts[s].height * n_av_total
                                / av_parts[s].height)) for s in valid)
    kept_parts = []
    for s in valid:
        p_s = av_parts[s].height / n_av_total
        n_keep = max(1, min(ct_parts[s].height, int(round(p_s * n_target))))
        idx = rng.choice(ct_parts[s].height, size=n_keep, replace=False)
        kept_parts.append(ct_parts[s][np.sort(idx).tolist()])
        balance.append({"domain": domain, "control_arm": control_arm,
                        **{c: v for c, v in zip(STRATA_COLS, s)},
                        "n_avwap": av_parts[s].height,
                        "n_control_raw": ct_parts[s].height,
                        "n_control_kept": n_keep, "weight": p_s})
    matched = pl.concat([av_parts[s] for s in valid] + kept_parts)
    return matched, balance


def stratum_delta(matched: pl.DataFrame, weights: dict[tuple, float],
                  control_arm: str = "control") -> float:
    """Stratum-weighted bounce-rate difference (percentage points).

    One ``group_by`` pass; strata missing an arm (e.g. inside a bootstrap
    resample) drop out with weight renormalisation (documented in the plan).
    ``control_arm`` names the comparison arm in ``matched``.
    """
    if matched.height == 0:
        return float("nan")
    grouped = matched.group_by(STRATA_COLS + ["arm"]).agg(
        pl.len().alias("n"),
        (pl.col("outcome") == BOUNCE).cast(pl.Int64).sum().alias("n_bounce"))
    rates: dict[tuple, dict[str, float]] = {}
    for r in grouped.to_dicts():
        s = tuple(r[c] for c in STRATA_COLS)
        rates.setdefault(s, {})[str(r["arm"])] = r["n_bounce"] / r["n"]
    total = 0.0
    wsum = 0.0
    for s, w in weights.items():
        rr = rates.get(s)
        if not rr or "avwap" not in rr or control_arm not in rr:
            continue
        total += w * (rr["avwap"] - rr[control_arm])
        wsum += w
    return 100.0 * total / wsum if wsum > 0 else float("nan")


def cluster_ids(frame: pl.DataFrame) -> np.ndarray:
    """Cluster label per row: anchor segment (AVWAP) / frozen level (control)."""
    return (frame.get_column("instrument").to_numpy().astype(str) + "|"
            + frame.get_column("arm").to_numpy().astype(str) + "|"
            + frame.get_column("level_id").to_numpy().astype(str))


def bootstrap_delta(matched: pl.DataFrame, weights: dict[tuple, float],
                    seed: int,
                    control_arm: str = "control") -> tuple[float, float, float]:
    """Cluster bootstrap (per arm, per instrument) of the weighted Delta.

    Resamples whole clusters with replacement within (instrument, arm)
    groups; stratum weights stay frozen; empty strata drop with weight
    renormalisation inside ``stratum_delta``.
    """
    rng = np.random.default_rng(seed)
    cl = cluster_ids(matched)
    groups = (matched.get_column("instrument").to_numpy().astype(str) + "|"
              + matched.get_column("arm").to_numpy().astype(str))
    group_clusters = {g: np.unique(cl[groups == g]) for g in np.unique(groups)}
    members = {c: np.flatnonzero(cl == c) for c in np.unique(cl)}
    boots = []
    for _ in range(N_BOOT):
        parts = []
        for g, cs in group_clusters.items():
            draw = rng.choice(cs, size=cs.size, replace=True)
            parts.extend(members[c] for c in draw)
        idx = np.concatenate(parts)
        boots.append(stratum_delta(matched[np.sort(idx).tolist()], weights,
                                   control_arm))
    arr = np.asarray([b for b in boots if np.isfinite(b)])
    return (float(np.std(arr)), float(np.percentile(arr, CI_PERCENTILES[0])),
            float(np.percentile(arr, CI_PERCENTILES[1])))


def permutation_p_delta(matched: pl.DataFrame, weights: dict[tuple, float],
                        delta_obs: float, seed: int) -> tuple[float, int]:
    """One-sided cluster-label permutation p for Delta > 0.

    Within each instrument, the arm labels of whole clusters (anchor segments
    and frozen levels pooled) are randomly reassigned, preserving the
    cluster-count split per arm; Delta is recomputed under frozen strata
    definitions and weights. Returns ``(p, n_fallback_instruments)`` where the
    fallback counts instruments with < 2 clusters in either arm (their labels
    permute at the episode level inside the same scheme).
    """
    rng = np.random.default_rng(seed)
    cl = cluster_ids(matched)
    inst = matched.get_column("instrument").to_numpy().astype(str)
    arm = matched.get_column("arm").to_numpy().astype(str)
    plans: list[tuple[np.ndarray, np.ndarray, int]] = []
    n_fallback = 0
    for i in np.unique(inst):
        mask = inst == i
        clusters = np.unique(cl[mask])
        arm_of = {c: arm[cl == c][0] for c in clusters}
        n_av = sum(1 for c in clusters if arm_of[c] == "avwap")
        if n_av < 2 or (clusters.size - n_av) < 2:
            n_fallback += 1
            plans.append((np.flatnonzero(mask), np.empty(0, dtype=object), -1))
        else:
            plans.append((np.flatnonzero(mask), clusters, n_av))
    arms_orig = matched.get_column("arm").to_numpy().astype(object)
    count_ge = 0
    for _ in tqdm(range(N_PERM), desc="permutation", leave=False):
        new_arm = arms_orig.copy()
        for rows_idx, clusters, n_av in plans:
            if n_av < 0:
                perm = rng.permutation(new_arm[rows_idx])
                new_arm[rows_idx] = perm
            else:
                shuffled = rng.permutation(clusters)
                av_set = set(shuffled[:n_av].tolist())
                sub_cl = cl[rows_idx]
                new_arm[rows_idx] = np.where(
                    np.isin(sub_cl, list(av_set)), "avwap", "control")
        permuted = matched.with_columns(pl.Series("arm", new_arm.astype(str)))
        d = stratum_delta(permuted, weights)
        if np.isfinite(d) and d >= delta_obs:
            count_ge += 1
    return (1 + count_ge) / (1 + N_PERM), n_fallback


def holm_adjust_two(p_values: dict[str, float]) -> dict[str, float]:
    """Holm step-down adjustment for the two-domain binding family."""
    items = sorted(p_values.items(), key=lambda kv: kv[1])
    adjusted: dict[str, float] = {}
    running = 0.0
    for rank, (key, p) in enumerate(items):
        adj = min(1.0, (len(items) - rank) * p)
        running = max(running, adj)
        adjusted[key] = running
    return adjusted


def verdict_for(delta: float, ci_low: float, ci_high: float, holm_p: float,
                n_av: int, n_ct: int) -> str:
    """Scope-predeclared verdict classes (floor, FOR, AGAINST, INCONCLUSIVE).

    AGAINST-as-immaterial is symmetric in the point estimate (design §11
    amendment): CI_high < materiality AND CI_low <= 0 — FOR not met and all
    material effects excluded, regardless of the sign of delta.
    """
    if n_av < FLOOR_EPISODES_PER_ARM or n_ct < FLOOR_EPISODES_PER_ARM:
        return "BELOW_FLOOR_NO_VERDICT"
    if delta > 0.0 and ci_low > 0.0 and holm_p <= ALPHA:
        return "EVIDENCE_FOR"
    if ci_high <= 0.0:
        return "EVIDENCE_AGAINST"
    if ci_high < MATERIALITY_PP and ci_low <= 0.0:
        return "EVIDENCE_AGAINST_IMMATERIAL"
    return "INCONCLUSIVE_SPANS_ZERO"


def write_power_statement(counts: list[dict[str, Any]]) -> None:
    """Persist the realized-count power statement BEFORE any contrast read.

    Uses matched episode counts only — no outcome column is touched. Reports
    the worst-case (p = 0.5) unclustered binomial SE of Delta, the implied
    one-sided 95% minimal detectable Delta (optimistic under clustering), and
    per-cell flags for verdict classes structurally unreachable at realized n
    (scope §Power; design §11 amendment). Write-ordering: this file must
    exist before ``stratum_delta`` is first called on a matched set.
    """
    rows = []
    for c in counts:
        n_av, n_ct = int(c["n_avwap"]), int(c["n_control"])
        if n_av > 0 and n_ct > 0:
            se_pp = 100.0 * float(np.sqrt(0.25 / n_av + 0.25 / n_ct))
            mde_for = 1.645 * se_pp
            immaterial_reachable = bool(1.96 * se_pp < MATERIALITY_PP)
        else:
            se_pp, mde_for, immaterial_reachable = float("nan"), float("nan"), False
        rows.append({
            "contrast": c.get("contrast", "avwap_vs_static"),
            "binding": bool(c.get("binding", True)),
            "domain": c["domain"], "n_avwap": n_av, "n_control": n_ct,
            "binomial_se_pp_worst_case": se_pp,
            "mde_for_pp_one_sided_95": mde_for,
            "se_optimistic_under_clustering": True,
            "below_floor": bool(n_av < FLOOR_EPISODES_PER_ARM
                                or n_ct < FLOOR_EPISODES_PER_ARM),
            "against_immaterial_reachable": immaterial_reachable,
        })
    write_rows(RESULTS_DIR / "power_statement.csv", rows)
    LOGGER.info("Power statement persisted (counts only) BEFORE the binding contrast")


def censoring_sensitivity(episodes: pl.DataFrame) -> list[dict[str, Any]]:
    """Non-binding censoring bracket: Delta under extreme imputations.

    The arms censor differently (anchor-segment ends are informative
    trend-change events on the AVWAP arm; control-level lifetime ends are
    not), so excluding unresolved episodes can shift Delta directionally.
    Impute every unresolved episode as a bounce, then as a pass (per arm,
    symmetric), re-match with the identical machinery, and report the
    point-estimate bracket (design §11 amendment; no CI, no test).
    """
    rows: list[dict[str, Any]] = []
    for domain in DOMAINS:
        row: dict[str, Any] = {"domain": domain}
        for impute in (BOUNCE, PASS_THROUGH):
            imputed = episodes.with_columns(
                pl.when(pl.col("outcome") == UNRESOLVED)
                .then(pl.lit(impute)).otherwise(pl.col("outcome")).alias("outcome"))
            rng = np.random.default_rng(
                seed_for(EXPERIMENT_ID, "sens", domain, impute))
            matched, balance = match_controls(imputed, domain, rng)
            weights = {tuple(b[c] for c in STRATA_COLS): b["weight"] for b in balance}
            row[f"delta_pp_all_{impute}"] = stratum_delta(matched, weights)
        sub = episodes.filter((pl.col("domain") == domain)
                              & (pl.col("outcome") == UNRESOLVED))
        row["n_unresolved_avwap"] = sub.filter(pl.col("arm") == "avwap").height
        row["n_unresolved_control"] = sub.filter(pl.col("arm") == "control").height
        rows.append(row)
    return rows


# --------------------------------------------------------------------------- #
# Descriptive decompositions (no new tests)
# --------------------------------------------------------------------------- #
def per_instrument_deltas(matched: pl.DataFrame, weights: dict[tuple, float],
                          domain: str) -> list[dict[str, Any]]:
    """Descriptive per-instrument Delta with cluster-bootstrap CIs."""
    rows = []
    for inst in INSTRUMENTS:
        sub = matched.filter(pl.col("instrument") == inst)
        w_inst = {s: w for s, w in weights.items() if s[0] == inst}
        if sub.height == 0 or not w_inst:
            rows.append({"domain": domain, "instrument": inst, "delta_pp": None,
                         "ci_low": None, "ci_high": None, "n_avwap": 0, "n_control": 0})
            continue
        d = stratum_delta(sub, w_inst)
        se, lo, hi = bootstrap_delta(sub, w_inst,
                                     seed_for(EXPERIMENT_ID, "instboot", domain, inst))
        rows.append({"domain": domain, "instrument": inst, "delta_pp": d,
                     "ci_low": lo, "ci_high": hi, "se": se,
                     "n_avwap": sub.filter(pl.col("arm") == "avwap").height,
                     "n_control": sub.filter(pl.col("arm") == "control").height})
    return rows


def split_half_delta(matched: pl.DataFrame, weights: dict[tuple, float],
                     domain: str) -> dict[str, Any]:
    """Chronological split-half Delta signs (stability disclosure, non-binding)."""
    med = float(matched.get_column("open_ns").median())
    out: dict[str, Any] = {"domain": domain, "split_median_ns": med}
    for name, cond in (("h1", pl.col("open_ns") <= med), ("h2", pl.col("open_ns") > med)):
        half = matched.filter(cond)
        out[f"{name}_delta_pp"] = stratum_delta(half, weights)
        out[f"{name}_n"] = half.height
    return out


# --------------------------------------------------------------------------- #
# Plotting (4)
# --------------------------------------------------------------------------- #
def plot_episode_accounting(episodes: pl.DataFrame, contrast: list[dict[str, Any]],
                            path: Path) -> None:
    """Episode counts by arm/outcome/domain incl. unresolved and floor status."""
    fig, axes = plt.subplots(1, len(DOMAINS), figsize=(6 * len(DOMAINS), 4.4))
    for ax, domain in zip(np.atleast_1d(axes), DOMAINS):
        sub = episodes.filter(pl.col("domain") == domain)
        cats = ["bounce", "pass", "unresolved"]
        x = np.arange(len(cats))
        arm_colors = {"avwap": "#3498db", "control": "#e67e22",
                      "control_moving": "#8e44ad"}
        for k, arm in enumerate(("avwap", "control", "control_moving")):
            counts = [sub.filter((pl.col("arm") == arm)
                                 & (pl.col("outcome") == c)).height for c in cats]
            ax.bar(x + (k - 1) * 0.28, counts, 0.26, label=arm,
                   color=arm_colors[arm])
        row = next(r for r in contrast if r["domain"] == domain)
        ax.set_title(f"{domain} (matched n: {row['n_avwap']}/{row['n_control']}; "
                     f"floor {FLOOR_EPISODES_PER_ARM})")
        ax.set_xticks(x)
        ax.set_xticklabels(cats)
        ax.set_ylabel("Episodes")
        ax.legend(fontsize=8)
    fig.suptitle("EXP-040 episode accounting", fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_delta_forest(contrast: list[dict[str, Any]],
                      inst_rows: list[dict[str, Any]],
                      moving_rows: list[dict[str, Any]], path: Path) -> None:
    """Binding pooled Delta per domain + subordinated descriptive cells.

    Subordinated rows: the moving-copy Delta_m (design §11/8) and the
    per-instrument cells — all descriptive, visually de-emphasised.
    """
    fig, ax = plt.subplots(figsize=(9, 6.5))
    ys, labels = [], []
    y = 0
    for domain in DOMAINS:
        row = next(r for r in contrast if r["domain"] == domain)
        ax.errorbar(row["delta_pp"], y,
                    xerr=[[row["delta_pp"] - row["ci_low"]],
                          [row["ci_high"] - row["delta_pp"]]],
                    fmt="o", color="#2e7d32", capsize=4, markersize=9)
        labels.append(f"{domain} POOLED vs static (Holm p={row['holm_p']:.3f}, "
                      f"{row['verdict']})")
        ys.append(y)
        y -= 1
        m = next((r for r in moving_rows if r["domain"] == domain), None)
        if m is not None and np.isfinite(m["delta_m_pp"]):
            ax.errorbar(m["delta_m_pp"], y,
                        xerr=[[m["delta_m_pp"] - m["ci_low"]],
                              [m["ci_high"] - m["delta_m_pp"]]],
                        fmt="D", color="#8e44ad", capsize=3, markersize=6)
            labels.append("   vs shifted moving copy (descriptive)")
            ys.append(y)
            y -= 1
        for r in [r for r in inst_rows if r["domain"] == domain]:
            if r["delta_pp"] is None:
                continue
            ax.errorbar(r["delta_pp"], y,
                        xerr=[[r["delta_pp"] - r["ci_low"]],
                              [r["ci_high"] - r["delta_pp"]]],
                        fmt="s", color="#95a5a6", capsize=2, markersize=5)
            labels.append(f"   {r['instrument']} (descriptive)")
            ys.append(y)
            y -= 1
        y -= 0.5
    ax.axvline(0, color="black", lw=0.9)
    ax.set_yticks(ys)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("Delta = P(bounce|AVWAP) - P(bounce|control)  (pp)")
    ax.set_title("EXP-040 HYP-001 contrast (binding = pooled rows only)")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_direction_breakdown(matched_by_domain: dict[str, pl.DataFrame],
                             path: Path) -> None:
    """Bounce rates by arm x entry direction per domain."""
    fig, axes = plt.subplots(1, len(DOMAINS), figsize=(6 * len(DOMAINS), 4.2))
    for ax, domain in zip(np.atleast_1d(axes), DOMAINS):
        matched = matched_by_domain[domain]
        x = np.arange(2)
        for k, arm in enumerate(("avwap", "control")):
            rates = []
            for side in (1, -1):
                sub = matched.filter((pl.col("arm") == arm)
                                     & (pl.col("entry_side") == side))
                rates.append(100.0 * sub.filter(pl.col("outcome") == BOUNCE).height
                             / sub.height if sub.height else np.nan)
            ax.bar(x + (k - 0.5) * 0.35, rates, 0.32, label=arm,
                   color="#3498db" if arm == "avwap" else "#e67e22")
        ax.set_xticks(x)
        ax.set_xticklabels(["from above (support)", "from below (resistance)"],
                           fontsize=8)
        ax.set_ylabel("Bounce rate (%)")
        ax.set_title(domain)
        ax.legend(fontsize=8)
    fig.suptitle("EXP-040 bounce rate by entry direction", fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_split_half(halves: list[dict[str, Any]], path: Path) -> None:
    """Delta per analysis-set half per domain."""
    fig, ax = plt.subplots(figsize=(7, 4.2))
    x = np.arange(len(DOMAINS))
    ax.bar(x - 0.18, [h["h1_delta_pp"] for h in halves], 0.34, label="half 1",
           color="#85c1e9")
    ax.bar(x + 0.18, [h["h2_delta_pp"] for h in halves], 0.34, label="half 2",
           color="#3498db")
    ax.axhline(0, color="black", lw=0.9)
    ax.set_xticks(x)
    ax.set_xticklabels(DOMAINS)
    ax.set_ylabel("Delta (pp)")
    ax.set_title("EXP-040 split-half stability (non-binding)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    """Run the EXP-040 HYP-001 direct S/R test end to end."""
    configure_logging()
    ensure_output_dirs()
    t0 = time.time()
    LOGGER.info("=== %s: HYP-001 direct line S/R test ===", EXPERIMENT_ID)

    cells = build_cells()
    episodes = collect_episodes(cells)
    clearance_dropped = int(episodes.get_column("_clearance_dropped")[0])
    episodes = episodes.drop("_clearance_dropped")
    episodes = assign_speed_terciles(episodes)
    resolved = episodes.filter(pl.col("outcome") != UNRESOLVED)
    n_unresolved = episodes.height - resolved.height

    contrast_rows: list[dict[str, Any]] = []
    inst_rows: list[dict[str, Any]] = []
    half_rows: list[dict[str, Any]] = []
    balance_rows: list[dict[str, Any]] = []
    matched_by_domain: dict[str, pl.DataFrame] = {}
    weights_by_domain: dict[str, dict[tuple, float]] = {}
    raw_p: dict[str, float] = {}
    # Matching pass first (counts only), so the power statement is persisted
    # BEFORE any contrast is computed (ordering-enforced; design §11 amendment).
    # Both control arms are matched here: static (binding) and moving copies
    # (descriptive secondary, design §11/8).
    matched_moving: dict[str, pl.DataFrame] = {}
    weights_moving: dict[str, dict[tuple, float]] = {}
    for domain in DOMAINS:
        rng = np.random.default_rng(seed_for(EXPERIMENT_ID, "match", domain))
        matched, balance = match_controls(resolved, domain, rng)
        balance_rows.extend(balance)
        matched_by_domain[domain] = matched
        weights_by_domain[domain] = {tuple(b[c] for c in STRATA_COLS): b["weight"]
                                     for b in balance}
        rng_m = np.random.default_rng(seed_for(EXPERIMENT_ID, "match_moving", domain))
        matched_m, balance_m = match_controls(resolved, domain, rng_m,
                                              control_arm="control_moving")
        balance_rows.extend(balance_m)
        matched_moving[domain] = matched_m
        weights_moving[domain] = {tuple(b[c] for c in STRATA_COLS): b["weight"]
                                  for b in balance_m}
    write_power_statement(
        [{"contrast": "avwap_vs_static", "binding": True, "domain": d,
          "n_avwap": matched_by_domain[d].filter(pl.col("arm") == "avwap").height,
          "n_control": matched_by_domain[d].filter(pl.col("arm") == "control").height}
         for d in DOMAINS]
        + [{"contrast": "avwap_vs_moving", "binding": False, "domain": d,
            "n_avwap": matched_moving[d].filter(pl.col("arm") == "avwap").height,
            "n_control": matched_moving[d].filter(
                pl.col("arm") == "control_moving").height}
           for d in DOMAINS])

    for domain in DOMAINS:
        matched = matched_by_domain[domain]
        weights = weights_by_domain[domain]
        n_av = matched.filter(pl.col("arm") == "avwap").height
        n_ct = matched.filter(pl.col("arm") == "control").height
        delta = stratum_delta(matched, weights)
        se, lo, hi = bootstrap_delta(matched, weights,
                                     seed_for(EXPERIMENT_ID, "boot", domain))
        p, n_fallback = permutation_p_delta(matched, weights, delta,
                                            seed_for(EXPERIMENT_ID, "perm", domain))
        raw_p[domain] = p
        contrast_rows.append({"domain": domain, "delta_pp": delta, "se": se,
                              "ci_low": lo, "ci_high": hi, "perm_p": p,
                              "n_avwap": n_av, "n_control": n_ct,
                              "n_strata": len(weights),
                              "n_perm_fallback_instruments": n_fallback})
        inst_rows.extend(per_instrument_deltas(matched, weights, domain))
        half_rows.append(split_half_delta(matched, weights, domain))
        LOGGER.info("%s: Delta=%.2f pp CI[%.2f, %.2f] p=%.4f (n=%d/%d)",
                    domain, delta, lo, hi, p, n_av, n_ct)

    holm = holm_adjust_two(raw_p)
    for row in contrast_rows:
        row["holm_p"] = holm[row["domain"]]
        row["verdict"] = verdict_for(row["delta_pp"], row["ci_low"], row["ci_high"],
                                     row["holm_p"], row["n_avwap"], row["n_control"])

    # Descriptive moving-copy contrast (design §11/8): bootstrap CI only —
    # no permutation, no Holm, never a verdict input.
    moving_rows: list[dict[str, Any]] = []
    for domain in DOMAINS:
        matched_m = matched_moving[domain]
        weights_m = weights_moving[domain]
        if matched_m.height:
            d_m = stratum_delta(matched_m, weights_m, control_arm="control_moving")
            se_m, lo_m, hi_m = bootstrap_delta(
                matched_m, weights_m, seed_for(EXPERIMENT_ID, "boot_moving", domain),
                control_arm="control_moving")
        else:
            d_m = se_m = lo_m = hi_m = float("nan")
        moving_rows.append({
            "domain": domain, "delta_m_pp": d_m, "se": se_m,
            "ci_low": lo_m, "ci_high": hi_m,
            "n_avwap": matched_m.filter(pl.col("arm") == "avwap").height,
            "n_control_moving": matched_m.filter(
                pl.col("arm") == "control_moving").height,
            "n_strata": len(weights_m), "binding": False,
        })
        LOGGER.info("%s: Delta_m=%.2f pp CI[%.2f, %.2f] (descriptive, moving copy)",
                    domain, d_m, lo_m, hi_m)

    # Determinism replay: re-run the 4h bootstrap with the same seed.
    target = next(r for r in contrast_rows if r["domain"] == "4h")
    se2, lo2, hi2 = bootstrap_delta(matched_by_domain["4h"], weights_by_domain["4h"],
                                    seed_for(EXPERIMENT_ID, "boot", "4h"))
    drift = max(abs(se2 - target["se"]), abs(lo2 - target["ci_low"]),
                abs(hi2 - target["ci_high"]))
    replay = {"cell": "4h", "max_drift": drift, "passed": bool(drift <= DETERMINISM_TOL)}
    if not replay["passed"]:
        raise ValueError(f"DETERMINISM REPLAY FAILED: {replay}")

    # ---- persist results -------------------------------------------------------
    episodes.write_csv(RESULTS_DIR / "episodes.csv")
    write_rows(RESULTS_DIR / "matching_balance.csv", balance_rows)
    write_rows(RESULTS_DIR / "contrast_results.csv", contrast_rows)
    write_rows(RESULTS_DIR / "contrast_by_instrument.csv", inst_rows)
    write_rows(RESULTS_DIR / "split_half.csv", half_rows)
    sens_rows = censoring_sensitivity(episodes)
    write_rows(RESULTS_DIR / "censoring_sensitivity.csv", sens_rows)
    write_rows(RESULTS_DIR / "moving_control_contrast.csv", moving_rows)
    verdicts = {r["domain"]: r["verdict"] for r in contrast_rows}
    supported = any(v == "EVIDENCE_FOR" for v in verdicts.values())
    refuted = all(v in ("EVIDENCE_AGAINST", "EVIDENCE_AGAINST_IMMATERIAL")
                  for v in verdicts.values())
    overall = ("HYP001_SUPPORTED" if supported
               else "HYP001_REFUTED" if refuted else "HYP001_INCONCLUSIVE")
    metadata = {
        "experiment_id": EXPERIMENT_ID,
        "frozen_parameters": {
            "eps_mult": EPS_MULT, "hysteresis_mult": HYSTERESIS_MULT,
            "episode_cap_bars": EPISODE_CAP_BARS, "materiality_pp": MATERIALITY_PP,
            "delta_range_bw": DELTA_RANGE, "control_spacing_bars": CONTROL_SPACING_BARS,
            "control_lifetime_bars": CONTROL_LIFETIME_BARS,
            "control_line_clearance_bw": CONTROL_LINE_CLEARANCE_BW,
            "speed_lookback_bars": SPEED_LOOKBACK_BARS,
            "atr_period": ATR_PERIOD, "vol_window_days": VOL_WINDOW_DAYS,
            "n_boot": N_BOOT, "n_perm": N_PERM, "alpha": ALPHA,
            "floor_episodes_per_arm": FLOOR_EPISODES_PER_ARM,
            "min_stratum_episodes": MIN_STRATUM_EPISODES,
            "moving_control_arm": ("AVWAP(t) + delta*BW(t), same delta draw/"
                                   "grid/lifetime as static arm; descriptive "
                                   "only (design §11/8)"),
        },
        "episode_accounting": {
            "total": episodes.height, "resolved": resolved.height,
            "unresolved_excluded": n_unresolved,
            "control_clearance_dropped": clearance_dropped,
            "by_arm": {arm: episodes.filter(pl.col("arm") == arm).height
                       for arm in ("avwap", "control", "control_moving")},
        },
        "verdicts": verdicts, "holm_p": holm, "overall_verdict": overall,
        "power_statement_before_contrast": True,
        "censoring_sensitivity": sens_rows,
        "moving_control_contrast_descriptive": moving_rows,
        "determinism_replay": replay,
        "runtime_seconds": round(time.time() - t0, 1),
        "overall_status": "MEASUREMENT_COMPLETE",
    }
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(metadata, indent=2,
                                                              default=str))

    # ---- plots ---------------------------------------------------------------
    plot_episode_accounting(episodes, contrast_rows,
                            PLOTS_DIR / "episode_accounting.png")
    plot_delta_forest(contrast_rows, inst_rows, moving_rows,
                      PLOTS_DIR / "delta_forest.png")
    plot_direction_breakdown(matched_by_domain, PLOTS_DIR / "direction_breakdown.png")
    plot_split_half(half_rows, PLOTS_DIR / "split_half_stability.png")

    # ---- console summary -----------------------------------------------------
    for r in contrast_rows:
        LOGGER.info("%s: %s (Delta %.2f pp, Holm p %.4f)", r["domain"], r["verdict"],
                    r["delta_pp"], r["holm_p"])
    LOGGER.info("Overall: %s. Results in %s, plots in %s", overall, RESULTS_DIR,
                PLOTS_DIR)


if __name__ == "__main__":
    main()
