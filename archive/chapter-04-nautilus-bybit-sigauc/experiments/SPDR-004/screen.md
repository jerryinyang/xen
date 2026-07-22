# SPDR-004 — Screen summary (neutral quantification)

**Lane:** SPDR TRAIN-only · CF-HTFCAP-001  
**Design:** `design.md` · **AMENDMENTS 1–5** · re-run 2026-07-16 (A5 QA-2 fix)  
**Integrity:** **PASS 11/11** · no disposition here  
**Binding read:** `analysis.md`

---

## Amendments

| ID | Change |
|----|--------|
| A1 | UNF baseline = RAND battery @ UNF cadence |
| A2 | Membership = USDT notional `Σ(vol×close)` |
| A3 | Cell strata = top-10 membership-days |
| A4 | Two-sample lift CIs + L-20 emit |
| **A5** | UNF lift CI bootstraps **both** treatment trades (block≥H) **and** battery seeds — bans fixed-treatment `battery_minus_seeds` |

---

## Universe

**Primary 10:** SOL, ETH, BTC, XRP, OP, DOGE, 1000PEPE, APT, LTC, LINK  
Membership notional; catalog mass ~2022-07-15+.

---

## Integrity / methods

- PASS 11/11; G1–G3 ok  
- `lift_ci_method` ∈ {`two_sample_block`, `two_sample_block_vs_battery`, `two_sample_seed_means`} only  
- L-20: `block_h_ci_*`, seed ranges, `block_sens_*` present  

---

## Magnitudes (A5 re-emit)

| Facet | Value |
|--------|--------|
| Med lift (all treatment) | **+0.79** bps |
| Lift CI+ total | **124/720** (was 219 pre-A5; UNF arm corrected) |
| UNF CI+ | **13/240** (was ~108 under fixed-treatment battery CI) |
| MOM CI+ | **9/240** |
| RAND CI+ | **102/240** (seed-mean two-sample; L-19 arm) |
| Powered CI+ | **111** |
| Domain med lift | 1h **+0.19** · 4h **+5.11** · 1d **−8.31** |
| Example SOL 4h×1 UNF DI_ADX | lift **12.0** bps, CI **[+0.64, +24.4]**, method `two_sample_block_vs_battery`, block=16 |

Pooled lines disclosure-only. Money floor ~13–15 bps taker+GAP. Control C still primary identification facet for analyst.

---

## Non-claims

No disposition · no XENA · no TEST/holdout.
