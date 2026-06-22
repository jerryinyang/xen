"""EXP-085 — TRAIN-only gross->net cost read-gate on the EXP-083 valid-candidate set (CF-CAPGEO-001).

HYP-004 cost layer (D0-amendment-002). Applies a predeclared conservative round-trip + holding-time
financing model to the realized exit paths of the **26 EXP-083 hash-pinned valid {candidate x stratum}
survivors** (4 S2-PASS + 22 S2-DEFERRED), on the **TRAIN region only**, and re-evaluates **net** per-event
expectancy + median per stratum (moving-block bootstrap one-sided CI_low), with the net matched-random
excess as a non-binding companion.

This is a **read-gate, not a confirm**: no frozen referee suite, no WF-EXPANDING, no TEST/holdout contact
(all reserved to EXP-084). Verdict in {NET_SURVIVES (>=1 survivor net exp & median CI_low > 0, per stratum),
NET_FLAT (none)}. Per-stratum only; no pooling as a binding statistic (LESSON-001).

Reuse-first: the survivor exit paths are re-resolved by importing the frozen EXP-083 orchestration
(``run_experiment.py``) and calling its building blocks unchanged (the ``ass_overlay.py`` pattern). The
per-event exit **bar** the financing leg needs — discarded by the frozen resolvers — is recovered by the new
``xen.capgeo_cost`` mirror, captured by **intercepting** the frozen resolver calls inside ``build_candidates``
(identical barrier params, reconciled to the frozen ``Resolution.ret`` within 1e-9). No frozen module is
edited; their source hashes are recorded unchanged from EXP-083.

Read region: TRAIN sub-split ``[0, int(analysis_rows*0.7))`` of the first-70% analysis set (== EXP-083). The
analysis-TEST stratum and the final-30% global holdout are never sliced. 0 counted TEST reads, 0 slots.

Run:
    cd python && python experiments/EXP-085/code/run_experiment.py
    # optional smoke: EXP085_N_BOOT=2000 python experiments/EXP-085/code/run_experiment.py
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

import xen.capgeo_cost as cost           # noqa: E402  (the one new module; exit mirror + cost overlay)
from xen.capgeo_cost import COST_CONSTANTS, HOLDING_DAYS_DEFINITION  # noqa: E402
from xen.capgeo_screen import one_sided_lo, two_sample_diff_lo       # noqa: E402  (frozen kernels)

LOGGER = logging.getLogger("EXP-085")

# --------------------------------------------------------------------------- #
# Path setup + reuse of the frozen EXP-083 orchestration
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-085"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
EXPERIMENT_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
_EXP083_RUN = PROJECT_ROOT / "python" / "experiments" / "EXP-083" / "code" / "run_experiment.py"
_EXP083_VALID_SET = PROJECT_ROOT / "python" / "experiments" / "EXP-083" / "results" \
    / "valid_candidate_set.json"

# --------------------------------------------------------------------------- #
# Constants (frozen; seeds recorded in run_metadata.json)
# --------------------------------------------------------------------------- #
EXP083_VALID_SHA = "fa4035f371a2ada656f05d697b709be48559e6a5ad322526f45dbbfccd8f3126"
SEED_BOOT_085 = 20260622           # net-bootstrap master seed (per-survivor keyed; recorded)
N_BOOT = int(os.environ.get("EXP085_N_BOOT", "10000"))   # binding 10_000 (scope); env lowers for smoke
_SRC = PROJECT_ROOT / "python" / "src" / "xen"
_FROZEN_MODULES = ["capgeo_screen", "capgeo_substrates", "capgeo_geometry", "domain_bars",
                   "capgeo_exits"]


def _load_module(path: Path, name: str):
    """Import a python file as a module (import-safe: the target's main() is __main__-guarded)."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:                       # pragma: no cover - defensive
        raise ImportError(f"Could not load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------- #
# Exit-bar interception — capture the frozen resolvers' exit indices (reconciled), no module edit
# --------------------------------------------------------------------------- #
class _ExitInterceptor:
    """Context manager: wrap ``rx``'s frozen resolver names so each call also records its exit path.

    Inside the ``with`` block, ``rx.build_candidates`` calls the frozen resolvers (unchanged values), and
    each wrapped call additionally runs the line-faithful ``capgeo_cost`` mirror on the *identical* args,
    reconciles the mirror's recomputed return/class against the frozen ``Resolution`` (HALT on mismatch),
    and stashes the recovered exit path keyed by ``id(Resolution)``. On exit the original names are
    restored. The frozen module files are never modified.
    """

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
                raise RuntimeError(f"EXP-085 HALT: exit-mirror reconciliation FAILED in {name}")
            self.paths[id(res)] = path
            return res
        return wrapped


# --------------------------------------------------------------------------- #
# Provenance — assert the EXP-083 valid-set internal content hash before any market read
# --------------------------------------------------------------------------- #
def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_valid_set(path: Path) -> dict:
    """Load the frozen valid set and assert its internal content hash == the pinned sha (HALT else).

    Reproduces EXP-083 ``_freeze_valid_set`` canonicalization exactly:
    ``sha256(json.dumps({"members": members, "holm_rule": holm_rule}, sort_keys=True, default=str))``.
    """
    data = json.loads(path.read_text())
    canonical = json.dumps({"members": data["members"], "holm_rule": data["holm_rule"]},
                           sort_keys=True, default=str)
    recomputed = hashlib.sha256(canonical.encode()).hexdigest()
    if recomputed != data["sha256"] or data["sha256"] != EXP083_VALID_SHA:
        raise RuntimeError(f"EXP-085 HALT: valid-set sha mismatch (recomputed {recomputed[:12]}, "
                           f"file {data['sha256'][:12]}, pin {EXP083_VALID_SHA[:12]})")
    if int(data["n_valid"]) != len(data["members"]):
        raise RuntimeError("EXP-085 HALT: valid-set n_valid != len(members)")
    return data


# --------------------------------------------------------------------------- #
# Pure computation — re-resolve one survivor cell's substrates under interception
# --------------------------------------------------------------------------- #
def assemble_cell(rx, train_frame: pl.DataFrame, instrument: str, period: int, cell_index: int,
                  summary: pl.DataFrame, substrates: set[str], itc: _ExitInterceptor) -> dict:
    """Build candidate + matched-control resolutions for the needed substrates of one cell.

    Mirrors ``rx.process_cell`` assembly up to ``build_candidates`` (reusing every frozen helper), under
    the active exit interceptor. ``period`` doubles as ``domain_minutes`` (DOMAIN_LABEL keys are minutes:
    15/60/240). Returns ``{substrate: (pin, ctrl_pin, cand_map, ctrl_map, domain_minutes, s_i)}``.
    """
    domain = rx.DOMAIN_LABEL[period]
    bars = rx.build_domain_bars(train_frame, period)
    ohlc = rx._real_ohlc(bars)
    if "TickVolume" in bars.columns:
        ohlc["volume"] = bars.get_column("TickVolume").to_numpy().astype(np.float64)
    atr = rx.wilder_atr(ohlc["high"], ohlc["low"], ohlc["close"], rx.ATR_PERIOD)
    es = rx.make_entrysets(bars, instrument, domain, cell_index)

    out: dict[str, tuple] = {}
    for s_i, sub in enumerate(rx.SUBSTRATE_ORDER):
        if sub not in substrates:
            continue
        srow = summary.filter((pl.col("instrument") == instrument) & (pl.col("domain") == domain)
                              & (pl.col("substrate") == rx._SUMMARY_SUBSTRATE[sub]))
        if srow.height == 0:
            continue
        stats = rx._cell_stats_from_summary(srow.row(0, named=True))
        pin = rx._path_inputs(bars, instrument, domain, sub, es[sub], ohlc, atr)
        atr_med = float(np.median(pin.atr_entry)) if pin.atr_entry.size else float("nan")
        ctrl_pin = rx._matched_control(bars, instrument, domain, ohlc, atr, pin, cell_index, s_i)
        cand_map = rx.build_candidates(pin, stats, atr_med)
        ctrl_map = rx.build_candidates(ctrl_pin, stats, atr_med)
        out[sub] = (pin, ctrl_pin, cand_map, ctrl_map, int(period), s_i)
    return out


def _net_arrays(resolution, exit_path, pin, domain_minutes: int, rt: float, fin: float):
    """Resolved-event (gross, net, cost decomposition, holding) arrays for one candidate Resolution."""
    mask = resolution.resolved
    gross = resolution.ret[mask]
    entry_idx = pin.entry_idx[mask]
    atr_entry = pin.atr_entry[mask]
    exit_idx = exit_path.exit_idx[mask]
    p_entry = pin.close[entry_idx]
    hold = cost.holding_days(entry_idx, exit_idx, domain_minutes)
    ec = cost.event_costs(gross, p_entry, atr_entry, hold, rt, fin)
    return gross, ec


# --------------------------------------------------------------------------- #
# Pure computation — per-survivor net read + verdict
# --------------------------------------------------------------------------- #
def _verdict(net_exp: float, net_exp_lo: float, net_med: float, net_med_lo: float) -> str:
    if net_exp_lo > 0.0 and net_med_lo > 0.0:
        return "NET_POS"
    if net_exp < 0.0 and net_med < 0.0:
        return "NET_NEG"
    return "NET_INCONCLUSIVE_SPANS_ZERO"


def score_survivor(member: dict, cell: dict, cand_index: dict, itc: _ExitInterceptor,
                   cell_index: int) -> dict:
    """Reconcile gross, apply costs, bootstrap net exp/median + matched-random companion for one survivor.

    Parameters
    ----------
    member : dict
        One EXP-083 valid-set member (substrate/instrument/domain/candidate/n_resolved/gross_exp/...).
    cell : dict
        ``assemble_cell`` output for the member's (instrument, domain) cell.
    cand_index : dict
        Stable candidate -> index map (deterministic bootstrap seeding).
    itc : _ExitInterceptor
        Holds the recovered exit paths keyed by ``id(Resolution)``.
    cell_index : int
        full-grid cell index (bootstrap seed component).

    Returns
    -------
    dict
        One ``cost_readgate`` result row (HALT via RuntimeError on a gross/exit reconciliation failure).
    """
    sub, cid = member["substrate"], member["candidate"]
    pin, ctrl_pin, cand_map, ctrl_map, domain_minutes, s_i = cell[sub]
    rt, fin = COST_CONSTANTS[member["instrument"]]

    cand_full = cand_map[cid][0]
    gross, ec = _net_arrays(cand_full, itc.paths[id(cand_full)], pin, domain_minutes, rt, fin)
    n_res = int(gross.shape[0])
    if n_res != int(member["n_resolved"]) or abs(float(np.mean(gross)) - float(member["gross_exp"])) \
            > cost.RECON_TOL:
        raise RuntimeError(f"EXP-085 HALT: gross reconciliation FAILED {sub}/{member['instrument']}/"
                           f"{member['domain']}/{cid}: n={n_res}(vs {member['n_resolved']}) "
                           f"mean={float(np.mean(gross)):.12f}(vs {member['gross_exp']:.12f})")

    rng = np.random.default_rng([SEED_BOOT_085, cell_index, s_i, cand_index[cid]])
    net_exp, net_exp_lo = one_sided_lo(ec.net, rng, "mean", n_boot=N_BOOT)
    net_med, net_med_lo = one_sided_lo(ec.net, rng, "median", n_boot=N_BOOT)

    ctrl_full = ctrl_map[cid][0]
    # The control has its own (independent) entry set, so its resolved arrays index ctrl_pin, not pin.
    _g_c, ec_c = _net_arrays(ctrl_full, itc.paths[id(ctrl_full)], ctrl_pin, domain_minutes, rt, fin)
    matched_excess_lo = two_sample_diff_lo(ec.net, ec_c.net, rng, "mean", n_boot=N_BOOT)

    cost_atr_mean = float(np.mean(ec.cost_total))
    txn_share = float(np.mean(ec.cost_txn)) / cost_atr_mean
    return {
        "substrate": sub, "instrument": member["instrument"], "domain": member["domain"],
        "candidate": cid, "s2_deferred": bool(member["s2_deferred"]), "n_resolved": n_res,
        "gross_exp": float(np.mean(gross)), "gross_med": float(np.median(gross)),
        "holding_days_mean": float(np.mean(ec.holding_days)), "cost_atr_mean": cost_atr_mean,
        "txn_share": txn_share, "fin_share": 1.0 - txn_share,
        "net_exp": net_exp, "net_exp_lo": net_exp_lo, "net_med": net_med, "net_med_lo": net_med_lo,
        "net_matched_excess_lo": matched_excess_lo,
        "net_verdict": _verdict(net_exp, net_exp_lo, net_med, net_med_lo),
    }


# --------------------------------------------------------------------------- #
# Plotting (bounded; from the 26-row cost_readgate table only)
# --------------------------------------------------------------------------- #
def _row_label(r) -> str:
    return f"{r['instrument']}-{r['domain']}/{r['candidate']}"


def plot_waterfall(pdf, path: Path) -> None:
    """Plot 1 — per-survivor gross->net expectancy with net CI_low whisker vs the zero line."""
    sns.set_theme(style="whitegrid")
    pdf = pdf.sort_values(["instrument", "domain", "candidate"]).reset_index(drop=True)
    y = np.arange(len(pdf))
    colours = ["tab:green" if not s2 else "tab:orange" for s2 in pdf["s2_deferred"]]
    fig, ax = plt.subplots(figsize=(10, max(6, 0.32 * len(pdf))))
    ax.scatter(pdf["gross_exp"], y, marker="o", facecolors="none", edgecolors="grey",
               s=40, label="gross expectancy", zorder=3)
    ax.scatter(pdf["net_exp"], y, c=colours, s=42, label="net expectancy", zorder=4)
    ax.hlines(y, pdf["net_exp_lo"], pdf["net_exp"], color=colours, lw=2, alpha=0.6, zorder=2)
    for yi, (g, n) in enumerate(zip(pdf["gross_exp"], pdf["net_exp"])):
        ax.plot([g, n], [yi, yi], color="lightgrey", lw=0.8, zorder=1)
    ax.axvline(0, color="black", ls="--", lw=1)
    ax.set_yticks(y, [_row_label(r) for _, r in pdf.iterrows()], fontsize=7)
    ax.set_xlabel("expectancy (ATR units)")
    ax.set_title("EXP-085 gross->net expectancy (whisker = net one-sided 95% CI_low)\n"
                 "green = S2-PASS, orange = S2-DEFERRED")
    ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_cost_decomposition(pdf, path: Path) -> None:
    """Plot 2 — per-survivor mean cost split into transaction vs financing (ATR units)."""
    sns.set_theme(style="whitegrid")
    pdf = pdf.sort_values("cost_atr_mean").reset_index(drop=True)
    txn = pdf["cost_atr_mean"] * pdf["txn_share"]
    fin = pdf["cost_atr_mean"] * pdf["fin_share"]
    y = np.arange(len(pdf))
    fig, ax = plt.subplots(figsize=(10, max(6, 0.32 * len(pdf))))
    ax.barh(y, txn, color="tab:blue", label="transaction (round-trip)")
    ax.barh(y, fin, left=txn, color="tab:red", label="financing (holding)")
    ax.set_yticks(y, [_row_label(r) for _, r in pdf.iterrows()], fontsize=7)
    ax.set_xlabel("mean per-event cost (ATR units)")
    ax.set_title("EXP-085 cost decomposition — transaction vs financing")
    ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_net_vs_gross(pdf, path: Path) -> None:
    """Plot 3 — net vs gross expectancy scatter with net=0 and gross=net reference lines."""
    sns.set_theme(style="whitegrid")
    cmap = {"NET_POS": "tab:green", "NET_INCONCLUSIVE_SPANS_ZERO": "tab:orange", "NET_NEG": "tab:red"}
    fig, ax = plt.subplots(figsize=(8, 7))
    for v, c in cmap.items():
        d = pdf[pdf["net_verdict"] == v]
        ax.scatter(d["gross_exp"], d["net_exp"], c=c, s=12 + np.sqrt(d["n_resolved"]),
                   alpha=0.8, edgecolors="none", label=f"{v} (n={len(d)})")
    lim = [min(pdf["gross_exp"].min(), pdf["net_exp"].min()) - 0.1,
           max(pdf["gross_exp"].max(), pdf["net_exp"].max()) + 0.1]
    ax.plot(lim, lim, color="black", ls="--", lw=1, label="gross = net")
    ax.axhline(0, color="grey", ls=":", lw=0.8)
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_xlabel("gross expectancy (ATR)")
    ax.set_ylabel("net expectancy (ATR)")
    ax.set_title("EXP-085 net vs gross expectancy (point size ~ sqrt(n))")
    ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def _build_grid(rx, val005):
    """Reproduce the EXP-083 instrument list + full grid (cell_index source) by loading all first-70%."""
    found, _missing = val005.discover_infr003_files()
    instruments = [s for s in val005.TARGET_SYMBOLS if s in found]
    loaded: dict[str, object] = {}
    for inst in tqdm(instruments, desc="load first-70%"):
        li, _seal, _status = val005.load_first70(found[inst])
        if li is not None:
            loaded[inst] = li
    instruments = [s for s in instruments if s in loaded]
    full_grid = [(inst, p) for inst in instruments for p in val005.DOMAINS]
    return loaded, full_grid


def _score_all(rx, members, loaded, full_grid, summary) -> list[dict]:
    """Score every survivor; one assemble per (instrument, domain) cell under a fresh interceptor."""
    period_of = {v: k for k, v in rx.DOMAIN_LABEL.items()}
    by_cell: dict[tuple[str, str], list[dict]] = {}
    for mem in members:
        by_cell.setdefault((mem["instrument"], mem["domain"]), []).append(mem)

    rows: list[dict] = []
    for (inst, domain), cell_members in tqdm(by_cell.items(), desc="cost cells"):
        period = period_of[domain]
        cell_index = full_grid.index((inst, period))
        substrates = {m["substrate"] for m in cell_members}
        li = loaded[inst]
        train_frame = li.frame.slice(0, int(int(li.frame.height) * 0.7))
        if not train_frame.get_column("CloseTime").is_sorted():
            raise RuntimeError(f"EXP-085 HALT: {inst}-{domain} TRAIN frame not CloseTime-sorted")
        with _ExitInterceptor(rx) as itc:
            cell = assemble_cell(rx, train_frame, inst, period, cell_index, summary, substrates, itc)
            for sub in cell:
                cand_index = {cid: i for i, cid in enumerate(cell[sub][2])}  # cell[sub][2] = cand_map
                for mem in (m for m in cell_members if m["substrate"] == sub):
                    rows.append(score_survivor(mem, cell, cand_index, itc, cell_index))
    return rows


def _fingerprint(rows: list[dict]) -> str:
    def _round(v):
        return round(v, 9) if isinstance(v, float) and np.isfinite(v) else v
    recs = sorted(({k: _round(v) for k, v in r.items()} for r in rows),
                  key=lambda d: (d["substrate"], d["instrument"], d["domain"], d["candidate"]))
    return hashlib.sha256(json.dumps(recs, sort_keys=True, default=str).encode()).hexdigest()


def _module_hashes() -> dict:
    return {m: _hash_file(_SRC / f"{m}.py") for m in _FROZEN_MODULES} \
        | {"capgeo_cost": _hash_file(_SRC / "capgeo_cost.py")}


def _write_outputs(df: pl.DataFrame, verdict: str, valid_data: dict, determinism_ok: bool) -> None:
    """Emit cost_readgate.{parquet,csv}, valid_net_set.json, run_metadata.json."""
    df.write_parquet(RESULTS_DIR / "cost_readgate.parquet")
    df.write_csv(RESULTS_DIR / "cost_readgate.csv")

    pos = df.filter(pl.col("net_verdict") == "NET_POS").select(
        ["substrate", "instrument", "domain", "candidate", "n_resolved",
         "net_exp", "net_exp_lo", "net_med", "net_med_lo", "net_matched_excess_lo"]).to_dicts()
    (RESULTS_DIR / "valid_net_set.json").write_text(json.dumps({
        "verdict": verdict, "n_net_pos": len(pos), "read_eligible_members": pos,
        "authorizes": "NOTHING — read-eligibility only; an EXP-084 counted read opens ONLY on additional "
                      "operator ratification at EXP-084's own D0 (D0-amendment-002).",
        "provenance": {"exp083_valid_set_sha256": EXP083_VALID_SHA,
                       "cost_constants_RT_F_bps": COST_CONSTANTS,
                       "holding_days_definition": HOLDING_DAYS_DEFINITION,
                       "seed_boot": SEED_BOOT_085, "n_boot": N_BOOT}}, indent=2, default=str))

    meta = {
        "experiment": EXPERIMENT_ID, "hypothesis": "HYP-004 cost read-gate (D0-amendment-002)",
        "generated_at": datetime.now(timezone.utc).isoformat(), "verdict": verdict,
        "n_survivors": int(df.height),
        "n_net_pos": int(df.filter(pl.col("net_verdict") == "NET_POS").height),
        "n_inconclusive": int(df.filter(
            pl.col("net_verdict") == "NET_INCONCLUSIVE_SPANS_ZERO").height),
        "n_net_neg": int(df.filter(pl.col("net_verdict") == "NET_NEG").height),
        "cost_model": {
            "round_trip_bps_per_instrument": {k: v[0] for k, v in COST_CONSTANTS.items()},
            "financing_bps_per_day_per_instrument": {k: v[1] for k, v in COST_CONSTANTS.items()},
            "conservative_binding": "RT = 2 x BASE (EXP-030); financing adverse-side (EXP-034)",
            "holding_days_definition": HOLDING_DAYS_DEFINITION,
            "ratification": "constants + holding-days definition OPERATOR-RATIFIED at Stage 4 "
                            "(2026-06-22): RT/F as proposed; holding-days = bar-count proxy. Frozen "
                            "before the TRAIN run; never tuned against outcomes",
            "atr_unit_conversion": "cost_ATR = (RT/1e4 + F/1e4 * holding_days) * P_entry / ATR_entry; "
                                   "net_ATR = gross_ATR - cost_ATR (identical resolved events)"},
        "binding_rule": "per-stratum: NET_POS iff net_exp CI_low_1s > 0 AND net_med CI_low_1s > 0; "
                        "NET_SURVIVES iff >=1 NET_POS; no pooling as a binding statistic (LESSON-001)",
        "read_region": "TRAIN sub-split [0, int(analysis_rows*0.7)); analysis-TEST + holdout never sliced",
        "seeds": {"SEED_BOOT_085": SEED_BOOT_085}, "n_boot": N_BOOT,
        "exp083_valid_set_sha256": EXP083_VALID_SHA,
        "exp083_valid_set_assert_ok": True,
        "reconciliation_ok": True, "determinism_ok": bool(determinism_ok),
        "exit_mirror": "xen.capgeo_cost line-faithful mirror of the 3 frozen resolver families "
                       "(static/fixed-horizon/partial); reconciled to frozen Resolution.ret within 1e-9 "
                       "and cls/mask exactly on every resolved event",
        "module_hashes": _module_hashes(),
        "holdout_untouched": True, "test_stratum_touched": False,
        "counted_test_reads": 0, "candidate_slots": 0,
        "notes": [
            "Read-gate input to G-018; does not itself close/open the family.",
            "Matched-random net excess is a non-binding companion (same cost on both arms).",
            "22 of 26 survivors are S2-DEFERRED low-n 4h cells (n=44-78): NET_INCONCLUSIVE_SPANS_ZERO "
            "is the expected, honest outcome; the binding power sits in AUDUSD-1h (n=988).",
            "VP-POC (USDCAD-4h) carries EXP-083's selection-on-geometry disclosure (POC-subsample).",
        ],
    }
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(meta, indent=2, default=str))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGGER.info("EXP-085 — TRAIN-only gross->net cost read-gate; N_BOOT=%d", N_BOOT)

    valid_data = assert_valid_set(_EXP083_VALID_SET)
    members = valid_data["members"]
    LOGGER.info("valid-set sha asserted (%s); %d survivors", EXP083_VALID_SHA[:12], len(members))

    rx = _load_module(_EXP083_RUN, "exp083_run_experiment")
    val005 = rx._load_val005()
    summary = pl.read_parquet(rx._EXP081_SUMMARY)
    loaded, full_grid = _build_grid(rx, val005)

    rows = _score_all(rx, members, loaded, full_grid, summary)
    replay = _score_all(rx, members, loaded, full_grid, summary)
    determinism_ok = _fingerprint(rows) == _fingerprint(replay)

    df = pl.DataFrame(rows).sort(["substrate", "instrument", "domain", "candidate"])
    n_pos = int(df.filter(pl.col("net_verdict") == "NET_POS").height)
    verdict = "NET_SURVIVES" if n_pos > 0 else "NET_FLAT"

    _write_outputs(df, verdict, valid_data, determinism_ok)
    pdf = df.to_pandas()
    plot_waterfall(pdf, PLOTS_DIR / "01_gross_to_net_waterfall.png")
    plot_cost_decomposition(pdf, PLOTS_DIR / "02_cost_decomposition.png")
    plot_net_vs_gross(pdf, PLOTS_DIR / "03_net_vs_gross.png")

    LOGGER.info("verdict=%s survivors=%d net_pos=%d determinism_ok=%s",
                verdict, df.height, n_pos, determinism_ok)
    LOGGER.info("results -> %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
