"""Generate equity curves for RCT on 1h (EXP-091) vs 4h (TEMP-091), equally weighted."""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

for v in ("POLARS_MAX_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
          "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(v, "1")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# --- import EXP-090 substrate ---
ROOT = Path(__file__).resolve().parents[3]
EXP090_CODE = ROOT / "experiments" / "EXP-090" / "code" / "run_experiment.py"
spec = importlib.util.spec_from_file_location("exp090_module", EXP090_CODE)
E90 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = E90
spec.loader.exec_module(E90)

from xen.capgeo_cost import event_costs, holding_days
from xen.intrabar_fill import net_return_atr

# --- constants (mirror EXP-091 / TEMP-091) ---
E90.DOMAINS["4h"] = 240
MR_COST_RT_BPS = {
    "EURUSD": 3.0, "GBPUSD": 4.0, "USDJPY": 4.0, "USDCHF": 4.0, "AUDUSD": 4.0,
    "NZDUSD": 4.5, "EURJPY": 6.0, "GBPJPY": 6.0, "AUDJPY": 6.0, "XAUUSD": 6.0,
    "USTEC": 5.0, "US2000": 6.0, "JP225": 6.0,
}
FIN_BPS_DAY = 0.0
RCT_ARM = "RCT"

files, _ = E90.VAL005.discover_infr003_files()
files = {k.upper(): v for k, v in files.items()}


def cell_net_series(instrument: str, domain: str) -> np.ndarray | None:
    """Resolve RCT on one cell, return per-event net returns (ATR units) in chronological order."""
    p = files.get(instrument)
    if p is None:
        return None
    train_1m, _ = E90.load_train_1m(instrument, p)
    ctx, dropped, status = E90.build_cell_context(train_1m, instrument, domain)
    if ctx is None:
        return None
    idx = ctx.core_entry_idx
    direction = ctx.core_direction
    res = E90.resolve_arm(ctx, idx, direction, RCT_ARM, ctx.minute_high, ctx.minute_low, ctx.minute_open)
    gross = net_return_atr(res.fill_price, ctx.close[idx], direction, ctx.atr[idx])
    hd = holding_days(idx, res.exit_domain_idx, E90.DOMAINS[domain])
    resolved = res.resolved
    keep = resolved & np.isfinite(gross) & np.isfinite(hd) & (hd >= 0.0)
    g = gross[keep]
    costs = event_costs(g, ctx.close[idx][keep], ctx.atr[idx][keep], hd[keep],
                        rt_bps=MR_COST_RT_BPS[instrument], fin_bps_day=FIN_BPS_DAY)
    net = costs.net
    return net[np.isfinite(net)]


# --- 1h cells (EXP-091 member cells on 1h) ---
ONE_H_CELLS = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "NZDUSD",
               "EURJPY", "GBPJPY", "AUDJPY", "USTEC", "US2000"]
# --- 4h cells (all instruments on 4h) ---
FOUR_H_CELLS = sorted(MR_COST_RT_BPS)

print("Resolving 1h cells...")
one_h_series = []
for inst in ONE_H_CELLS:
    s = cell_net_series(inst, "1h")
    if s is not None and s.shape[0] > 0:
        # Convert ATR units to %: assume ~1 ATR ≈ 0.1% for FX / 0.5% for indices
        # Use raw ATR-unit cumsum for now — we'll normalize at portfolio level
        one_h_series.append(s)
        print(f"  1h {inst}: {s.shape[0]} events")

print("Resolving 4h cells...")
four_h_series = []
for inst in FOUR_H_CELLS:
    s = cell_net_series(inst, "4h")
    if s is not None and s.shape[0] > 0:
        four_h_series.append(s)
        print(f"  4h {inst}: {s.shape[0]} events")

# --- Build equally-weighted equity curves ---
# Pad/slice to same length? No — just cumsum each, resample to a common event axis.
# Simpler: plot per-event cumulative P&L in ATR units, equally weighted.

def portfolio_equity(series_list: list[np.ndarray], label: str, ax: plt.Axes, color: str):
    """Plot equally-weighted portfolio equity curve from per-event net ATR series."""
    # Each cell contributes equally: weight = 1/N, cumulative sum its events
    n = len(series_list)
    max_len = max(s.shape[0] for s in series_list)
    # Build a common event index (1..max_len) by padding with last value
    equity = np.zeros(max_len)
    for s in series_list:
        cum = np.cumsum(s) / n
        padded = np.full(max_len, cum[-1])
        padded[:cum.shape[0]] = cum
        equity += padded
    ax.plot(range(max_len), equity, label=label, color=color, lw=1.5)
    ax.fill_between(range(max_len), 0, equity, alpha=0.15, color=color)
    return equity


fig, ax = plt.subplots(figsize=(10, 5.5))

eq_1h = portfolio_equity(one_h_series, "1h RCT (10 instruments, equally weighted)", ax, "steelblue")
eq_4h = portfolio_equity(four_h_series, "4h RCT (12 instruments, equally weighted)", ax, "darkorange")

# Final stats
final_1h = eq_1h[-1]
final_4h = eq_4h[-1]
n_1h_total = sum(s.shape[0] for s in one_h_series)
n_4h_total = sum(s.shape[0] for s in four_h_series)

ax.axhline(0, color="grey", lw=0.6)
ax.set_xlabel("Event (sorted by entry time across all cells)")
ax.set_ylabel("Cumulative net P&L (ATR units, equally weighted)")
ax.set_title("RCT Equity Curves: 1h (EXP-091) vs 4h (TEMP-091) — equally weighted portfolio")
ax.legend(fontsize=8)
ax.text(0.02, 0.98, f"1h final: {final_1h:+.2f} ATR  ({n_1h_total} events)",
        transform=ax.transAxes, va="top", fontsize=8, color="steelblue")
ax.text(0.02, 0.92, f"4h final: {final_4h:+.2f} ATR  ({n_4h_total} events)",
        transform=ax.transAxes, va="top", fontsize=8, color="darkorange")
fig.tight_layout()
out = Path(__file__).resolve().parent.parent / "plots" / "rct_equity_1h_vs_4h.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"\nSaved to {out}")
print(f"1h: {final_1h:+.2f} ATR, {n_1h_total} events, {len(one_h_series)} cells")
print(f"4h: {final_4h:+.2f} ATR, {n_4h_total} events, {len(four_h_series)} cells")
