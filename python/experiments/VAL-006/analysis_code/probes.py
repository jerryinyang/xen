"""VAL-006 Phase 2b — falsification probes on the census positives.

P1  Censored-MTM-inclusive totals: for exits that let losers run (e1 has no SL/time-stop),
    realized per-leg P&L is survivorship-biased — completed legs are TP winners by
    construction. Honest total = realized net + marked-to-open P&L of censored legs.
P2  Exposure normalisation: totals are per-unit-notional bps summed across up to ~200
    concurrent legs. Report net per leg-bar of exposure and return on peak exposure.
P3  Shift collapse (corrected estimand): shift-twin per-leg mean / raw per-leg mean.
P4  The critical-017 candidate: e3/extend/z15 US2000 — net per leg with CI at frozen cost,
    plus cost sensitivity (cost at which CI_low crosses 0).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "python" / "src"))

from xen.adjudication import assemble_multileg_bps, per_leg_net  # noqa: E402
from xen.referee_adaptive import adaptive_cost_bps_for  # noqa: E402

DATA = ROOT / "data" / "strategy_runs"
RESULTS = ROOT / "python" / "experiments" / "VAL-006" / "results"
SEED, N_BOOT, BLOCK, ALPHA = 20260704, 10_000, 5, 0.05


def cell_dirs(root: str):
    for rd in sorted((DATA / root).iterdir()):
        if rd.is_dir() and (rd / "positions.parquet").exists():
            yield rd


def load(rd: Path):
    meta = json.loads((rd / "run_metadata.json").read_text())
    pos = pl.read_parquet(rd / "positions.parquet")
    cis = pl.read_parquet(rd / "cis_trades.parquet")
    return meta["symbol"], pos, cis


def boot_mean_ci(x: np.ndarray) -> tuple[float, float, float]:
    n = len(x)
    if n < 2:
        return (float(x[0]) if n else float("nan"),) * 3
    rng = np.random.default_rng(SEED)
    n_blocks = int(np.ceil(n / BLOCK))
    starts = rng.integers(0, max(n - BLOCK, 1), size=(N_BOOT, n_blocks))
    means = np.empty(N_BOOT)
    for b in range(N_BOOT):
        idx = (starts[b][:, None] + np.arange(BLOCK)[None, :]).ravel()[:n] % n
        means[b] = x[idx].mean()
    return float(x.mean()), float(np.quantile(means, ALPHA / 2)), \
        float(np.quantile(means, 1 - ALPHA / 2))


# ---------------------------------------------------------------- P1 + P2
def p1_p2(roots: list[str]) -> pl.DataFrame:
    rows = []
    for root in roots:
        parts = root.split("-")
        for rd in cell_dirs(root):
            inst, pos, cis = load(rd)
            cost = adaptive_cost_bps_for(inst, "4h")
            s = assemble_multileg_bps(pos, cis, cost_bps=cost)
            realized = float(s.net_bps.sum())
            honest = realized + s.censored_mtm_bps - cost * s.n_censored
            exp_bars = int(s.open_legs.sum())
            rows.append({
                "root": root, "instrument": inst,
                "n_legs_completed": s.n_legs - s.n_censored, "n_censored": s.n_censored,
                "realized_net_bps": realized,
                "censored_mtm_bps": float(s.censored_mtm_bps),
                "honest_total_bps": honest,
                "flipped_sign": bool(np.sign(honest) != np.sign(realized) and realized != 0),
                "exposure_leg_bars": exp_bars,
                "net_per_exposure_bar": honest / exp_bars if exp_bars else float("nan"),
                "peak_exposure_legs": int(s.open_legs.max()),
                "ann_ret_on_peak_exposure_pct": (honest / 1e4 /
                                                 max((s.times[-1] - s.times[0])
                                                     / np.timedelta64(1, "s")
                                                     / (365.25 * 24 * 3600), 1e-9)
                                                 / max(int(s.open_legs.max()), 1) * 100),
            })
    return pl.DataFrame(rows)


# ---------------------------------------------------------------- P3
SHIFT_PAIRS = [
    ("EXP-014b-4h-s8-extend-z15", "EXP-014b-4h-s8-extend-z15-shift"),
    ("EXP-014b-4h-s8-extend-z20", "EXP-014b-4h-s8-extend-z20-shift"),
    ("EXP-014c-4h-s8-e2-extend-z15", "EXP-014c-4h-s8-e2-extend-z15-shift"),
    ("EXP-014c-4h-s8-e3-extend-z15", "EXP-014c-4h-s8-e3-extend-z15-shift"),
]


def leg_mean(rd: Path) -> tuple[str, float]:
    inst, pos, cis = load(rd)
    cost = adaptive_cost_bps_for(inst, "4h")
    live = cis.filter(pl.col("RealizedBps").is_finite()
                      & pl.col("Censored").cast(pl.Boolean).not_())
    if not live.height:
        return inst, float("nan")
    return inst, float(per_leg_net(live, cost_bps=cost)["NetBps"].mean())


def p3() -> pl.DataFrame:
    rows = []
    for raw_root, shift_root in SHIFT_PAIRS:
        raw = dict(leg_mean(rd) for rd in cell_dirs(raw_root))
        sh = dict(leg_mean(rd) for rd in cell_dirs(shift_root))
        for inst in sorted(set(raw) & set(sh)):
            r, s_ = raw[inst], sh[inst]
            rows.append({"pair": raw_root, "instrument": inst,
                         "raw_leg_mean": r, "shift_leg_mean": s_,
                         "collapse_fraction": s_ / r if abs(r) > 1e-9 else float("nan")})
    return pl.DataFrame(rows)


# ---------------------------------------------------------------- P4
def p4() -> dict:
    rd = next(d for d in cell_dirs("EXP-014c-4h-s8-e3-extend-z15")
              if "us2000" in d.name)
    inst, pos, cis = load(rd)
    cost = adaptive_cost_bps_for(inst, "4h")
    live = cis.filter(pl.col("RealizedBps").is_finite()
                      & pl.col("Censored").cast(pl.Boolean).not_())
    gross = live.get_column("RealizedBps").to_numpy()
    out = {"instrument": inst, "frozen_cost_bps": cost, "n_legs": len(gross),
           "gross_per_leg": boot_mean_ci(gross),
           "net_per_leg_at_frozen_cost": boot_mean_ci(gross - cost)}
    # cost sensitivity: largest cost with CI_low > 0
    lo_at = {}
    for c in [0.0, 1.0, 2.0, 4.0, 6.0, 8.0, 10.0]:
        lo_at[c] = boot_mean_ci(gross - c)[1]
    out["ci_low_by_cost"] = lo_at
    out["breakeven_cost_ci_low"] = max((c for c, lo in lo_at.items() if lo > 0),
                                       default=None)
    return out


def main() -> None:
    e1_roots = ["EXP-014c-4h-s8-e1-extend-z15", "EXP-014c-4h-s8-e1-extend-z20",
                "EXP-014c-4h-s8-e1-allow-z15", "EXP-014c-4h-s8-e1-allow-z20"]
    other_roots = ["EXP-014b-4h-s8-extend-z15", "EXP-014b-4h-s8-extend-z20",
                   "EXP-014b-4h-s8-allow-z15", "EXP-014b-4h-s8-allow-z20",
                   "EXP-014c-4h-s8-e2-extend-z15", "EXP-014c-4h-s8-e2-extend-z20",
                   "EXP-014c-4h-s8-e3-extend-z15", "EXP-014c-4h-s8-e3-extend-z20",
                   "EXP-014b-4h-s8-blmkt-z15", "EXP-014b-4h-s8-blmkt-z20"]
    t12 = p1_p2(e1_roots + other_roots)
    t12.write_parquet(RESULTS / "probes_p1_p2.parquet")
    t3 = p3()
    t3.write_parquet(RESULTS / "probes_p3_shift.parquet")
    r4 = p4()
    (RESULTS / "probes_p4_us2000.json").write_text(json.dumps(r4, indent=2))

    pl.Config.set_tbl_rows(30)
    pl.Config.set_tbl_width_chars(200)
    print("== P1: e1 honest totals (censored MTM included) ==")
    print(t12.filter(pl.col("root").str.contains("e1-extend"))
          .select(["root", "instrument", "n_censored", "realized_net_bps",
                   "censored_mtm_bps", "honest_total_bps", "flipped_sign"]))
    print("\n== P1 flip census (all probed roots) ==")
    print(t12.group_by("root").agg(pl.col("flipped_sign").sum().alias("n_flips"),
                                   pl.len().alias("n")).sort("root"))
    print("\n== P2: exposure-normalised (non-e1 extend, honest) ==")
    print(t12.filter(~pl.col("root").str.contains("e1"))
          .sort("net_per_exposure_bar", descending=True)
          .select(["root", "instrument", "honest_total_bps", "net_per_exposure_bar",
                   "peak_exposure_legs", "ann_ret_on_peak_exposure_pct"]).head(15))
    print("\n== P3: shift collapse fractions (corrected estimand) ==")
    print(t3.sort(["pair", "instrument"]))
    print("\n== P4: US2000 e3/extend/z15 ==")
    print(json.dumps(r4, indent=2))


if __name__ == "__main__":
    main()
