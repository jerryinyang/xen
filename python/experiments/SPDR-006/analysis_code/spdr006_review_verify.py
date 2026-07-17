"""Independent verification of analysis.md headline numbers (review pass).

Reads only raw emissions (cells.parquet, amplifier_vs_spdr004.parquet, unit_pin.json).
Does not import screen_code or the prior analyst script.
"""
import json
import pandas as pd

R = "experiments/SPDR-006/results"
c = pd.read_parquet(f"{R}/cells.parquet")
amp = pd.read_parquet(f"{R}/amplifier_vs_spdr004.parquet")
pin = json.load(open(f"{R}/unit_pin.json")) if __import__("os").path.exists(f"{R}/unit_pin.json") else {}

t = c[c.is_treatment].copy()
b = c[~c.is_treatment]
print("counts", len(t), len(b))
print("unpowered", int(t.unpowered.sum()), "powered", int((~t.unpowered).sum()))
print("med mean bps", round(t.mean_bps.median(), 2), "med lift", round(t.lift_bps.median(), 2))
cip = t[t.lift_ci_low > 0]
print("lift CI+ total", len(cip), "powered", len(cip[~cip.unpowered]))

print("\n-- filter axis --")
for f, g in t.groupby("htf_filter"):
    gp = g[~g.unpowered]
    print(f, len(g), "med lift", round(g.lift_bps.median(), 2),
          "CI+", int((g.lift_ci_low > 0).sum()),
          "CI+pow", int((gp.lift_ci_low > 0).sum()),
          "unpow", int(g.unpowered.sum()))

print("\n-- base axis --")
for f, g in t.groupby("base"):
    gp = g[~g.unpowered]
    print(f, len(g), "pow", len(gp), "CI+", int((g.lift_ci_low > 0).sum()),
          "CI+pow", int((gp.lift_ci_low > 0).sum()),
          "med lift", round(g.lift_bps.median(), 2),
          "methods", g.lift_ci_method.unique())

print("\n-- banned method --")
print("battery_minus_seeds count:", int((t.lift_ci_method == "battery_minus_seeds").sum()))

print("\n-- promote ladders --")
for sym, filt in [("SOLUSDT", "DI×VOL_HI"), ("BTCUSDT", "DI×VOL_HI"),
                  ("BTCUSDT", "DI_ADX×VOL_HI"), ("SOLUSDT", "DI_ADX×VOL_HI")]:
    g = t[(t.symbol == sym) & (t.domain == "4h/15m") & (t.base == "UNF") & (t.htf_filter == filt)]
    g = g.sort_values("hold_mult")
    print(sym, filt)
    print(g[["hold_mult", "mean_bps", "lift_bps", "lift_ci_low", "n_trades",
             "destroy_collapse_frac", "lift_ci_low_seed_range_lo"]].round(2).to_string(index=False))

print("\n-- amplifier --")
print("rows", len(amp), amp.columns.tolist())
# join powered CI+ interaction cells
key = ["symbol", "domain", "hold_mult", "base", "htf_filter"]
inter = t[t.htf_filter.isin(["DI×VOL_HI", "DI_ADX×VOL_HI"])]
ipow = inter[(~inter.unpowered) & (inter.lift_ci_low > 0)]
m = ipow.merge(amp, on=key, suffixes=("", "_amp"))
dcol = [x for x in amp.columns if "delta" in x or "amp" in x.lower()]
print("powered CI+ interaction:", len(ipow), "joined:", len(m), "delta cols:", dcol)
if dcol:
    d = m[dcol[0]] if dcol[0] in m else None
print(amp.head(3).T)
