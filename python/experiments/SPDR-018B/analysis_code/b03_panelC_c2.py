"""Rebuild the C2 shock-MOMO object and the M-3 comparator from panel_C myself."""
import numpy as np
import pandas as pd

R = "python/experiments/SPDR-018B/results/"
p = pd.read_parquet(R + "panel_C.parquet")
pd.set_option("display.width", 250)

print("=== panel_C provenance / fences ===")
for c in ["event_ts", "entry_ts", "exit_ts"]:
    s = pd.to_datetime(p[c], utc=True)
    print(f"  {c}: min={s.min()}  max={s.max()}")
ets = pd.to_datetime(p["event_ts"], utc=True)
ent = pd.to_datetime(p["entry_ts"], utc=True)
ext = pd.to_datetime(p["exit_ts"], utc=True)
print("  entry_ts == event_ts share:", (ent == ets).mean())
print("  entry_idx - event_idx: ", p["entry_idx"].sub(p["event_idx"]).value_counts().head().to_dict())
print("  exit_idx - entry_idx by h:", p.groupby("h").apply(
    lambda d: (d.exit_idx - d.entry_idx).value_counts().head(2).to_dict(), include_groups=False).to_dict())
print("  rows >= cTrader holdout 2024-12-13:", int((ext >= pd.Timestamp("2024-12-13", tz="UTC")).sum()))
print("  rows >= Bybit holdout 2025-01-08:", int((ext >= pd.Timestamp("2025-01-08", tz="UTC")).sum()))
print("  rows >= cTrader train_end 2023-11-22:", int((ext >= pd.Timestamp("2023-11-22", tz="UTC")).sum()))
print("  symbols:", sorted(p.symbol.unique()), " bands:", sorted(p.band.unique()))
print("  policy:", p.policy.value_counts(dropna=False).to_dict())
print("  label:", p.label.value_counts(dropna=False).to_dict())
print("  cost_deflator uniq:", p.cost_deflator.unique(), " cost_model:", p.cost_model.unique()[:3])
print("  cost columns: c_gross mean", p.c_gross_bps.mean(), "cost_bps_vol_scaled median", p.cost_bps_vol_scaled.median(),
      "cost_raw median", p.cost_raw_bps.median())
print("  c_net == c_gross - cost_vol_scaled?  max|diff| =",
      (p.c_net_bps - (p.c_gross_bps - p.cost_bps_vol_scaled)).abs().max())
print("  c_net_unscaled == c_gross - cost_raw? max|diff| =",
      (p.c_net_unscaled_bps - (p.c_gross_bps - p.cost_raw_bps)).abs().max())
print("  implied deflator = median(cost_vol_scaled/cost_raw):",
      (p.cost_bps_vol_scaled / p.cost_raw_bps).median())

# ---------- raw shock split, as screen.md quotes it ----------
print("\n=== raw shock split, ALL arm-C rows (what screen.md §4 quotes) ===")
for flag, d in p.groupby("shock_flag"):
    print(f"  shock={flag}: n={len(d)} gross_mean={d.c_gross_bps.mean():.4f} net={d.c_net_bps.mean():.4f}")

# ---------- the C2 object: shock-conditioned MOMO policy ----------
print("\n=== the C2 object: rows carrying a momentum policy ===")
print("  policy x shock_flag row counts:")
print(pd.crosstab(p.policy, p.shock_flag).to_string())
momo = p[(p.policy == "P-MOMO")]
print(f"  P-MOMO rows total {len(momo)}; of which shock {int(momo.shock_flag.sum())} "
      f"({momo.shock_flag.mean()*100:.1f}%)")
print("  share of ALL shock rows carrying P-MOMO:",
      round((p.shock_flag & (p.policy == 'P-MOMO')).sum() / p.shock_flag.sum(), 4))

live = p[p.shock_flag & (p.policy == "P-MOMO")]
pool = p[(~p.shock_flag) & (p.policy == "P-MOMO")]
print(f"  LIVE (shock & P-MOMO) n={len(live)} gross mean={live.c_gross_bps.mean():.4f}")
print(f"  POOL (no-shock & P-MOMO) n={len(pool)} gross mean={pool.c_gross_bps.mean():.4f}")

# ---------- my own decile-stratified magnitude-matched comparator ----------
def m3(live, pool, seeds=2000, key="c_gross_bps", rng_seed=0):
    """decile-stratify on |r_h| of the live rows; draw same-decile comparator rows w/o replacement."""
    ab_live = live["r_h"].abs().to_numpy()
    edges = np.quantile(ab_live, np.linspace(0, 1, 11))
    edges[0], edges[-1] = -np.inf, np.inf
    lb = np.digitize(ab_live, edges[1:-1])
    ab_pool = pool["r_h"].abs().to_numpy()
    pb = np.digitize(ab_pool, edges[1:-1])
    y = pool[key].to_numpy()
    counts = np.bincount(lb, minlength=10)
    idx_by_bin = [np.where(pb == b)[0] for b in range(10)]
    supply = [(b, int(counts[b]), len(idx_by_bin[b])) for b in range(10)]
    rng = np.random.default_rng(rng_seed)
    out = np.empty(seeds)
    for s in range(seeds):
        acc, n = 0.0, 0
        for b in range(10):
            k, pool_i = counts[b], idx_by_bin[b]
            if k == 0 or len(pool_i) == 0:
                continue
            take = rng.choice(pool_i, size=min(k, len(pool_i)), replace=False)
            acc += y[take].sum()
            n += len(take)
        out[s] = acc / max(n, 1)
    liveval = live[key].mean()
    return dict(live=liveval, null_mean=out.mean(), null_sd=out.std(),
                q=list(np.quantile(out, [.05, .25, .5, .75, .95])),
                pct=float((out < liveval).mean()), n_live=len(live), n_pool=len(pool),
                supply=supply)

print("\n=== my own M-3 rebuild, P-MOMO, GROSS ===")
r = m3(live, pool)
for k, v in r.items():
    if k != "supply":
        print("  ", k, v)
print("   decile supply (bin, live_n, pool_n):", r["supply"])

mr_live = p[p.shock_flag & (p.policy == "P-MR")]
mr_pool = p[(~p.shock_flag) & (p.policy == "P-MR")]
print("\n=== my own M-3 rebuild, P-MR, GROSS ===")
r2 = m3(mr_live, mr_pool)
for k, v in r2.items():
    if k != "supply":
        print("  ", k, v)

# ---------- session stratification ----------
print("\n=== session-stratified (my own definition: UTC hour of event_ts) ===")
hour = pd.to_datetime(p["event_ts"], utc=True).dt.hour
sess = pd.Series(np.where(hour < 7, "ASIA", np.where(hour < 13, "EU", "US")), index=p.index)
p2 = p.assign(sess=sess)
for s in ["ASIA", "EU", "US"]:
    lv = p2[(p2.sess == s) & p2.shock_flag & (p2.policy == "P-MOMO")]
    pl = p2[(p2.sess == s) & (~p2.shock_flag) & (p2.policy == "P-MOMO")]
    if len(lv) < 20 or len(pl) < 20:
        print(f"  {s}: too few rows live={len(lv)} pool={len(pl)}")
        continue
    rr = m3(lv, pl)
    print(f"  {s}: live={rr['live']:.3f} null_mean={rr['null_mean']:.3f} null_sd={rr['null_sd']:.3f} "
          f"pct={rr['pct']:.4f} n_live={rr['n_live']} n_pool={rr['n_pool']} q5={rr['q'][0]:.2f} q95={rr['q'][4]:.2f}")
    print(f"      pool gross mean (unstratified)={pl.c_gross_bps.mean():.3f}  "
          f"live-null gap={rr['live']-rr['null_mean']:.3f}")

# ---------- is the comparator a neutral yardstick? ----------
print("\n=== comparator neutrality probe: what does the POOL itself earn? ===")
for s in ["ASIA", "EU", "US"]:
    for pol in ["P-MOMO", "P-MR", "P-NONE"]:
        d = p2[(p2.sess == s) & (~p2.shock_flag) & (p2.policy == pol)]
        if len(d) > 30:
            se = d.c_gross_bps.std() / np.sqrt(len(d))
            print(f"  {s:5s} {pol:7s} no-shock: n={len(d):6d} gross mean={d.c_gross_bps.mean():+7.3f} (naive se {se:.3f})")
    d = p2[(p2.sess == s) & p2.shock_flag & (p2.policy == "P-MOMO")]
    print(f"  {s:5s} P-MOMO  SHOCK   : n={len(d):6d} gross mean={d.c_gross_bps.mean():+7.3f} "
          f"(naive se {d.c_gross_bps.std()/np.sqrt(len(d)):.3f})")
