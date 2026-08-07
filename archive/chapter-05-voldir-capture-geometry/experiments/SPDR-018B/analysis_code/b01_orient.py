"""SPDR-018B analyst pass 2 — orientation. Re-derives everything from results/*.parquet."""
import json
import numpy as np
import pandas as pd

R = "python/experiments/SPDR-018B/results/"
m = pd.read_parquet(R + "metrics_by_cell.parquet")
pd.set_option("display.width", 250)

print("=== cells by arm ===")
print(m.groupby("arm").size())
print("total", len(m))
print("\n=== residue items ===")
print(m.groupby("residue_item").size().to_string())

print("\n=== precision columns ===")
for c in [
    "target_mde_bps_absolute__SUPERSEDED",
    "target_mde_bps_sigma_scaled",
    "sigma_target_deflator",
    "precision_basis",
    "at_parent_target_precision",
    "at_parent_target_precision_absolute__SUPERSEDED",
    "provenance_note",
]:
    if c in m:
        v = m[c]
        if v.dtype == object:
            print(c, "->", v.dropna().value_counts().head(5).to_dict())
        else:
            print(c, "-> notnull", v.notna().sum(), "uniq", sorted(v.dropna().unique())[:12])

print("\n=== signed cells def ===")
signed = m["gross_p"].notna() & m["gross_W"].notna() & m["gross_L"].notna()
print("signed", signed.sum())
print("at target (new col)", int(m["at_parent_target_precision"].fillna(False).sum()))
print("signed & at target", int((signed & m["at_parent_target_precision"].fillna(False)).sum()))
print(
    "signed & at target (SUPERSEDED col)",
    int((signed & m["at_parent_target_precision_absolute__SUPERSEDED"].fillna(False)).sum()),
)

print("\n=== universe / holdout fences from emitted parquets ===")
for arm in "ABCD":
    a = pd.read_parquet(R + f"arm_{arm}.parquet")
    tscols = [c for c in a.columns if c.endswith("_ts") or "slot_" in c]
    print(f"arm {arm}: rows={len(a)} cols={len(a.columns)} tscols={tscols}")
    print("   symbols:", sorted(a["symbol"].dropna().unique())[:8] if "symbol" in a else "n/a")
    for c in tscols:
        s = pd.to_datetime(a[c], utc=True, errors="coerce")
        if s.notna().any():
            print(f"   {c}: min={s.min()} max={s.max()}")
