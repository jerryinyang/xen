"""P2 + P3 — median / trimmed-mean CIs and CI fragility, recovered as an ADDITIVE ADDENDUM.

Threads P2 and P3 from SPDR-018 analysis.md §14 and SPDR-018B analysis.md §12.

WHY THIS IS AN ADDENDUM AND NOT A RE-EMISSION
---------------------------------------------
Both quantities are computable from the parents' leg-level panels, which `arm_b.load_panel()`
exposes. Neither requires rewriting a frozen artifact:

  * P2 (median / 10% trimmed-mean block-bootstrap CIs) is gated behind
    `metrics.signed_cell(full=...)`, which the arms pass as `full=exhausted` — hence the 240 of
    24,098 coverage the analyst measured. Setting it True recovers them.
  * P3 (CI fragility: per-block CIs over blocks {1,3,7} days and the min/max seed range over the
    5 bootstrap seeds) is ALREADY COMPUTED on every cell of both runs, returned in
    `metrics.signed_cell()["_ci_detail"]`, and then discarded by `cells.py:127`, which explicitly
    skips `_ci_detail` when building the record. It is a serialisation gap, not a missing method.

NOTHING FROZEN IS TOUCHED. `screen_code/` is imported, never modified. The frozen `arm_*.parquet`
and `metrics_by_cell.parquet` are read for validation only. Output goes to NEW artifacts.

SELF-VALIDATION (the reason this is trustworthy)
-----------------------------------------------
Reproducing a cell's input series by regrouping the panel is the one place drift could enter. So
every recomputed cell must reproduce its FROZEN mean-family values -- mean, p, W, L, W_L, edge,
block_mde_mean_bps -- to a tight tolerance. If a cell fails, it is reported and EXCLUDED rather
than published. A cell that reproduces its frozen values was provably computed on the same input
series, which is what licenses trusting its new median/trimmed CIs.

Usage:  python analysis_code/p02_p03_full_ci.py [--jobs N] [--limit N] [--symbols A,B]
"""
from __future__ import annotations
import argparse, json, sys, time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
sys.path.insert(0, str(EXP / "screen_code"))

import arm_b                      # noqa: E402  parent panel loader + the arm's own grouping
import metrics                    # noqa: E402  the frozen statistics layer

RESULTS = EXP / "results"
TOL = 1e-9

# the mean-family columns that must reproduce exactly (validation contract)
VALIDATE = ("mean", "p", "W", "L", "W_L", "edge", "block_mde_mean_bps")


def powered_signed_keys() -> pd.DataFrame:
    """The frozen powered signed arm-B per-symbol cells, with their frozen values for validation."""
    m = pd.read_parquet(RESULTS / "arm_B.parquet")
    m = m[(m.at_parent_target_precision == True) & (m.basis == "per_symbol")]  # noqa: E712
    keep = ["symbol", "clock", "band", "signal", "exit_mode", "n", "n_dates"]
    keep += [f"gross_{c}" for c in VALIDATE if f"gross_{c}" in m.columns]
    return m[[c for c in keep if c in m.columns]].reset_index(drop=True)


def _fragility(detail: dict, name: str) -> dict:
    """Flatten the per-block / per-seed envelope that cells.py discards (P3)."""
    ci = detail.get(name)
    if not ci or not ci.get("per_block"):
        return {}
    out: dict = {}
    lo_seed_spans, hi_seed_spans, block_lo, block_hi = [], [], [], []
    for pb in ci["per_block"]:
        b = int(pb["block_days"])
        out[f"{name}_ci_low_block{b}"] = float(pb["ci"][0])
        out[f"{name}_ci_high_block{b}"] = float(pb["ci"][1])
        lo_r, hi_r = pb["ci_low_seed_range"], pb["ci_high_seed_range"]
        out[f"{name}_ci_low_seed_span_block{b}"] = float(lo_r[1] - lo_r[0])
        out[f"{name}_ci_high_seed_span_block{b}"] = float(hi_r[1] - hi_r[0])
        lo_seed_spans.append(lo_r[1] - lo_r[0])
        hi_seed_spans.append(hi_r[1] - hi_r[0])
        block_lo.append(pb["ci"][0])
        block_hi.append(pb["ci"][1])
    # headline fragility summaries
    out[f"{name}_ci_low_seed_span_max"] = float(max(lo_seed_spans))
    out[f"{name}_ci_high_seed_span_max"] = float(max(hi_seed_spans))
    out[f"{name}_ci_low_block_span"] = float(max(block_lo) - min(block_lo))
    out[f"{name}_ci_high_block_span"] = float(max(block_hi) - min(block_hi))
    width = ci["ci_high"] - ci["ci_low"]
    out[f"{name}_ci_width"] = float(width)
    # is the CI's sign conclusion stable across blocks and seeds?
    out[f"{name}_ci_low_sign_stable"] = bool(min(block_lo) > 0 or max(block_lo) < 0)
    out[f"{name}_seed_span_frac_of_width"] = (
        float(max(lo_seed_spans + hi_seed_spans) / width) if width > 0 else float("nan"))
    return out


def one_cell(job: dict) -> dict:
    """Recompute a single frozen cell with full=True, validate, and flatten the fragility."""
    panel = arm_b.load_panel()
    key = {k: job[k] for k in arm_b.KEYS}
    g = panel
    for k, v in key.items():
        g = g[g[k] == v]
    rec: dict = dict(key)
    rec["n_rows_regrouped"] = int(len(g))
    if len(g) == 0:
        rec["status"] = "REGROUP_EMPTY"
        return rec

    ts = g[arm_b.TS].to_numpy(dtype="int64")
    gross = g[arm_b.GROSS].to_numpy(dtype=float)
    net = g[arm_b.NET].to_numpy(dtype=float)
    cost = gross - net
    cost_mean = float(np.nanmean(cost)) if np.isfinite(cost).any() else 0.0

    t0 = time.time()
    out = metrics.signed_cell(gross, ts, cost_bps=cost_mean, full=True)
    rec["seconds"] = round(time.time() - t0, 2)

    # ---- validation contract: the frozen mean family must reproduce -------------------
    bad = []
    for c in VALIDATE:
        frozen = job.get(f"gross_{c}")
        got = out.get(c)
        if frozen is None or got is None or not np.isfinite(float(frozen)):
            continue
        denom = max(abs(float(frozen)), 1.0)
        if abs(float(got) - float(frozen)) / denom > 1e-6:
            bad.append(f"{c}: frozen={frozen!r} recomputed={got!r}")
    rec["status"] = "OK" if not bad else "VALIDATION_FAILED"
    rec["validation_detail"] = "; ".join(bad)
    if bad:
        return rec

    # ---- P2: the two point statistics and their recovered CIs -------------------------
    for f in ("n", "n_dates", "mean", "median", "trimmed_mean_10",
              "median_ci_low", "median_ci_high",
              "trimmed_mean_ci_low", "trimmed_mean_ci_high",
              "mean_ci_low", "mean_ci_high", "block_mde_mean_bps"):
        rec[f] = out.get(f)
    # the quantity L-51 / P2 exist to size
    if out.get("mean") is not None and out.get("median") is not None:
        rec["mean_minus_median_bps"] = float(out["mean"] - out["median"])
    # do the three statistics agree in sign?
    signs = {np.sign(out.get(k, np.nan)) for k in ("mean", "median", "trimmed_mean_10")}
    rec["three_stat_sign_agree"] = bool(len({s for s in signs if np.isfinite(s)}) == 1)

    # ---- P3: fragility of every CI that carries a read --------------------------------
    detail = out.get("_ci_detail", {})
    for name in ("mean", "p", "edge", "median", "trimmed_mean"):
        rec.update(_fragility(detail, name))
    return rec


def main() -> int:
    ap = argparse.ArgumentParser(description="P2+P3 addendum (additive; frozen artifacts untouched)")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--symbols", type=str, default="")
    ap.add_argument("--out", type=str, default="p02_p03_full_ci_armB.parquet")
    args = ap.parse_args()

    tgt = powered_signed_keys()
    if args.symbols:
        want = [s for s in args.symbols.split(",") if s]
        tgt = tgt[tgt.symbol.isin(want)]
    if args.limit:
        tgt = tgt.head(args.limit)
    jobs_list = tgt.to_dict("records")
    print(f"== P2+P3 addendum over {len(jobs_list)} frozen powered signed arm-B per-symbol cells")
    print(f"   jobs={args.jobs}  validation tolerance=1e-6 relative on {VALIDATE}")

    t0 = time.time()
    if args.jobs > 1:
        with ProcessPoolExecutor(max_workers=args.jobs) as ex:
            recs = list(ex.map(one_cell, jobs_list, chunksize=1))
    else:
        recs = [one_cell(j) for j in jobs_list]
    df = pd.DataFrame(recs)
    dt = time.time() - t0

    n_ok = int((df.status == "OK").sum())
    print(f"\n== {n_ok}/{len(df)} cells validated and recomputed in {dt/60:.1f} min")
    for st, k in df.status.value_counts().items():
        print(f"   {st}: {k}")
    if (df.status == "VALIDATION_FAILED").any():
        print("\n!! VALIDATION FAILURES — these cells are NOT published:")
        for _, r in df[df.status == "VALIDATION_FAILED"].head(10).iterrows():
            print(f"   {dict((k, r[k]) for k in arm_b.KEYS)}: {r.validation_detail}")

    ok = df[df.status == "OK"]
    if len(ok):
        print("\n== P2: do the three point statistics agree?")
        print(f"   sign agreement mean/median/trimmed : {ok.three_stat_sign_agree.mean():.3f}")
        print(f"   median(mean - median)              : {ok.mean_minus_median_bps.median():+.2f} bps")
        print(f"   p95 |mean - median|                : "
              f"{ok.mean_minus_median_bps.abs().quantile(0.95):.2f} bps")
        for c in ("mean", "median", "trimmed_mean_10"):
            print(f"   median across cells of {c:<16}: {ok[c].median():+.3f} bps")
        print("\n== P2: do the recovered median / trimmed CIs exclude zero?")
        for nm, lo, hi in (("median", "median_ci_low", "median_ci_high"),
                           ("trimmed", "trimmed_mean_ci_low", "trimmed_mean_ci_high"),
                           ("mean", "mean_ci_low", "mean_ci_high")):
            if lo in ok.columns:
                excl = ((ok[lo] > 0) | (ok[hi] < 0)).sum()
                neg = (ok[hi] < 0).sum()
                print(f"   {nm:<8} CI excludes 0 in {excl:>4} of {len(ok)}  "
                      f"({neg} negative, {excl - neg} positive)")
        print("\n== P3: CI fragility (seed span as a fraction of CI width)")
        for name in ("mean", "p", "edge", "median", "trimmed_mean"):
            c = f"{name}_seed_span_frac_of_width"
            if c in ok.columns and ok[c].notna().any():
                s = ok[c].dropna()
                print(f"   {name:<13} median {s.median():.4f}  p95 {s.quantile(0.95):.4f}  "
                      f"max {s.max():.4f}")
        for name in ("mean", "median"):
            c = f"{name}_ci_low_block_span"
            if c in ok.columns and ok[c].notna().any():
                s = ok[c].dropna()
                print(f"   {name} CI-low span across blocks {{1,3,7}}d: "
                      f"median {s.median():.3f}  p95 {s.quantile(0.95):.3f} bps")

    path = RESULTS / args.out
    df.to_parquet(path, index=False)
    print(f"\nwrote {path}  ({len(df)} rows, {len(df.columns)} cols)")
    return 0 if not (df.status == "VALIDATION_FAILED").any() else 1


if __name__ == "__main__":
    raise SystemExit(main())
