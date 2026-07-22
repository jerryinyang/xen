# SPDR-006 — Screen summary (neutral quantification)

**Lane:** SPDR TRAIN-only · CF-HTFCAP-001 vol-regime facet  
**Design:** `design.md` (FROZEN) · inherits SPDR-004 AMENDMENTS 1–5  
**Run:** 2026-07-17 · **Integrity:** **PASS 14/14** · no disposition here  
**Binding read:** `analysis.md`

---

## Grid

| Axis | Levels |
|------|--------|
| Symbols | top-10 membership-days (byte-identical membership to SPDR-004, sha `30350088…`) |
| Domain | 1h/5m, 4h/15m, 1d/1h |
| Hold | 0.5×, 1×, 2×, 4× HTF span |
| Base | UNF, MOM, RAND (seeds 1000–1024) |
| HTF filter | VOL_HI (≥1.25), VOL_LO (≤0.8), DI×VOL_HI, DI_ADX×VOL_HI |

**Cells:** 1440 treatment + 240 baselines. No DI-only / DI_ADX-only (frozen SPDR-004).  
**K=3:** THIS grid only (no pooling with SPDR-004 for K).

---

## Integrity / methods

| Item | Result |
|------|--------|
| 1–11 (SPDR-004 form) | PASS |
| 12 Joint phase-shift vol+DI+ADX | PASS |
| 13 No DI-only treatment | PASS |
| 14 Amplifier table (720 rows) | PASS |
| G1–G3 | PASS |
| `lift_ci_method` | `two_sample_block` / `two_sample_block_vs_battery` / `two_sample_seed_means` only (`battery_minus_seeds` absent) |
| L-20 | `block_h_ci_*`, seed ranges, `block_sens_*` present |

---

## Money floor (L-21 measured — not GAP=2)

TRAIN-median staging `SpreadBps` + taker 5.5 bps/side (11 RT) + funding GAP 1 bps/8h.

| Symbol | SpreadBps med | Floor 4h/15m ×1 (~4h) |
|--------|---------------|------------------------|
| BTCUSDT | 0.30 | ~11.8 bps |
| ETHUSDT | 0.48 | ~12.0 bps |
| SOLUSDT | 1.63 | ~13.1 bps |
| DOGEUSDT | 1.65 | ~13.2 bps |
| 1000PEPEUSDT | 1.72 | ~13.2 bps |
| OPUSDT | 2.87 | ~14.4 bps |

Full pins: `results/unit_pin.json`.

---

## Magnitudes (disclosure; full table in `results/cells.parquet`)

| Facet | Value |
|--------|--------|
| Med lift (all treatment) | **+1.51** bps |
| Lift CI+ powered | **184** / 1440 (266 CI+ incl. unpowered tails) |
| UNF / MOM / RAND CI+ powered | **41 / 21 / 122** of 480 each |
| VOL_HI med lift | +0.89 · CI+ powered **15** |
| VOL_LO med lift | **−0.02** · CI+ powered **5** (compression; no sign-flip story) |
| DI×VOL_HI med lift | **+5.14** · CI+ powered **86** |
| DI_ADX×VOL_HI med lift | **+5.81** · CI+ powered **78** |
| Domain med lift | 1h **+0.13** · 4h **+7.71** · 1d **+1.26** |
| Control C on CI+ | med collapse **≈1.02**; **81.5%** of CI+ with collapse > 0.5 |

### Example ladders (gross mean / lift bps; CI-honest)

**SOL 4h/15m UNF × DI×VOL_HI** (monotone; all holds lift CI+ except none — all 4 CI+):

| hold | mean | lift | lift CI low | n | collapse |
|------|------|------|-------------|---|----------|
| 0.5× | 11.4 | 12.1 | +0.35 | 1599 | 0.64 |
| 1× | 23.3 | 23.3 | +4.99 | 800 | 0.69 |
| 2× | 39.9 | 37.4 | +5.95 | 409 | 0.62 |
| 4× | 78.2 | 77.7 | +45.3 | 213 | 0.55 |

**SOL 4h/15m UNF × DI_ADX×VOL_HI:** mean 10.5→21.6→37.8→68.8; lift CI+ from 1× up (h0.5 CI low −3.3).  
**BTC 4h/15m UNF × DI×VOL_HI:** mean 7.0→14.1→29.7→56.6; all 4 holds lift CI+; collapse 0.79–0.90.

Money floor cross-check (SOL 4h): h1 mean 23.3 > floor ~13.1; h0.5 mean 11.4 ≈ floor; BTC h0.5 mean 7.0 < floor ~11.6.

### Amplifier vs frozen SPDR-004 (read-only)

`results/amplifier_vs_spdr004.parquet` — 720 interaction rows.  
Among powered lift-CI+ interaction cells: **160/164** have `amp_lift_minus_frozen_lift > 0`.  
Example SOL 4h UNF DI×VOL_HI: amp vs DI-only lift **+7.3 → +50.0 bps** across holds 0.5–4×.

### K=3 cluster scan (THIS grid; magnitudes only)

Largest powered CI+ regions (domain × filter × base):

| region | n CI+ | n_hold | n_sym | med lift |
|--------|-------|--------|-------|----------|
| 4h/15m DI×VOL_HI RAND | 32 | 4 | 10 | +16.2 |
| 4h/15m DI_ADX×VOL_HI RAND | 30 | 4 | 9 | +19.2 |
| 4h/15m DI_ADX×VOL_HI UNF | 8 | 4 | 3 | +28.5 |
| BTC 4h DI×VOL_HI UNF (hold ladder) | 4 | 4 | 1 | +21.9 |
| SOL 4h DI_ADX×VOL_HI RAND | 4 | 4 | 1 | +27.2 |

VOL_HI / VOL_LO standalone do **not** form K=3 powered CI+ hold ladders on primary symbols.

---

## Artifacts

```
results/cells.parquet          # full per-stratum (1680 rows)
results/amplifier_vs_spdr004.* # interaction vs frozen SPDR-004
results/unit_pin.json          # ATR + SpreadBps + cost examples
results/integrity.json         # 14/14
results/summary.json
results/membership.parquet     # sha-identical to SPDR-004
```

---

## Non-claims

No disposition · no XENA design · no TEST/holdout · no SPDR-004 re-run.
