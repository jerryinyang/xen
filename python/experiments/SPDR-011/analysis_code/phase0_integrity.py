"""Phase 0 integrity checks on the SPDR-011 DESIGN artifact — independent of experiment code."""
from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

import polars as pl

from xen.nautilus.catalog_fence import load_fence_manifest

ROOT = Path(__file__).resolve().parents[4]
ART = ROOT / "data/nautilus_runs/SPDR-011/artifact-bundle/design.parquet"
FAMILY = ROOT / "data/nautilus_runs/SPDR-011"
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT"]

a = pl.read_parquet(ART)
fence = load_fence_manifest()
rows = []


def check(name: str, ok: bool, evidence: str) -> None:
    rows.append((name, "PASS" if ok else "FAIL", evidence))


# --- causality: every decision input known at or before the trigger ---
for col in ("state_known_ts", "range_known_ts", "signed_known_ts"):
    bad = a.filter(pl.col(col) > pl.col("trigger_ts")).height
    nulls = a.filter(pl.col(col).is_null()).height
    check(f"{col} <= trigger_ts", bad == 0, f"violations={bad}, nulls={nulls}, n={a.height}")

# --- decision precedes action ---
# Design §5.2 sets entry_ts == slot end == trigger_ts. Causality does not rest on a strict
# timestamp gap: the trigger bar's prints all fall strictly BEFORE t while the execution mark
# is the first minute opening AT t. That separation is verified in phase0_fill_anchor.py and
# phase0_signal_recompute.py; here we assert only that action never precedes decision.
bad = a.filter(pl.col("trigger_ts") > pl.col("entry_ts")).height
check("entry_ts >= trigger_ts (design: equal)", bad == 0,
      f"violations={bad}; equal on {a.filter(pl.col('trigger_ts') == pl.col('entry_ts')).height}/{a.height}")

# --- frozen 4h horizon ---
bad = a.filter(
    (pl.col("exit_ts") - pl.col("entry_ts")) != pl.duration(hours=4)
).height
check("exit_ts == entry_ts + 4h", bad == 0, f"violations={bad}")

# --- state used only on the day AFTER its source day ---
bad = a.filter(pl.col("state_source_day") >= pl.col("trade_day")).height
check("state_source_day < trade_day", bad == 0, f"violations={bad}")
bad = a.filter(pl.col("range_source_day") >= pl.col("trade_day")).height
check("range_source_day < trade_day", bad == 0, f"violations={bad}")

# --- holdout / TEST fence: nothing at or beyond TRAIN end ---
mx_exit = a["exit_ts"].max()
mx_entry = a["entry_ts"].max()
check(
    "all exits < TRAIN end (TEST/holdout untouched)",
    mx_exit < fence.train_end_utc,
    f"max exit_ts={mx_exit} < train_end={fence.train_end_utc}; holdout_start={fence.holdout_start_utc}",
)
check(
    "all entries >= analysis start",
    a["entry_ts"].min() >= fence.analysis_start_utc,
    f"min entry_ts={a['entry_ts'].min()} >= {fence.analysis_start_utc}",
)

# --- band purity ---
bands = a["band"].unique().to_list()
check("DESIGN band only (no CONFIRM rows)", bands == ["DESIGN"], f"bands={bands}")

# --- price-primary: real Nautilus emission, non-STUB fence, pinned manifest ---
stubs, pins = [], []
for s in SYMBOLS:
    fa = json.load(open(FAMILY / s / "fence_attestation.json"))
    stubs.append(fa.get("status"))
    pins.append(fa.get("manifest_sha256"))
check(
    "fence attestation non-STUB",
    all(s != "STUB" for s in stubs),
    f"statuses={sorted(set(stubs))}",
)
check(
    "fence manifest hash pinned + identical across cells",
    len(set(pins)) == 1 and pins[0],
    f"manifest_sha256={pins[0]}",
)

# --- cost scope disclosure carried on every row ---
check(
    "spread unavailable + not charged on every row",
    a["spread_rt_bps"].null_count() == a.height
    and a["cost_scope"].unique().to_list() == ["PARTIAL_FEES_FUNDING_ONLY"],
    f"spread_rt_bps nulls={a['spread_rt_bps'].null_count()}/{a.height}, "
    f"cost_scope={a['cost_scope'].unique().to_list()}, "
    f"status={a['spread_cost_status'].unique().to_list()}",
)

print(f"{'check':52s} {'result':6s} evidence")
for n, r, e in rows:
    print(f"{n:52s} {r:6s} {e}")
print("\nALL PASS:", all(r == "PASS" for _, r, _ in rows))
