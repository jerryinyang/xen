"""EXP-025 — CTRL-REF-RANDOM: random-entry reference arm dir_gap (design §6, deviation D4).

Entries: seed 2001, random TRAIN bars (post-warmup, DI direction defined), matched count =
that symbol's largest T1 TRAIN cell n. Estimand: dir_gap(H) = E[m_H | +DI] - E[m_H | -DI],
m_H = forward open-to-open return over H bars starting at the next bar open (bps).
Sampling is analysis-side per D4; regenerable from seed 2001 + the emitted bar calendar.
CI: circular block bootstrap; block chosen so a block spans >= H bars at the realised
median entry spacing (design: block >= H), sweep x0.5/x2 disclosed.
"""
import glob, json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
from xen.evaluation import block_bootstrap_ci

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
RES = os.path.join(os.path.dirname(__file__), "..", "results")
HOLDS = [12, 24, 36, 48]
SEED = 2001


def main() -> None:
    cuts = json.load(open(os.path.join(RES, "train_cuts.json")))
    counts = pd.read_csv(os.path.join(RES, "cell_counts.csv"))
    n_by_sym = counts.groupby("symbol")["n_train"].max().to_dict()
    rng = np.random.default_rng(SEED)

    rows = []
    for d in sorted(glob.glob(os.path.join(ROOT, "data", "strategy_runs", "EXP-025-ref", "htfdi_*"))):
        sym = json.load(open(os.path.join(d, "run_metadata.json")))["symbol"]
        p = pd.read_parquet(os.path.join(d, "positions.parquet"),
                            columns=["SourceCloseTime", "RealOpen", "TrendDir", "Warmup"])
        p["SourceCloseTime"] = pd.to_datetime(p["SourceCloseTime"])
        p = p.sort_values("SourceCloseTime").reset_index(drop=True)
        train = p["SourceCloseTime"] < pd.Timestamp(cuts[sym])
        opens = p["RealOpen"].to_numpy(float)
        tdir = p["TrendDir"].to_numpy(int)
        ok = train.to_numpy() & (~p["Warmup"].to_numpy(bool)) & (tdir != 0)
        max_h = max(HOLDS)
        idx_pool = np.flatnonzero(ok)
        idx_pool = idx_pool[idx_pool + 1 + max_h < len(opens)]
        n = min(n_by_sym[sym], len(idx_pool))
        idx = np.sort(rng.choice(idx_pool, size=n, replace=False))
        spacing = float(np.median(np.diff(idx))) if n > 1 else np.inf
        for h in HOLDS:
            m = (opens[idx + 1 + h] - opens[idx + 1]) / opens[idx + 1] * 1e4
            sign = tdir[idx]
            gap_stat = lambda a: np.nan  # placeholder, defined via paired arrays below
            pos, neg = m[sign > 0], m[sign < 0]
            # dir_gap CI: bootstrap the signed series w = m * sign_indicator via block bootstrap
            # over the time-ordered joint sample using the identity
            # dir_gap = mean(m|+) - mean(m|-); resample the (m, sign) pairs jointly.
            pairs = np.arange(n)
            block = max(1, int(np.ceil(h / max(spacing, 1e-9))), 4)

            def dg(ix, m=m, s=sign):
                mm, ss = m[ix.astype(int)], s[ix.astype(int)]
                if (ss > 0).sum() == 0 or (ss < 0).sum() == 0:
                    return np.nan
                return mm[ss > 0].mean() - mm[ss < 0].mean()

            ci = block_bootstrap_ci(pairs.astype(float), stat=dg, block=block)
            sweeps = {b: block_bootstrap_ci(pairs.astype(float), stat=dg,
                                            block=max(1, int(block * b)))["ci"]
                      for b in (0.5, 2)}
            rows.append(dict(symbol=sym, h=h, n=n, n_pos=int((sign > 0).sum()),
                             n_neg=int((sign < 0).sum()), block=block,
                             median_spacing_bars=spacing,
                             dir_gap_bps=float(pos.mean() - neg.mean()),
                             ci_low=ci["ci"][0], ci_high=ci["ci"][1],
                             ci_low_seed_range=str(ci["ci_low_seed_range"]),
                             ci_half=str(np.round(sweeps[0.5], 3)),
                             ci_double=str(np.round(sweeps[2], 3))))
        print(sym, "done", flush=True)
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(RES, "ref_arm_dir_gap.csv"), index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
