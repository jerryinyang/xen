"""
Experiment EXP-009: Broadened Untuned Strategy Effect-Size Distribution.

Phase 002 optional/context measurement. Computes a canonical breadth of six
untuned, fixed-parameter simple strategies on the first-70% analysis slice,
evaluates them with the frozen referees, and locates each net effect relative to
the EXP-003 pooled domain gate MDE. Exploratory: no per-strategy pass/fail. Reuses
the frozen ``xen.referee_calibration`` harness unchanged (Donchian/MA included);
the four added indicators live in the sibling experiment-local ``strategies``
module. Never loads the final 30% global holdout.
"""
from __future__ import annotations

import json
import logging
import math
import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from tqdm.auto import tqdm

from xen.referee_calibration import (
    ALPHA_GRID,
    DOMAIN_SPECS,
    build_domain_frames,
    domain_split_index,
    donchian_breakout_positions,
    evaluate_referees,
    list_timebar_files,
    load_analysis_data,
    ma_crossover_positions,
    next_log_returns_from_bars,
    seed_for,
    write_json,
)

# Experiment-local helper. Insert the script dir on path so the import resolves
# on a direct manual run. (xen is installed editable.)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from strategies import (  # noqa: E402  (local helper; needs script dir on path)
    BOLLINGER_NUM_STD,
    BOLLINGER_WINDOW,
    MACD_FAST,
    MACD_SIGNAL,
    MACD_SLOW,
    ROC_PERIOD,
    RSI_HIGH,
    RSI_LOW,
    RSI_PERIOD,
    STRATEGY_FAMILY,
    bollinger_positions,
    macd_positions,
    roc_positions,
    rsi_positions,
)


LOGGER = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-009"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = PROJECT_ROOT / "data"
EXPERIMENT_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
EXP003_METADATA = (
    PROJECT_ROOT / "python" / "experiments" / "EXP-003" / "results" / "run_metadata.json"
)
EXP003_MDE = PROJECT_ROOT / "python" / "experiments" / "EXP-003" / "results" / "mde_summary.csv"
EXP004_METADATA = (
    PROJECT_ROOT / "python" / "experiments" / "EXP-004" / "results" / "run_metadata.json"
)

# Reused frozen Donchian/MA parameters (match EXP-004).
DONCHIAN_LOOKBACK = 20
MA_FAST = 20
MA_SLOW = 50

ALPHA0 = 0.05
BOOTSTRAP_RESAMPLES = 1000
HEADLINE_REFEREE = "gate_stack"

# Scope dependency gate: EXP-004 must record this accepted success status, and the
# EXP-003 gate-stack alpha0 MDE rows for these domains must be present and finite.
EXP004_REQUIRED_STATUS = "PASS"
REQUIRED_MDE_DOMAINS: tuple[str, ...] = tuple(DOMAIN_SPECS.keys())
REQUIRED_MDE_REFEREE = "gate_stack"


# --------------------------------------------------------------------------- #
# Output helpers
# --------------------------------------------------------------------------- #
def configure_logging() -> None:
    """Configure concise INFO-level logging for the manual run."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")


def ensure_output_dirs() -> None:
    """Create the experiment ``results/`` and ``plots/`` directories."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write a list of result dicts to ``path`` as CSV."""
    pl.DataFrame(rows).write_csv(path)


# --------------------------------------------------------------------------- #
# Dependency gate and MDE map
# --------------------------------------------------------------------------- #
def require_dependencies() -> dict[str, str]:
    """Fail fast unless EXP-003 is COMPLETE (with MDE) and EXP-004 SUPPORTED/PASS.

    EXP-003/EXP-004 are measurement/anchor runs, so the gate is artifact-based,
    mirroring EXP-005. Per ``scope.md`` the gate must enforce the upstream
    *validity*, not merely artifact presence: EXP-003 ``COMPLETE`` and EXP-004
    recording its accepted success status (``PASS`` in the EXP-004 metadata, i.e.
    the H-dogfood SUPPORTED anchor). Finite gate-stack MDE rows are asserted
    separately in :func:`load_mde_map`.

    Returns
    -------
    dict[str, str]
        Recorded upstream statuses for ``run_metadata.json``.
    """
    if not EXP003_METADATA.exists():
        raise FileNotFoundError(f"EXP-003 metadata not found: {EXP003_METADATA}")
    exp003 = json.loads(EXP003_METADATA.read_text(encoding="utf-8"))
    if exp003.get("overall_status") != "COMPLETE":
        raise RuntimeError(f"EXP-003 is not COMPLETE: {exp003.get('overall_status')}")
    if not EXP003_MDE.exists():
        raise FileNotFoundError(f"EXP-003 MDE summary not found: {EXP003_MDE}")
    if not EXP004_METADATA.exists():
        raise FileNotFoundError(f"EXP-004 metadata not found: {EXP004_METADATA}")
    exp004 = json.loads(EXP004_METADATA.read_text(encoding="utf-8"))
    exp004_status = str(exp004.get("overall_status"))
    if exp004_status != EXP004_REQUIRED_STATUS:
        raise RuntimeError(
            f"EXP-004 consistency anchor did not pass: overall_status="
            f"{exp004_status!r}, required {EXP004_REQUIRED_STATUS!r}"
        )
    return {
        "exp003_status": str(exp003.get("overall_status")),
        "exp004_status": exp004_status,
    }


def load_mde_map() -> dict[tuple[str, str], dict[str, float]]:
    """Load the EXP-003 MDE map at alpha0, keyed by (domain, referee).

    Returns
    -------
    dict[tuple[str, str], dict[str, float]]
        ``{(domain, referee): {"mde_bps", "mde_grid_uncertainty_bps"}}``.
    """
    frame = pl.read_csv(EXP003_MDE).filter(pl.col("alpha") == ALPHA0)
    out: dict[tuple[str, str], dict[str, float]] = {}
    for row in frame.iter_rows(named=True):
        mde = row["mde_bps"]
        unc = row["mde_grid_uncertainty_bps"]
        out[(str(row["domain"]), str(row["referee"]))] = {
            "mde_bps": float(mde) if mde is not None else math.nan,
            "mde_grid_uncertainty_bps": float(unc) if unc is not None else math.nan,
        }
    # Fail loudly if the required gate-stack alpha0 MDE rows are missing or
    # non-finite (scope dependency + plan Step 1: "asserted finite"). Without
    # this, a missing/imprecise upstream map would silently degrade to `no_mde`
    # classifications, which the scope predeclares as Evidence AGAINST.
    missing: list[str] = []
    for domain in REQUIRED_MDE_DOMAINS:
        cell = out.get((domain, REQUIRED_MDE_REFEREE))
        if cell is None or not math.isfinite(cell["mde_bps"]):
            missing.append(domain)
    if missing:
        raise RuntimeError(
            f"EXP-003 MDE map missing finite {REQUIRED_MDE_REFEREE} alpha0={ALPHA0} "
            f"rows for domains {missing}; cannot anchor EXP-009 (Evidence AGAINST)."
        )
    return out


# --------------------------------------------------------------------------- #
# Strategy positions and evaluation
# --------------------------------------------------------------------------- #
def strategy_positions(domain_frame: pl.DataFrame) -> dict[str, np.ndarray]:
    """Compute all six untuned strategy positions aligned to next returns.

    Donchian and MA are reused from the frozen harness; RSI/Bollinger/MACD/ROC
    come from the experiment-local ``strategies`` module. All arrays have
    length ``domain_rows - 1`` (aligned to ``t -> t+1`` returns).
    """
    ordered = domain_frame.sort("CloseTime")
    high = np.asarray(ordered.get_column("High"), dtype=float)
    low = np.asarray(ordered.get_column("Low"), dtype=float)
    close = np.asarray(ordered.get_column("Close"), dtype=float)
    return {
        "donchian_20": donchian_breakout_positions(high, low, close, lookback=DONCHIAN_LOOKBACK),
        "ma_20_50": ma_crossover_positions(close, fast=MA_FAST, slow=MA_SLOW),
        "rsi_14": rsi_positions(close, period=RSI_PERIOD),
        "bollinger_20_2": bollinger_positions(
            close, window=BOLLINGER_WINDOW, num_std=BOLLINGER_NUM_STD
        ),
        "macd_12_26_9": macd_positions(close, fast=MACD_FAST, slow=MACD_SLOW, signal=MACD_SIGNAL),
        "roc_20": roc_positions(close, period=ROC_PERIOD),
    }


def classify_location(
    effect: float, ci_upper: float, mde: float, grid_unc: float
) -> tuple[str, float]:
    """Classify a net effect relative to its domain MDE (anchored to MDE, not 0).

    CI-aware per analysis-plan Step 5: a cell is ``below_MDE`` only when its
    block-bootstrap **CI upper bound** sits below the domain MDE (confidently
    below), not merely its point estimate. A cell whose point estimate is below
    the MDE but whose CI upper bound reaches or crosses it is **not** counted as
    below_MDE — it is ``near_MDE`` (the not-confidently-below middle band, which
    also subsumes the grid-uncertainty neighbourhood). This prevents overstating
    "the untuned set sits safely below the MDE" when the uncertainty interval
    still crosses it.

    Returns
    -------
    tuple[str, float]
        ``(location, gap_bps)`` where gap = ``effect - mde``. Location is
        ``below_MDE`` / ``near_MDE`` / ``at_or_above_MDE``; ``no_mde`` when the
        domain MDE is not finite.
    """
    if not math.isfinite(mde):
        return "no_mde", math.nan
    band = grid_unc if math.isfinite(grid_unc) else 0.0
    if effect >= mde:
        return "at_or_above_MDE", effect - mde
    if (mde - effect) <= band:
        return "near_MDE", effect - mde
    if math.isfinite(ci_upper) and ci_upper < mde:
        return "below_MDE", effect - mde
    # Point estimate below the MDE but the CI upper bound reaches/crosses it:
    # not confidently below, so classify as near (an explicit uncertainty band).
    return "near_MDE", effect - mde


def evaluate_domain(
    *,
    instrument: str,
    domain: str,
    domain_frame: pl.DataFrame,
    train_end_ts: Any,
    mde_map: dict[tuple[str, str], dict[str, float]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Evaluate all six strategies for one (instrument, domain) cell.

    Returns
    -------
    tuple[list, list, list]
        ``(verdict_rows, effect_rows, location_rows)``. ``verdict_rows`` span the
        full alpha grid and both referees; ``effect_rows`` / ``location_rows`` are
        the alpha0 subset used for the distribution and MDE-location read.
    """
    returns, aligned = next_log_returns_from_bars(domain_frame)
    split_index = domain_split_index(aligned, train_end_ts)
    verdict_rows: list[dict[str, Any]] = []
    effect_rows: list[dict[str, Any]] = []
    location_rows: list[dict[str, Any]] = []
    for name, positions in strategy_positions(domain_frame).items():
        for verdict in evaluate_referees(
            returns,
            positions,
            instrument=instrument,
            domain=domain,
            alpha_values=ALPHA_GRID,
            n_bootstrap=BOOTSTRAP_RESAMPLES,
            seed=seed_for(EXPERIMENT_ID, instrument, domain, name),
            split_index=split_index,
        ):
            labels = {"instrument": instrument, "domain": domain, "strategy": name}
            verdict_rows.append({**labels, **verdict})
            if float(verdict["alpha"]) != ALPHA0:
                continue
            referee = verdict["referee"]
            mde = mde_map.get((domain, referee), {})
            mde_bps = float(mde.get("mde_bps", math.nan))
            grid_unc = float(mde.get("mde_grid_uncertainty_bps", math.nan))
            location, gap = classify_location(
                float(verdict["effect_bps"]), float(verdict["ci_upper_bps"]), mde_bps, grid_unc
            )
            effect_rows.append(
                {
                    **labels,
                    "family": STRATEGY_FAMILY[name],
                    "referee": referee,
                    "effect_bps": verdict["effect_bps"],
                    "ci_lower_bps": verdict["ci_lower_bps"],
                    "ci_upper_bps": verdict["ci_upper_bps"],
                    "effective_n": verdict["effective_n"],
                    "block_length": verdict["block_length"],
                    "mde_bps": mde_bps,
                    "mde_grid_uncertainty_bps": grid_unc,
                    "location_vs_mde": location,
                    "gap_to_mde_bps": gap,
                }
            )
            location_rows.append(
                {
                    **labels,
                    "family": STRATEGY_FAMILY[name],
                    "referee": referee,
                    "effect_bps": verdict["effect_bps"],
                    "ci_upper_bps": verdict["ci_upper_bps"],
                    "mde_bps": mde_bps,
                    "location_vs_mde": location,
                    "ci_upper_below_mde": bool(
                        math.isfinite(mde_bps) and float(verdict["ci_upper_bps"]) < mde_bps
                    ),
                }
            )
    return verdict_rows, effect_rows, location_rows


# --------------------------------------------------------------------------- #
# Distribution summary
# --------------------------------------------------------------------------- #
def summarize_distribution(effect_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Per-(domain, referee) and per-(family, domain, referee) net-effect summary.

    Descriptive distribution: median/IQR/min/max plus below/near/at_or_above
    counts at the domain level, and median net effect per family.

    Returns
    -------
    list[dict[str, Any]]
        Rows tagged by ``group_kind`` (``domain`` or ``family``).
    """
    frame = pl.DataFrame(effect_rows)
    rows: list[dict[str, Any]] = []
    by_domain = frame.group_by(["domain", "referee"], maintain_order=True).agg(
        pl.col("effect_bps").median().alias("median_effect_bps"),
        pl.col("effect_bps").quantile(0.25).alias("p25_effect_bps"),
        pl.col("effect_bps").quantile(0.75).alias("p75_effect_bps"),
        pl.col("effect_bps").min().alias("min_effect_bps"),
        pl.col("effect_bps").max().alias("max_effect_bps"),
        pl.len().alias("n_cells"),
        (pl.col("location_vs_mde") == "below_MDE").sum().alias("n_below_mde"),
        (pl.col("location_vs_mde") == "near_MDE").sum().alias("n_near_mde"),
        (pl.col("location_vs_mde") == "at_or_above_MDE").sum().alias("n_at_or_above_mde"),
    )
    for record in by_domain.sort(["domain", "referee"]).iter_rows(named=True):
        rows.append({"group_kind": "domain", "family": "ALL", **record})
    by_family = frame.group_by(["family", "domain", "referee"], maintain_order=True).agg(
        pl.col("effect_bps").median().alias("median_effect_bps"),
        pl.col("effect_bps").min().alias("min_effect_bps"),
        pl.col("effect_bps").max().alias("max_effect_bps"),
        pl.len().alias("n_cells"),
    )
    for record in by_family.sort(["family", "domain", "referee"]).iter_rows(named=True):
        rows.append({"group_kind": "family", **record})
    return rows


# --------------------------------------------------------------------------- #
# Plotting (bounded summary inputs only)
# --------------------------------------------------------------------------- #
def plot_effect_forest(effect_rows: list[dict[str, Any]]) -> None:
    """Gate-stack net effect +/- CI per strategy x instrument, faceted by domain."""
    pdf = pl.DataFrame(effect_rows).filter(pl.col("referee") == HEADLINE_REFEREE).to_pandas()
    domains = sorted(pdf["domain"].unique())
    fig, axes = plt.subplots(1, len(domains), figsize=(5 * len(domains), 6), sharex=True)
    axes = axes if len(domains) > 1 else [axes]
    for ax, domain in zip(axes, domains):
        sub = pdf[pdf["domain"] == domain].sort_values(["strategy", "instrument"]).reset_index()
        ax.errorbar(
            sub["effect_bps"],
            range(len(sub)),
            xerr=[sub["effect_bps"] - sub["ci_lower_bps"], sub["ci_upper_bps"] - sub["effect_bps"]],
            fmt="o",
            markersize=3,
        )
        mde = sub["mde_bps"].iloc[0] if len(sub) else math.nan
        if math.isfinite(mde):
            ax.axvline(mde, color="red", linewidth=1, label=f"MDE={mde:g}")
        ax.axvline(0.0, color="grey", linewidth=0.8)
        ax.set_yticks(range(len(sub)), sub["strategy"] + " " + sub["instrument"], fontsize=5)
        ax.set_xlabel("Net effect (bps)")
        ax.set_title(str(domain))
        ax.legend(fontsize=7)
    fig.suptitle("Gate-stack net effect vs domain MDE (alpha=0.05)")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "effect_forest_vs_mde.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_gross_vs_net(effect_rows: list[dict[str, Any]]) -> None:
    """Scatter of minimal-baseline gross vs gate-stack net effect, coloured by domain."""
    frame = pl.DataFrame(effect_rows)
    gross = frame.filter(pl.col("referee") == "minimal_baseline").select(
        ["instrument", "domain", "strategy", "effect_bps"]
    ).rename({"effect_bps": "gross_bps"})
    net = frame.filter(pl.col("referee") == "gate_stack").select(
        ["instrument", "domain", "strategy", "effect_bps"]
    ).rename({"effect_bps": "net_bps"})
    merged = gross.join(net, on=["instrument", "domain", "strategy"], how="inner").to_pandas()
    fig, ax = plt.subplots(figsize=(7, 6))
    for domain, group in merged.groupby("domain"):
        ax.scatter(group["gross_bps"], group["net_bps"], label=str(domain), s=20)
    span = merged[["gross_bps", "net_bps"]]
    lim = [span.min().min(), span.max().max()]
    ax.plot(lim, lim, color="grey", linewidth=0.8, label="identity")
    ax.set_xlabel("Gross effect (minimal baseline, bps)")
    ax.set_ylabel("Net effect (gate stack, bps)")
    ax.set_title("Gross vs net effect (cost drag) at alpha=0.05")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "gross_vs_net_effect.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_net_distribution(effect_rows: list[dict[str, Any]]) -> None:
    """Per-domain net-effect distribution (box over cells) with the MDE marker."""
    pdf = pl.DataFrame(effect_rows).filter(pl.col("referee") == HEADLINE_REFEREE).to_pandas()
    domains = sorted(pdf["domain"].unique())
    data = [pdf[pdf["domain"] == d]["effect_bps"].to_numpy() for d in domains]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.boxplot(data, tick_labels=domains, showfliers=True)
    for idx, domain in enumerate(domains, start=1):
        mde = pdf[pdf["domain"] == domain]["mde_bps"].iloc[0]
        if math.isfinite(mde):
            ax.scatter([idx], [mde], color="red", marker="D", zorder=3)
    ax.axhline(0.0, color="grey", linewidth=0.8)
    ax.set_ylabel("Gate-stack net effect (bps)")
    ax.set_title("Net-effect distribution per domain (red diamond = MDE)")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "net_effect_distribution.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_location_matrix(location_rows: list[dict[str, Any]]) -> None:
    """Strategy x instrument location-vs-MDE matrix (gate stack), faceted by domain."""
    code_map = {"below_MDE": 0.0, "near_MDE": 1.0, "at_or_above_MDE": 2.0, "no_mde": np.nan}
    pdf = pl.DataFrame(location_rows).filter(pl.col("referee") == HEADLINE_REFEREE).to_pandas()
    pdf["code"] = pdf["location_vs_mde"].map(code_map)
    domains = sorted(pdf["domain"].unique())
    fig, axes = plt.subplots(1, len(domains), figsize=(4.5 * len(domains), 5), sharey=True)
    axes = axes if len(domains) > 1 else [axes]
    for ax, domain in zip(axes, domains):
        pivot = pdf[pdf["domain"] == domain].pivot_table(
            index="strategy", columns="instrument", values="code", aggfunc="max"
        )
        im = ax.imshow(pivot.values, aspect="auto", cmap="RdYlGn_r", vmin=0, vmax=2)
        ax.set_xticks(
            range(len(pivot.columns)), list(pivot.columns), rotation=45, ha="right", fontsize=7
        )
        ax.set_yticks(range(len(pivot.index)), list(pivot.index), fontsize=7)
        ax.set_title(str(domain))
    fig.suptitle("Location vs MDE (0=below, 1=near, 2=at/above)")
    fig.colorbar(im, ax=axes, fraction=0.046, pad=0.04)
    fig.savefig(PLOTS_DIR / "location_vs_mde_matrix.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_family_distribution(effect_rows: list[dict[str, Any]]) -> None:
    """Per-strategy net-effect box across instruments, faceted by domain (gate stack)."""
    pdf = pl.DataFrame(effect_rows).filter(pl.col("referee") == HEADLINE_REFEREE).to_pandas()
    domains = sorted(pdf["domain"].unique())
    strategies = sorted(pdf["strategy"].unique())
    fig, axes = plt.subplots(1, len(domains), figsize=(5 * len(domains), 5), sharey=True)
    axes = axes if len(domains) > 1 else [axes]
    for ax, domain in zip(axes, domains):
        sub = pdf[pdf["domain"] == domain]
        data = [sub[sub["strategy"] == s]["effect_bps"].to_numpy() for s in strategies]
        ax.boxplot(data, tick_labels=strategies, showfliers=False)
        mde = sub["mde_bps"].iloc[0] if len(sub) else math.nan
        if math.isfinite(mde):
            ax.axhline(mde, color="red", linewidth=1)
        ax.axhline(0.0, color="grey", linewidth=0.8)
        ax.set_xticklabels(strategies, rotation=90, fontsize=6)
        ax.set_title(str(domain))
    axes[0].set_ylabel("Net effect (bps)")
    fig.suptitle("Per-strategy net-effect distribution across instruments (red line = MDE)")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "per_family_distribution.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    """Run the EXP-009 broadened effect-size distribution and write results/plots."""
    configure_logging()
    ensure_output_dirs()
    dependency_status = require_dependencies()
    mde_map = load_mde_map()

    files = list_timebar_files(DATA_DIR)
    if not files:
        raise FileNotFoundError(f"No time-bar files found under {DATA_DIR / 'timebars'}")

    verdict_rows: list[dict[str, Any]] = []
    effect_rows: list[dict[str, Any]] = []
    location_rows: list[dict[str, Any]] = []
    analysis_rows: list[dict[str, Any]] = []
    for path in tqdm(files, desc="EXP-009 instruments"):
        data = load_analysis_data(path)
        for domain, frame in build_domain_frames(data.frame).items():
            analysis_rows.append(
                {
                    "instrument": data.instrument,
                    "source_file": data.source_file,
                    "domain": domain,
                    "domain_rows": frame.height,
                    "analysis_start": data.analysis_start,
                    "analysis_end": data.analysis_end,
                }
            )
            verdicts, effects, locations = evaluate_domain(
                instrument=data.instrument,
                domain=domain,
                domain_frame=frame,
                train_end_ts=data.train_end_ts,
                mde_map=mde_map,
            )
            verdict_rows.extend(verdicts)
            effect_rows.extend(effects)
            location_rows.extend(locations)

    distribution_rows = summarize_distribution(effect_rows)
    measurements_produced = bool(effect_rows) and bool(distribution_rows)
    overall_status = "COMPLETE" if measurements_produced else "INCONCLUSIVE"

    write_rows(RESULTS_DIR / "analysis_metadata.csv", analysis_rows)
    write_rows(RESULTS_DIR / "strategy_verdicts.csv", verdict_rows)
    write_rows(RESULTS_DIR / "strategy_effects.csv", effect_rows)
    write_rows(RESULTS_DIR / "effect_vs_mde.csv", location_rows)
    write_rows(RESULTS_DIR / "effect_distribution_summary.csv", distribution_rows)
    write_json(
        RESULTS_DIR / "run_metadata.json",
        {
            "experiment_id": EXPERIMENT_ID,
            "overall_status": overall_status,
            "measurements_produced": measurements_produced,
            "dependencies": dependency_status,
            "alpha0": ALPHA0,
            "alpha_grid": list(ALPHA_GRID),
            "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
            "strategies": {
                "donchian_20": {"lookback": DONCHIAN_LOOKBACK},
                "ma_20_50": {"fast": MA_FAST, "slow": MA_SLOW},
                "rsi_14": {"period": RSI_PERIOD, "low": RSI_LOW, "high": RSI_HIGH},
                "bollinger_20_2": {"window": BOLLINGER_WINDOW, "num_std": BOLLINGER_NUM_STD},
                "macd_12_26_9": {"fast": MACD_FAST, "slow": MACD_SLOW, "signal": MACD_SIGNAL},
                "roc_20": {"period": ROC_PERIOD},
            },
            "mde_map_alpha0": {f"{d}|{r}": v for (d, r), v in mde_map.items()},
        },
    )

    plot_effect_forest(effect_rows)
    plot_gross_vs_net(effect_rows)
    plot_net_distribution(effect_rows)
    plot_location_matrix(location_rows)
    plot_family_distribution(effect_rows)

    LOGGER.info("EXP-009 complete: %s", overall_status)
    LOGGER.info("Results: %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
