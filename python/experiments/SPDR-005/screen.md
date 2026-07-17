# SPDR-005 — Screen summary (neutral quantification)

**Lane:** SPDR TRAIN-only · CF-EPSOSC-001  
**Design:** `design.md` (FROZEN) · **AMENDMENT-1** (RET_ANCHOR censor at train_end)  
**Run:** 2026-07-17 · **Integrity:** **PASS 12/12** · no disposition here  
**Binding read:** `analysis.md`  
**Primary unit (L-16):** gross open-to-open **bps/episode** (fixed-H disclosure only)

---

## Grid

| Axis | Full emit | Primary promote slice (§5.4) |
|------|-----------|------------------------------|
| Symbols | top-10 by trailing 24h **base volume** | same |
| Domain | 5m, 15m, 1h | **15m, 1h** |
| Object | STRETCH, VOLARM | both |
| W | 48, 96, 192 | **96, 192** |
| k | 2.0, 2.5, 3.0 | **2.5, 3.0** |
| Clear | RET_ANCHOR, TIME, HYBRID | **RET_ANCHOR, HYBRID** |
| Side | LONG_ONLY, SHORT_ONLY | both |

**Cells:** 3240 treatment · **640 primary** (K=3 uses primary only).  
**Market entry only** (P-10). **No** hard-cap banded grid in treatment (P-12); GRID_TWIN disclosure separate.

**Primary 10 (membership-days):** SHIB1000, GALA, DOGE, RSR, 1000BONK, SLP, JASMY, XRP, 1000PEPE, 1000BTT  
(rank key = base volume, design §5.1 — not notional).

---

## Integrity / methods

| Item | Result |
|------|--------|
| 1–12 | **PASS 12/12** |
| G1–G3 | PASS |
| Control A | seeds 2000–2024 (full 25 on primary; 5-seed disclosure battery on non-primary) |
| Control B | episode-label **derangement** (L-28); collapse on CI+ |
| AMENDMENT-1 | censored_frac disclosed; primary RET med censored_frac **0**; full-grid flag_gt20 = **94** cells |
| L-16 | `primary_unit = bps_per_episode` on all rows |

---

## Money floor (L-21 measured)

TRAIN-median staging SpreadBps + taker 11 bps RT + funding GAP:

| Symbol | SpreadBps | Floor proxy (~8h episode) |
|--------|-----------|---------------------------|
| DOGEUSDT | 1.65 | ~13.7 bps |
| XRPUSDT | 2.06 | ~14.1 bps |
| 1000PEPEUSDT | 1.72 | ~13.7 bps |
| SHIB1000USDT | 2.67 | ~14.7 bps |
| 1000BONKUSDT | 15.3 | ~27.3 bps |

Full pins: `results/unit_pin.json`.

---

## Magnitudes (disclosure; full table `results/cells.parquet`)

### Full grid

| Facet | Value |
|--------|--------|
| Med mean bps/episode | **+5.69** |
| Med lift vs Control A | **+4.92** |
| Lift CI+ | **557 / 3240** |
| Unpowered | **897** |
| Censored flag >20% | **94** |

### Primary promote slice (binding for K)

| Facet | Value |
|--------|--------|
| n cells | **640** |
| Med mean | **−11.4** bps/episode |
| Med lift | **−9.2** bps |
| Lift CI+ (incl. unpowered) | **126** |
| Powered positive lift CI+ | see analyst re-derive |
| Control B collapse on CI+ | med **≈0.95**; **100%** of powered CI+ with collapse > 0.5 |
| STRETCH / VOLARM med lift | −9.8 / −9.0 |
| 15m / 1h med lift | **+3.8** / **−46.0** |
| LONG / SHORT med lift | −3.9 / −23.0 |

### K≥3 cluster scan (primary, powered positive lift CI+)

Largest regions (object × domain × clear):

| region | n CI+ | n_k | n_w | med lift |
|--------|------:|----:|----:|---------:|
| VOLARM × 15m × RET_ANCHOR | 25 | 2 | 2 | +54 |
| VOLARM × 15m × HYBRID | 23 | 2 | 2 | +60 |
| STRETCH × 15m × HYBRID | 11 | 2 | 2 | +35 |
| STRETCH × 1h × RET/HYBRID | 7–8 | 2 | 2 | +113–119 |

Per-symbol neighbourhoods (n≥3): SHIB/XRP/JASMY/DOGE VOLARM 15m; XRP/PEPE STRETCH 1h; SHIB/DOGE STRETCH 15m.

### VR facet (§5.5)

`results/vr_facet.parquet` — lags {2,4,8,16}.  
**15m:** med VR 0.88–0.95; **VR&lt;1 on 90%** of primary symbols at all lags.  
**1h:** med VR 0.97–0.99; VR&lt;1 on 60–70%.  
→ Oscillation diagnostic **not flat** on primary domains (half-symbol rule met).

### GRID_TWIN (P-12 sentinel)

`results/grid_twin.parquet` — med mean **−8.4** bps; some sparse 1h positives (e.g. 1000BTT n=18).  
**Not** the sole positive structure relative to multi-symbol VOLARM/STRETCH clusters above — structure-identity check for analyst.

---

## Artifacts

```
results/cells.parquet          # 3240 per-stratum (bps/episode)
results/vr_facet.parquet
results/grid_twin.parquet
results/unit_pin.json
results/integrity.json         # 12/12
results/membership.parquet
results/summary.json
```

---

## Non-claims

No disposition · no XENA · no TEST/holdout · fixed-H never family-terminal (L-16).
