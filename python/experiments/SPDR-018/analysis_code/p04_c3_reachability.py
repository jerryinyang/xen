"""P4 — is C3's required n reachable inside the Bybit catalog at all?

Thread P4 from SPDR-018 analysis.md §14 / report.md §9. Pure arithmetic over the EMITTED
results/not_resolvable.json. No re-run, no new emission, no catalog read.

The question: 1,946 C3 cells are NOT_RESOLVABLE (55% of the whole unresolved population). Each
carries `n_required_for_target`. Nobody has asked whether that n is obtainable within the fenced
TRAIN span. If it is not, THAT IS THE ANSWER to the conditional-direction question and should be
recorded as such rather than left as an open lead.
"""
import json, numpy as np, pandas as pd
from pathlib import Path

R = Path("python/experiments/SPDR-018/results")
rows = json.load(open(R / "not_resolvable.json"))["cells"]
d = pd.DataFrame(rows)

# --- the catalog ceiling -------------------------------------------------------------
# TRAIN fence per design §8 / checkpoint design: Bybit TRAIN span, 25-symbol universe.
pin = json.load(open(R / "unit_pin.json"))
TRAIN_DAYS = 901          # checkpoint design §2.1: Bybit DESIGN 609d of a 901d TRAIN span
N_SYMBOLS = 25
BARS_PER_DAY = {"H1": 24, "M15": 96, "H4": 6, "D1": 1}
print(f"unit pin: pooled sigma {pin['pooled_median_sigma_bps']:.2f} bps over "
      f"{pin['n_symbols_measured']} symbols")

def ceiling(clock):
    """Absolute upper bound on pooled bar-observations in TRAIN: one event per bar per symbol."""
    return TRAIN_DAYS * BARS_PER_DAY.get(clock, 24) * N_SYMBOLS

c3 = d[d.residue_item == "C3"].copy()
print(f"\n== C3 NOT_RESOLVABLE cells: {len(c3)}")
print("   basis mix:\n", c3.basis.value_counts().to_string())
print("   clock mix:\n", c3.clock.value_counts().to_string())

c3["ceiling_pooled_bars"] = c3.clock.map(ceiling)
c3["req"] = pd.to_numeric(c3.n_required_for_target, errors="coerce")
c3["req_over_realised"] = c3.req / c3.n
c3["req_over_ceiling"] = c3.req / c3.ceiling_pooled_bars
c3["event_rate_realised"] = c3.n / c3.ceiling_pooled_bars

ok = c3.req.notna()
print(f"\n== required n (n={ok.sum()} cells carry it)")
for q in (0.05, 0.25, 0.5, 0.75, 0.95, 1.0):
    print(f"   q{q:<5} required n = {c3.req[ok].quantile(q):>15,.0f}"
          f"   x realised = {c3.req_over_realised[ok].quantile(q):>10,.1f}")

print(f"\n== against the ABSOLUTE catalog ceiling (one event per bar per symbol, "
      f"{TRAIN_DAYS}d x {N_SYMBOLS} symbols)")
print(f"   H1 ceiling = {ceiling('H1'):,} pooled bar-observations")
print(f"   cells whose required n EXCEEDS the absolute ceiling: "
      f"{int((c3.req_over_ceiling[ok] > 1).sum())} of {int(ok.sum())} "
      f"({(c3.req_over_ceiling[ok] > 1).mean():.1%})")
for q in (0.5, 0.75, 0.95):
    print(f"   q{q} required/ceiling = {c3.req_over_ceiling[ok].quantile(q):.2f}")

# The decisive stratum: cells ALREADY pooled across all symbols on the full TRAIN span have no
# remaining legitimate lever (design §5 levers are exhausted by construction).
pooled = c3[ok & c3.basis.str.contains("pooled", na=False) & (c3.band == "TRAIN")]
print(f"\n== the decisive stratum: already POOLED on the full TRAIN span -> no lever remains")
print(f"   cells: {len(pooled)}")
if len(pooled):
    print(f"   median realised n           = {pooled.n.median():,.0f}")
    print(f"   median required n           = {pooled.req.median():,.0f}")
    print(f"   median shortfall multiple   = {pooled.req_over_realised.median():,.1f}x")
    print(f"   median realised event rate  = {pooled.event_rate_realised.median():.4f} of all bars")
    print(f"   required n vs H1 ceiling    = {pooled.req_over_ceiling.median():.2f}x "
          f"(>1 means unobtainable even if EVERY bar were an event)")
    # rate-preserving ceiling: keep the cell's own event rate, use every bar in the catalog
    print(f"   at its OWN event rate, the catalog can supply at most "
          f"{(pooled.ceiling_pooled_bars*pooled.event_rate_realised).median():,.0f} events "
          f"= the realised n (levers already exhausted)")

# How much MORE catalog would be needed, in years, at the realised event rate?
YEARS_TRAIN = TRAIN_DAYS / 365.25
pooled_years = pooled.req_over_realised * YEARS_TRAIN
print(f"\n== calendar span required at the realised event rate "
      f"(TRAIN = {YEARS_TRAIN:.2f} years)")
for q in (0.25, 0.5, 0.75, 0.95):
    print(f"   q{q:<5} = {pooled_years.quantile(q):>10,.1f} years of 25-symbol history")

out = c3[["arm","residue_item","band","basis","clock","symbol","conditioner","n","n_dates",
          "block_mde","target_mde","multiple_short","req","req_over_realised",
          "req_over_ceiling","event_rate_realised"]]
out.to_csv(R / "p04_c3_reachability.csv", index=False)
print(f"\nwrote {R/'p04_c3_reachability.csv'} ({len(out)} rows)")
