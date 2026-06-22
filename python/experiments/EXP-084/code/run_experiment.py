"""EXP-084 — AVWAP-4h portfolio confirmation read of the net-surviving capture geometry (CF-CAPGEO-001).

HYP-004b (D0-amendment-003, operator-ratified). The single sanctioned out-of-sample confirmation read for
HYP-004, reframed to a **portfolio unit**: ``SUB-AVWAP`` 4h events pooled across NZDUSD + USDCAD + USTEC,
exited by the single pinned parameter-free ``AVWAP-FH`` rule, NET of the EXP-085 operator-ratified cost
model, adjudicated under the frozen ``WF-EXPANDING`` protocol (``xen.wf``) + the D4 G-018 conjunction, with
the separability gate (S1 ∧ S2) now **binding** on the pooled basket (pooled TRAIN n ≥ 120, vs the per-cell
n<120 that deferred S2 in EXP-083/085).

Binding verdict ∈ {CONFIRM, NOT_CONFIRM, INCONCLUSIVE_SPANS_ZERO}. INCONCLUSIVE is a pre-registered acceptable
(non-failure) outcome. Per-stratum (3 instruments) and per-arm (the other 10 exits) reads are **disclosure**
(binding=false). Ledger: portfolio-aggregate rule → disclosure against the 3 strata, **0 counted reads**
(caps stay 0/2).

Read region: the WF series is the **full analysis set** (first 70% of each file = ``li.frame``); the frozen
``WF-EXPANDING`` schedule tests on [50%, 100%] of that series. The selection region ([0, 70%] of the analysis
set) overlaps folds in [50%, 70%] — handled per operator decision (Option A): the protocol is unchanged and
the per-fold trajectory is disclosed with a per-event freshness flag (entry vs the 70% selection boundary),
so a CONFIRM is read on the fresh folds. The final-30% global holdout is **never** built, sliced, or folded
(``load_first70`` excludes it; asserted).

Run:
    cd python && python experiments/EXP-084/code/run_experiment.py
    # smoke: EXP084_N_BOOT=2000 EXP084_NULL_REPS=80 python experiments/EXP-084/code/run_experiment.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                       # noqa: E402
import polars as pl                      # noqa: E402
import seaborn as sns                    # noqa: E402
from tqdm.auto import tqdm               # noqa: E402

import xen.capgeo_cost as cost           # noqa: E402
import xen.wf as wf                      # noqa: E402  (frozen WF-EXPANDING machinery)
from xen.capgeo_cost import COST_CONSTANTS, HOLDING_DAYS_DEFINITION  # noqa: E402
from xen.capgeo_screen import (          # noqa: E402
    m_cell_margin,
    s2_tail_residual,
    two_sample_diff_lo,
)

LOGGER = logging.getLogger("EXP-084")

# --------------------------------------------------------------------------- #
# Path setup + reuse of frozen EXP-083 orchestration
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-084"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
EXPERIMENT_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
_EXP083_RUN = PROJECT_ROOT / "python" / "experiments" / "EXP-083" / "code" / "run_experiment.py"
_EXP083_VALID_SET = PROJECT_ROOT / "python" / "experiments" / "EXP-083" / "results" \
    / "valid_candidate_set.json"
_EXP083_SCREEN = PROJECT_ROOT / "python" / "experiments" / "EXP-083" / "results" \
    / "screen_results.parquet"
_SRC = PROJECT_ROOT / "python" / "src" / "xen"

# --------------------------------------------------------------------------- #
# Constants (frozen; seeds recorded in run_metadata.json)
# --------------------------------------------------------------------------- #
EXP083_VALID_SHA = "fa4035f371a2ada656f05d697b709be48559e6a5ad322526f45dbbfccd8f3126"
BASKET = ("NZDUSD", "USDCAD", "USTEC")        # 4h SUB-AVWAP basket members (D0-amendment-003)
BASKET_ORDER = {s: i for i, s in enumerate(BASKET)}   # deterministic tie-break order
DOMAIN = "4h"
PERIOD = 240                                  # 4h domain_minutes (bar-count financing)
PINNED_ARM = "AVWAP-FH"                        # single binding exit (pinned a-priori)
DISCLOSURE_ARMS = ("RR-1", "RR-1.5", "RR-2", "RR-3", "D1-MEDIAN-CAPTURE", "D2-TAIL-ROBUST",
                   "D3-CAPTURE-EFFICIENT", "PARTIAL-V2A", "V2A-ADVNONE", "VP-POC")
ALL_ARMS = (PINNED_ARM, *DISCLOSURE_ARMS)
SUBSTRATE = "SUB-AVWAP"
SELECTION_FRAC = 0.70                          # EXP-083/085 TRAIN selection boundary (analysis-set frac)
SEED_BOOT_084 = 20260622
N_BOOT = int(os.environ.get("EXP084_N_BOOT", "10000"))
NULL_REPS = int(os.environ.get("EXP084_NULL_REPS", "200"))      # m_cell synthetic-null replications
N_BOOT_NULL = int(os.environ.get("EXP084_N_BOOT_NULL", "1000"))  # inner bootstrap for m_cell
RECON_TOL = 1e-9
S2_FLOOR = 120                                 # separability S2 operating floor (pooled TRAIN)
FROZEN_MODULES = ["capgeo_screen", "capgeo_substrates", "capgeo_geometry", "domain_bars",
                  "capgeo_exits", "capgeo_cost"]


def _load_module(path: Path, name: str):
    """Import a python file as a module (import-safe: target main() is __main__-guarded)."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:                       # pragma: no cover - defensive
        raise ImportError(f"Could not load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --------------------------------------------------------------------------- #
# Exit-bar interception (identical to EXP-085 — capture frozen resolvers' exit indices, reconciled)
# --------------------------------------------------------------------------- #
class _ExitInterceptor:
    """Wrap rx's frozen resolvers so each call also records its reconciled exit path (no module edit)."""

    _WRAP = {
        "resolve_static_barrier": cost.static_barrier_exit,
        "resolve_fixed_horizon": cost.fixed_horizon_exit,
        "resolve_partial_two_leg": cost.partial_two_leg_exit,
    }

    def __init__(self, rx) -> None:
        self.rx = rx
        self.paths: dict[int, cost.ExitPath] = {}
        self._orig: dict[str, object] = {}

    def __enter__(self) -> "_ExitInterceptor":
        for name, mirror in self._WRAP.items():
            self._orig[name] = getattr(self.rx, name)
            setattr(self.rx, name, self._make(self._orig[name], mirror, name))
        return self

    def __exit__(self, *exc) -> None:
        for name, fn in self._orig.items():
            setattr(self.rx, name, fn)
        self._orig.clear()

    def _make(self, original, mirror, name):
        def wrapped(*args, **kwargs):
            res = original(*args, **kwargs)
            path = mirror(*args, **kwargs)
            if not cost.reconcile_exit_path(path, res.ret, res.cls):
                raise RuntimeError(f"EXP-084 HALT: exit-mirror reconciliation FAILED in {name}")
            self.paths[id(res)] = path
            return res
        return wrapped


# --------------------------------------------------------------------------- #
# Provenance
# --------------------------------------------------------------------------- #
def assert_valid_set(path: Path) -> dict:
    """Assert the EXP-083 valid-set internal content hash == the pin (HALT else). EXP-085 canonicalization."""
    data = json.loads(path.read_text())
    canonical = json.dumps({"members": data["members"], "holm_rule": data["holm_rule"]},
                           sort_keys=True, default=str)
    recomputed = hashlib.sha256(canonical.encode()).hexdigest()
    if recomputed != data["sha256"] or data["sha256"] != EXP083_VALID_SHA:
        raise RuntimeError(f"EXP-084 HALT: valid-set sha mismatch (recomputed {recomputed[:12]}, "
                           f"file {data['sha256'][:12]}, pin {EXP083_VALID_SHA[:12]})")
    return data


def _screen_gross() -> dict:
    """{(instrument): (n_resolved, gross_exp)} for SUB-AVWAP-4h AVWAP-FH from the EXP-083 screen anchor."""
    sr = pl.read_parquet(_EXP083_SCREEN).filter(
        (pl.col("substrate") == SUBSTRATE) & (pl.col("domain") == DOMAIN)
        & (pl.col("candidate") == PINNED_ARM) & (pl.col("instrument").is_in(list(BASKET))))
    return {r["instrument"]: (int(r["n_resolved"]), float(r["gross_exp"]))
            for r in sr.iter_rows(named=True)}


# --------------------------------------------------------------------------- #
# Pure computation — resolve one instrument's arms (net) + random AVWAP-FH on a given frame
# --------------------------------------------------------------------------- #
def _arm_net(resolution, exit_path, pin, close_epoch_s, boundary_epoch, rt, fin):
    """Net-return, event close-time, and freshness flag arrays for one candidate Resolution (resolved)."""
    mask = resolution.resolved
    gross = resolution.ret[mask]
    entry_idx = pin.entry_idx[mask]
    atr_entry = pin.atr_entry[mask]
    exit_idx = exit_path.exit_idx[mask]
    p_entry = pin.close[entry_idx]
    hold = cost.holding_days(entry_idx, exit_idx, PERIOD)
    ec = cost.event_costs(gross, p_entry, atr_entry, hold, rt, fin)
    ct = close_epoch_s[entry_idx]
    fresh = ct >= boundary_epoch                         # event beyond the 70% selection boundary
    return {"gross": gross, "net": ec.net, "close_t": ct, "fresh": fresh}


def resolve_instrument(rx, itc, frame, instrument, cell_index, arms):
    """Resolve all requested arms + random AVWAP-FH on ``frame`` for one instrument (net, close-time, fresh).

    Returns ``{"arms": {arm: {gross,net,close_t,fresh}}, "random": {...AVWAP-FH...}}``. ``boundary_epoch`` is
    the instrument's 70% selection boundary (1-minute analysis-set CloseTime at row int(0.7*height)).
    """
    rt, fin = COST_CONSTANTS[instrument]
    bars = rx.build_domain_bars(frame, PERIOD)
    ohlc = rx._real_ohlc(bars)
    if "TickVolume" in bars.columns:
        ohlc["volume"] = bars.get_column("TickVolume").to_numpy().astype(np.float64)
    atr = rx.wilder_atr(ohlc["high"], ohlc["low"], ohlc["close"], rx.ATR_PERIOD)
    es = rx.make_entrysets(bars, instrument, DOMAIN, cell_index)
    close_epoch = bars.get_column("CloseTime").dt.epoch("s").to_numpy().astype(np.float64)

    s_i = rx.SUBSTRATE_ORDER.index(rx.SUB_AVWAP)
    summary = pl.read_parquet(rx._EXP081_SUMMARY)
    srow = summary.filter((pl.col("instrument") == instrument) & (pl.col("domain") == DOMAIN)
                          & (pl.col("substrate") == rx._SUMMARY_SUBSTRATE[rx.SUB_AVWAP]))
    stats = rx._cell_stats_from_summary(srow.row(0, named=True))
    pin = rx._path_inputs(bars, instrument, DOMAIN, rx.SUB_AVWAP, es[rx.SUB_AVWAP], ohlc, atr)
    atr_med = float(np.median(pin.atr_entry)) if pin.atr_entry.size else float("nan")
    ctrl_pin = rx._matched_control(bars, instrument, DOMAIN, ohlc, atr, pin, cell_index, s_i)

    boundary_epoch = float(close_epoch[-1]) + 1.0        # default: all in-selection if frame is sub-split

    with itc:                                            # interceptor active during candidate build
        cand_map = rx.build_candidates(pin, stats, atr_med)
        ctrl_map = rx.build_candidates(ctrl_pin, stats, atr_med)
    out_arms = {}
    for arm in arms:
        res = cand_map[arm][0]
        out_arms[arm] = _arm_net(res, itc.paths[id(res)], pin, close_epoch, boundary_epoch, rt, fin)
    rnd_res = ctrl_map[PINNED_ARM][0]
    random = _arm_net(rnd_res, itc.paths[id(rnd_res)], ctrl_pin, close_epoch, boundary_epoch, rt, fin)
    return {"arms": out_arms, "random": random, "boundary_epoch": boundary_epoch,
            "close_epoch": close_epoch}


# --------------------------------------------------------------------------- #
# Pure computation — pooling, separability, WF aggregate, verdict
# --------------------------------------------------------------------------- #
def _pool(per_inst: dict, key: str, arm: str | None = None) -> dict:
    """Pool one arm's (or random's) events across instruments, sorted by (close_time, instrument order)."""
    nets, cts, fresh, insts = [], [], [], []
    for inst in BASKET:
        d = per_inst[inst]["arms"][arm] if key == "arm" else per_inst[inst]["random"]
        nets.append(d["net"])
        cts.append(d["close_t"])
        fresh.append(d["fresh"])
        insts.append(np.full(d["net"].shape[0], BASKET_ORDER[inst], dtype=np.int64))
    net = np.concatenate(nets)
    ct = np.concatenate(cts)
    fr = np.concatenate(fresh)
    iv = np.concatenate(insts)
    order = np.lexsort((iv, ct))                         # primary close-time, tie-break instrument order
    return {"net": net[order], "close_t": ct[order], "fresh": fr[order], "inst": iv[order]}


def _fold_trajectory(net: np.ndarray, fresh: np.ndarray) -> list[dict]:
    """Per-fold net exp/median + fresh-fraction over the frozen WF schedule (disclosure)."""
    n = net.shape[0]
    rows = []
    for f in wf.make_folds(n):
        seg = net[f.test_start:f.test_stop]
        seg_fresh = fresh[f.test_start:f.test_stop]
        if seg.shape[0] == 0:
            continue
        rows.append({
            "fold": f.index, "test_lo_frac": round(f.test_start / n, 4),
            "test_hi_frac": round(f.test_stop / n, 4), "fold_n": int(seg.shape[0]),
            "fold_net_exp": float(np.mean(seg)), "fold_net_med": float(np.median(seg)),
            "frac_fresh": float(np.mean(seg_fresh)),
            "fresh_fold": bool(np.mean(seg_fresh) > 0.999),
        })
    return rows


def _oos_returns(net: np.ndarray) -> np.ndarray:
    """The pooled WF test-region returns ([initial_frac, 1.0] of the series)."""
    folds = wf.make_folds(net.shape[0])
    return net[folds[0].test_start:]


def verdict_logic(exp_lo: float, exp_hi: float, m: float, med_lo: float, beats_lo: float,
                  s1: bool, s2: bool, n_oos: int, subfloor_all: bool) -> str:
    """G-018 conjunction → portfolio verdict (CONFIRM / NOT_CONFIRM / INCONCLUSIVE_SPANS_ZERO)."""
    confirm = (exp_lo > m) and (med_lo > 0.0) and (beats_lo > 0.0) and s1 and s2
    if confirm:
        return "CONFIRM"
    power_adequate = (n_oos >= 2 * wf.MIN_FOLD) and not subfloor_all
    spans_zero = (exp_lo <= 0.0 <= exp_hi)
    if spans_zero and not power_adequate:
        return "INCONCLUSIVE_SPANS_ZERO"
    return "NOT_CONFIRM"


# --------------------------------------------------------------------------- #
# Plotting (bounded; from the result table only)
# --------------------------------------------------------------------------- #
def plot_fold_trajectory(traj: list[dict], path: Path) -> None:
    """Plot 1 — per-fold net expectancy vs zero with the fresh [>=70%] region marked."""
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(9, 5.5))
    x = [r["test_hi_frac"] for r in traj]
    y = [r["fold_net_exp"] for r in traj]
    cols = ["tab:green" if r["fresh_fold"] else "tab:grey" for r in traj]
    ax.bar(range(len(traj)), y, color=cols, edgecolor="black")
    for i, r in enumerate(traj):
        ax.text(i, r["fold_net_exp"], f"n={r['fold_n']}\nfresh={r['frac_fresh']:.0%}",
                ha="center", va="bottom", fontsize=7)
    ax.axhline(0, color="black", ls="--", lw=1)
    ax.set_xticks(range(len(traj)), [f"f{r['fold']}\n[{r['test_lo_frac']:.0%}-{r['test_hi_frac']:.0%}]"
                                     for r in traj], fontsize=8)
    ax.set_ylabel("fold net expectancy (ATR)")
    ax.set_title("EXP-084 WF-fold net trajectory — green = fresh (test ≥ 70% selection boundary)")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_net_distribution(net: np.ndarray, q05: float, q05c: float, k_tail_bound: float,
                          path: Path) -> None:
    """Plot 2 — pooled-basket net distribution with the S2 catastrophe boundary + q05 marks."""
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.hist(net, bins=40, color="tab:blue", alpha=0.7, edgecolor="white")
    ax.axvline(0, color="grey", ls=":", lw=1)
    ax.axvline(k_tail_bound, color="purple", ls="--", lw=1.2, label=f"S2 catastrophe bound {k_tail_bound:.2f}")
    ax.axvline(q05, color="tab:red", ls="--", lw=1.2, label=f"q05 {q05:.2f}")
    ax.axvline(q05c, color="tab:orange", ls=":", lw=1.2, label=f"q05_control {q05c:.2f}")
    ax.set_xlabel("net return (ATR)")
    ax.set_ylabel("count")
    ax.set_title("EXP-084 pooled-basket net distribution (AVWAP-FH) with S2 tail marks")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_per_stratum(rows: list[dict], path: Path) -> None:
    """Plot 3 — per-instrument net WF expectancy + CI_low vs the pooled basket (disclosure)."""
    sns.set_theme(style="whitegrid")
    labels = [r["label"] for r in rows]
    exp = [r["net_exp"] for r in rows]
    lo = [r["net_exp_lo"] for r in rows]
    fig, ax = plt.subplots(figsize=(8, 5))
    y = np.arange(len(rows))
    colours = ["tab:blue" if r["binding"] else "tab:grey" for r in rows]
    ax.scatter(exp, y, c=colours, s=45, zorder=3)
    ax.hlines(y, lo, exp, color=colours, lw=2, alpha=0.6, zorder=2)
    ax.axvline(0, color="black", ls="--", lw=1)
    ax.set_yticks(y, labels, fontsize=8)
    ax.set_xlabel("net WF expectancy (ATR); whisker = one-sided 95% CI_low")
    ax.set_title("EXP-084 per-stratum disclosure vs pooled basket (blue = binding portfolio)")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_per_arm(rows: list[dict], path: Path) -> None:
    """Plot 4 — per-arm pooled-basket net WF expectancy + CI_low (disclosure)."""
    sns.set_theme(style="whitegrid")
    rows = sorted(rows, key=lambda r: r["net_exp"])
    labels = [r["arm"] for r in rows]
    exp = [r["net_exp"] for r in rows]
    lo = [r["net_exp_lo"] for r in rows]
    fig, ax = plt.subplots(figsize=(8, 6))
    y = np.arange(len(rows))
    colours = ["tab:blue" if r["arm"] == PINNED_ARM else "tab:grey" for r in rows]
    ax.scatter(exp, y, c=colours, s=40, zorder=3)
    ax.hlines(y, lo, exp, color=colours, lw=2, alpha=0.6, zorder=2)
    ax.axvline(0, color="black", ls="--", lw=1)
    ax.set_yticks(y, labels, fontsize=8)
    ax.set_xlabel("pooled-basket net WF expectancy (ATR); whisker = CI_low")
    ax.set_title("EXP-084 per-arm disclosure (blue = pinned binding AVWAP-FH)")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def _build_loaded(rx, val005):
    """Load first-70% (analysis set) for the basket instruments; return {inst: li} + full_grid."""
    found, _missing = val005.discover_infr003_files()
    instruments = [s for s in val005.TARGET_SYMBOLS if s in found]
    loaded = {}
    for inst in instruments:
        li, _seal, _status = val005.load_first70(found[inst])
        if li is not None:
            loaded[inst] = li
    instruments = [s for s in instruments if s in loaded]
    full_grid = [(inst, p) for inst in instruments for p in val005.DOMAINS]
    return loaded, full_grid


def _resolve_basket(rx, loaded, full_grid, frame_kind: str, arms):
    """Resolve all basket instruments on the TRAIN sub-split or FULL analysis frame. Returns per_inst dict."""
    per_inst = {}
    for inst in tqdm(BASKET, desc=f"resolve {frame_kind}"):
        cell_index = full_grid.index((inst, PERIOD))
        li = loaded[inst]
        h = int(li.frame.height)
        if frame_kind == "train":
            frame = li.frame.slice(0, int(h * SELECTION_FRAC))
        else:
            frame = li.frame                              # full analysis set (WF series)
        if not frame.get_column("CloseTime").is_sorted():
            raise RuntimeError(f"EXP-084 HALT: {inst} frame not CloseTime-sorted")
        itc = _ExitInterceptor(rx)
        d = resolve_instrument(rx, itc, frame, inst, cell_index, arms)
        if frame_kind == "full":                          # set the real 70% selection boundary epoch
            boundary_epoch = float(li.frame.get_column("CloseTime").dt.epoch("s")
                                   .to_numpy()[int(h * SELECTION_FRAC)])
            for arm in arms:
                ct = d["arms"][arm]["close_t"]
                d["arms"][arm]["fresh"] = ct >= boundary_epoch
            d["random"]["fresh"] = d["random"]["close_t"] >= boundary_epoch
            d["boundary_epoch"] = boundary_epoch
        per_inst[inst] = d
    return per_inst


def _reconcile_gross(per_inst_train: dict, anchor: dict) -> None:
    """Assert TRAIN-sub-split AVWAP-FH n_resolved + gross mean reproduce the EXP-083 screen (HALT else)."""
    for inst in BASKET:
        a = per_inst_train[inst]["arms"][PINNED_ARM]
        n_res, gross_exp = int(a["gross"].shape[0]), float(np.mean(a["gross"]))
        n_ref, g_ref = anchor[inst]
        if n_res != n_ref or abs(gross_exp - g_ref) > RECON_TOL:
            raise RuntimeError(f"EXP-084 HALT: gross reconciliation FAILED {inst}-4h/AVWAP-FH: "
                               f"n={n_res}(vs {n_ref}) mean={gross_exp:.12f}(vs {g_ref:.12f})")


def _wf_aggregate(net: np.ndarray, rng) -> wf.WFAggregate:
    return wf.aggregate_walk_forward(net, rng, kind="block", n_boot=N_BOOT)


def _safe_disclosure_agg(net: np.ndarray, rng) -> dict:
    """WF aggregate for a (possibly thin) disclosure arm/stratum; NaN row if below WF minimum, never HALT."""
    n = int(net.shape[0])
    # WF needs an initial-train slice + >=2 pooled test points; thin arms (e.g. VP-POC) degrade to NaN.
    if n < max(4, 2 * 1) or int(round((1.0 - wf.INITIAL_FRAC) * n)) < 2:
        nan = float("nan")
        return {"n": n, "net_exp": nan, "net_exp_lo": nan, "net_med": nan, "net_med_lo": nan}
    agg = _wf_aggregate(net, rng)
    return {"n": n, "net_exp": agg.expectancy, "net_exp_lo": agg.expectancy_lo,
            "net_med": agg.median, "net_med_lo": agg.median_lo}


def run_once(rx, loaded, full_grid, anchor) -> dict:
    """One full evaluation pass (binding + disclosure). Returns the result payload (no I/O)."""
    # TRAIN sub-split (reconciliation only) — AVWAP-FH.
    per_train = _resolve_basket(rx, loaded, full_grid, "train", (PINNED_ARM,))
    _reconcile_gross(per_train, anchor)
    # FULL analysis set (WF series) — all arms + random.
    per_full = _resolve_basket(rx, loaded, full_grid, "full", ALL_ARMS)

    basket = _pool(per_full, "arm", PINNED_ARM)
    random = _pool(per_full, "random")
    n_pool = basket["net"].shape[0]

    # --- separability on pooled TRAIN (initial 50% of the WF series) ---
    n_train = int(round(wf.INITIAL_FRAC * n_pool))
    bt = basket["net"][:n_train]
    rt_train = random["net"][:int(round(wf.INITIAL_FRAC * random["net"].shape[0]))]
    s2_ok_floor = n_train >= S2_FLOOR
    if not s2_ok_floor:
        # Process-level HALT (scope "Process-level HALT (not a result)" category; plan Step 3 / Risk 3 +
        # D0-amendment-003 §1.1/§5): an unadjudicable S2 must revert to deferred+disclosed and route to the
        # operator — it must NOT be folded into a binding NOT_CONFIRM (scope reserves NOT_CONFIRM for a leg
        # that fails WITH adequate power). Fires before any WF aggregate or binding verdict is computed.
        raise RuntimeError(
            f"EXP-084 HALT: pooled WF initial-train n_train={n_train} < S2_FLOOR={S2_FLOOR} — "
            "S2 unadjudicable; the key advance is lost; deferred+disclosed, route to operator "
            "(do not emit a binding verdict).")
    rng_m = np.random.default_rng([SEED_BOOT_084, 2])
    m_margin = m_cell_margin(rt_train, bt.shape[0], rng_m, "mean",
                             null_reps=NULL_REPS, n_boot=N_BOOT_NULL) if rt_train.shape[0] else float("nan")
    rng_s1 = np.random.default_rng([SEED_BOOT_084, 3])
    s1_excess_lo = two_sample_diff_lo(bt, rt_train, rng_s1, "mean", n_boot=N_BOOT)
    s1_pass = bool(np.isfinite(s1_excess_lo) and np.isfinite(m_margin) and s1_excess_lo > m_margin)
    tm, q05, q05c, s2_raw = s2_tail_residual(bt, rt_train)
    s2_pass = bool(s2_raw and s2_ok_floor)

    # --- one frozen WF-EXPANDING run on the pooled basket (binding aggregate) ---
    agg = _wf_aggregate(basket["net"], np.random.default_rng([SEED_BOOT_084, 10]))
    rng_b = np.random.default_rng([SEED_BOOT_084, 11])
    beats_lo = two_sample_diff_lo(_oos_returns(basket["net"]), _oos_returns(random["net"]),
                                  rng_b, "mean", n_boot=N_BOOT)
    n_oos = _oos_returns(basket["net"]).shape[0]
    subfloor_all = len(agg.subfloor_folds) >= agg.n_folds_used
    verdict = verdict_logic(agg.expectancy_lo, agg.expectancy_hi, m_margin, agg.median_lo,
                            beats_lo, s1_pass, s2_pass, n_oos, subfloor_all)

    traj = _fold_trajectory(basket["net"], basket["fresh"])
    from xen.capgeo_geometry import K_TAIL
    mad = float(np.median(np.abs(bt - np.median(bt)))) if bt.shape[0] else float("nan")
    k_tail_bound = float(np.median(bt) - K_TAIL * mad) if bt.shape[0] else float("nan")

    # --- disclosure: per-stratum (each instrument AVWAP-FH) + per-arm (pooled basket) ---
    per_stratum = []
    for inst in BASKET:
        a = per_full[inst]["arms"][PINNED_ARM]["net"]
        s = _safe_disclosure_agg(a, np.random.default_rng([SEED_BOOT_084, 20, BASKET_ORDER[inst]]))
        per_stratum.append({"label": f"{inst}-4h", "binding": False, **s})
    per_stratum.append({"label": "PORTFOLIO", "binding": True, "n": n_pool,
                        "net_exp": agg.expectancy, "net_exp_lo": agg.expectancy_lo,
                        "net_med": agg.median, "net_med_lo": agg.median_lo})
    per_arm = []
    for arm in ALL_ARMS:
        pooled = _pool(per_full, "arm", arm)["net"]
        a = _safe_disclosure_agg(pooled, np.random.default_rng([SEED_BOOT_084, 30, ALL_ARMS.index(arm)]))
        per_arm.append({"arm": arm, "binding": arm == PINNED_ARM, **a})

    return {
        "verdict": verdict, "n_pool": n_pool, "n_train_sep": n_train, "n_oos": n_oos,
        "m_margin": m_margin, "exp": agg.expectancy, "exp_lo": agg.expectancy_lo,
        "exp_hi": agg.expectancy_hi, "med": agg.median, "med_lo": agg.median_lo,
        "beats_random_lo": beats_lo, "s1_excess_lo": s1_excess_lo, "s1_pass": s1_pass,
        "s2_tailmass": tm, "s2_q05": q05, "s2_q05_control": q05c, "s2_floor_ok": s2_ok_floor,
        "s2_pass": s2_pass, "fold_sizes": list(agg.fold_sizes), "subfloor_folds": list(agg.subfloor_folds),
        "k_tail_bound": k_tail_bound, "trajectory": traj, "per_stratum": per_stratum,
        "per_arm": per_arm, "basket_net": basket["net"], "basket_fresh": basket["fresh"],
    }


def _fingerprint(payload: dict) -> str:
    keys = ["verdict", "n_pool", "m_margin", "exp", "exp_lo", "med", "med_lo", "beats_random_lo",
            "s1_excess_lo", "s2_tailmass", "s2_q05", "s1_pass", "s2_pass"]
    sub = {k: (round(payload[k], 9) if isinstance(payload[k], float) and np.isfinite(payload[k])
               else payload[k]) for k in keys}
    sub["per_arm"] = [(r["arm"], round(r["net_exp"], 9), round(r["net_exp_lo"], 9)) for r in
                      payload["per_arm"]]
    return hashlib.sha256(json.dumps(sub, sort_keys=True, default=str).encode()).hexdigest()


def _write_outputs(payload: dict, valid_data: dict, determinism_ok: bool, pin: str) -> None:
    """Emit portfolio_confirm.{parquet,csv} (binding + disclosure rows) and run_metadata.json."""
    rows = [{
        "binding": True, "unit": "portfolio", "row": "PORTFOLIO/AVWAP-FH", "n": payload["n_pool"],
        "n_train_sep": payload["n_train_sep"], "n_oos": payload["n_oos"], "m_margin": payload["m_margin"],
        "net_exp": payload["exp"], "net_exp_lo": payload["exp_lo"], "net_med": payload["med"],
        "net_med_lo": payload["med_lo"], "beats_random_lo": payload["beats_random_lo"],
        "s1_pass": payload["s1_pass"], "s2_tailmass": payload["s2_tailmass"], "s2_q05": payload["s2_q05"],
        "s2_q05_control": payload["s2_q05_control"], "s2_floor_ok": payload["s2_floor_ok"],
        "s2_pass": payload["s2_pass"], "verdict": payload["verdict"],
    }]
    for r in payload["per_stratum"]:
        if r["binding"]:
            continue
        rows.append({"binding": False, "unit": "stratum", "row": r["label"], "n": r["n"],
                     "net_exp": r["net_exp"], "net_exp_lo": r["net_exp_lo"], "net_med": r["net_med"],
                     "net_med_lo": r["net_med_lo"], "verdict": "disclosure"})
    for r in payload["per_arm"]:
        rows.append({"binding": False, "unit": "arm", "row": f"PORTFOLIO/{r['arm']}", "n": r["n"],
                     "net_exp": r["net_exp"], "net_exp_lo": r["net_exp_lo"], "net_med": r["net_med"],
                     "net_med_lo": r["net_med_lo"], "verdict": "disclosure"})
    for r in payload["trajectory"]:
        rows.append({"binding": False, "unit": "fold", "row": f"fold{r['fold']}", "n": r["fold_n"],
                     "net_exp": r["fold_net_exp"], "net_med": r["fold_net_med"],
                     "test_lo_frac": r["test_lo_frac"], "test_hi_frac": r["test_hi_frac"],
                     "frac_fresh": r["frac_fresh"], "fresh_fold": r["fresh_fold"],
                     "verdict": "disclosure"})
    df = pl.DataFrame(rows, infer_schema_length=None)
    df.write_parquet(RESULTS_DIR / "portfolio_confirm.parquet")
    df.write_csv(RESULTS_DIR / "portfolio_confirm.csv")

    # Counted-read accounting context: a conforming WF run would be +1 PER STRATUM, but the binding
    # ledger entry is the portfolio-aggregate DISCLOSURE (0 counted) — see ledger_note.
    run_spec = wf.RunSpec(stratum="PORTFOLIO(NZDUSD,USDCAD,USTEC)-4h", frozen_before_oos=True,
                          between_fold_selection=False, predeclared_aggregation=True,
                          holdout_used_as_fold=False)
    counted_ctx = wf.counted_reads(run_spec, prior_counted=0).__dict__
    counted = {"if_per_stratum_counted_each": counted_ctx,
               "binding_rule": "portfolio-aggregate disclosure -> 0 counted (see ledger_disclosure)"}
    meta = {
        "experiment": EXPERIMENT_ID, "hypothesis": "HYP-004b portfolio confirmation (D0-amendment-003)",
        "generated_at": datetime.now(timezone.utc).isoformat(), "verdict": payload["verdict"],
        "unit": "portfolio", "basket": list(BASKET), "domain": DOMAIN, "pinned_arm": PINNED_ARM,
        "binding_conjunction": "CONFIRM iff exp_lo>m AND med_lo>0 AND beats_random_lo>0 AND S1 AND S2",
        "frozen_suite": "xen.wf WF-EXPANDING aggregate (kind=block) + FPR-calibrated margin m "
                        "(EXP-070/077 instantiation); framework-era bps gate stack NOT used (unit-incompatible)",
        "wf_schedule": {"initial_frac": wf.INITIAL_FRAC, "step_frac": wf.STEP_FRAC,
                        "n_folds": wf.N_FOLDS, "min_fold": wf.MIN_FOLD, "kind": "block"},
        "separability": {"K_tail": 3.0, "tau_tail": 0.06, "delta": 0.40, "s2_floor": S2_FLOOR,
                         "n_train_sep": payload["n_train_sep"], "s2_floor_ok": payload["s2_floor_ok"],
                         "s1_excess_lo": payload["s1_excess_lo"], "m_margin": payload["m_margin"]},
        "cost_model": {"constants_RT_F_bps": {k: COST_CONSTANTS[k] for k in BASKET},
                       "holding_days_definition": HOLDING_DAYS_DEFINITION,
                       "note": "EXP-085 operator-ratified; applied per-instrument before pooling"},
        "wf_overlap_disclosure": "WF tests [50%,100%] of the analysis series; selection region was [0,70%]; "
                                 "per-fold fresh flag (entry >= 70% boundary) disclosed; protocol unchanged "
                                 "(Option A, operator-ratified); CONFIRM read on fresh folds.",
        "seeds": {"SEED_BOOT_084": SEED_BOOT_084}, "n_boot": N_BOOT, "null_reps": NULL_REPS,
        "n_boot_null": N_BOOT_NULL,
        "exp083_valid_set_sha256": EXP083_VALID_SHA, "exp083_valid_set_assert_ok": True,
        "hash_pin": pin, "reconciliation_ok": True, "determinism_ok": bool(determinism_ok),
        "module_hashes": {m: _hash_file(_SRC / f"{m}.py") for m in FROZEN_MODULES}
        | {"wf": _hash_file(_SRC / "wf.py")},
        "holdout_untouched": True, "test_stratum_in_analysis_only": True,
        "counted_test_reads": 0, "candidate_slots": 0,
        "ledger_disclosure": [f"{inst}-4h" for inst in BASKET],
        "ledger_note": "portfolio-aggregate rule (Phase-011 Track-C precedent): portfolio read = DISCLOSURE "
                       "against each member stratum; 0 counted reads; all 48 strata stay 0/2. The 3 basket "
                       "strata become 'disclosed' (basket-claim-only; future clean per-instrument read "
                       "weakened, EXP-032 precedent).",
        "counted_reads_context": counted,
        "notes": [
            "USTEC-4h/AVWAP-FH was NOT an individual EXP-085 survivor (USTEC's survivor was RR-1); "
            "AVWAP-FH is the a-priori PINNED basket arm applied uniformly (no per-instrument arm "
            "selection) — disclosed. Reconciled to the EXP-083 screen anchor (n=46, gross 1.806).",
            "INCONCLUSIVE_SPANS_ZERO is a pre-registered acceptable (non-failure) outcome.",
        ],
    }
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(meta, indent=2, default=str))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGGER.info("EXP-084 — AVWAP-4h portfolio confirmation read; N_BOOT=%d", N_BOOT)

    valid_data = assert_valid_set(_EXP083_VALID_SET)
    anchor = _screen_gross()
    LOGGER.info("valid-set sha asserted (%s); basket=%s anchor=%s",
                EXP083_VALID_SHA[:12], BASKET, {k: v[0] for k, v in anchor.items()})

    rx = _load_module(_EXP083_RUN, "exp083_run_experiment")
    val005 = rx._load_val005()
    loaded, full_grid = _build_loaded(rx, val005)
    for inst in BASKET:
        if inst not in loaded:
            raise RuntimeError(f"EXP-084 HALT: basket instrument {inst} not loaded")

    pin_obj = {"basket": list(BASKET), "arm": PINNED_ARM, "cost": {k: COST_CONSTANTS[k] for k in BASKET},
               "wf": {"initial": wf.INITIAL_FRAC, "step": wf.STEP_FRAC, "folds": wf.N_FOLDS},
               "sha": EXP083_VALID_SHA, "conjunction": "exp_lo>m & med_lo>0 & beats>0 & S1 & S2"}
    pin = hashlib.sha256(json.dumps(pin_obj, sort_keys=True).encode()).hexdigest()
    LOGGER.info("basket+rule hash-pinned before OOS: %s", pin[:16])

    payload = run_once(rx, loaded, full_grid, anchor)
    replay = run_once(rx, loaded, full_grid, anchor)
    determinism_ok = _fingerprint(payload) == _fingerprint(replay)

    _write_outputs(payload, valid_data, determinism_ok, pin)
    plot_fold_trajectory(payload["trajectory"], PLOTS_DIR / "01_wf_fold_trajectory.png")
    plot_net_distribution(payload["basket_net"], payload["s2_q05"], payload["s2_q05_control"],
                          payload["k_tail_bound"], PLOTS_DIR / "02_pooled_net_distribution.png")
    plot_per_stratum(payload["per_stratum"], PLOTS_DIR / "03_per_stratum_disclosure.png")
    plot_per_arm(payload["per_arm"], PLOTS_DIR / "04_per_arm_disclosure.png")

    LOGGER.info("verdict=%s n_pool=%d n_train_sep=%d (S2 floor ok=%s) determinism_ok=%s",
                payload["verdict"], payload["n_pool"], payload["n_train_sep"],
                payload["s2_floor_ok"], determinism_ok)
    LOGGER.info("exp=%.4f exp_lo=%.4f (m=%.4f) med_lo=%.4f beats_lo=%.4f S1=%s S2=%s(tm=%.4f)",
                payload["exp"], payload["exp_lo"], payload["m_margin"], payload["med_lo"],
                payload["beats_random_lo"], payload["s1_pass"], payload["s2_pass"],
                payload["s2_tailmass"])
    LOGGER.info("results -> %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
