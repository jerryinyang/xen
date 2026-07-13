# CF-MTFCTX-001 — MTF Context Filters on Naive Controls (XENA lane)

Detailed experiment cards for the family group registered 2026-07-10 (chapter 03, checkpoint 011).
Registry card (thesis, locked decisions, evidence rows):
[`docs/signal-registry/candidate-families/cf-mtfctx-001.md`](../../../signal-registry/candidate-families/cf-mtfctx-001.md).
Run ledger: [`docs/signal-registry/xena-runs.md`](../../../signal-registry/xena-runs.md).

**Thesis.** HTF context (trend direction ±DI, trend strength ADX, volatility regime) improves the
signal quality of LTF entry models — adjudicated **not** as an A/B effect claim but as portfolio
selection: filtered (V01–V18) and unfiltered (V00) variants enter each XENA universe as equal
candidates and the frozen search + certification machinery selects.

**Family status: REGISTERED (2026-07-10). Status transitions are operator-signed at the
checkpoint-011 retrospective — not here, and not by any experiment.**

## Contents

- [XENA-001 — CTRL-01 RANDOM control (MACHINERY-ALARM)](#xena-001--mtfctx-c1-htf-context-filters-on-a-random-entry-control-ctrl-01)
- [XENA-002 — CTRL-02 NAIVE MOMENTUM (NO DETECTABLE STRUCTURE)](#xena-002--mtfctx-c2-htf-context-filters-on-a-naive-momentum-control-ctrl-02)
- [XENA-003 — CTRL-03 NAIVE REVERSION, native limit orders (NOT SUPPORTED — magnitude)](#xena-003--mtfctx-c3-htf-context-filters-on-a-naive-reversion-control-ctrl-03-native-limit-orders)

---

## XENA-001 — MTFCTX-C1: HTF context filters on a RANDOM entry control (CTRL-01)

**Status**: COMPLETED — **operator verdict: MACHINERY-ALARM**
**Date**: 2026-07-13 (verdict) · 2026-07-12 (adjudication)
**Instruments**: USTEC US500 US2000 JP225 AUS200 US30 EU50 GER40 HK50 UK100 XAUUSD BTCUSD (12)
**Data views / features**: 1m timebars → 3 HTF/LTF domain pairs (1d/1h, 4h/15m, 1h/5m); HTF ADX(14),
±DI, median-TR ATR(14) vol regime (P20/P80 hysteresis, 250-bar rank); oracle-composed round-trip legs

### Hypothesis Tests

1. **Structural control (design §7):** does the XENA machinery manufacture certified portfolios from
   noise on real prices and real code paths? Pre-registered reading (§1/§8): certification or gate
   pass on random entries = **MACHINERY-ALARM**, never an edge.
2. **FILTER-STRUCTURE (informative only):** are filtered variants (V01–V18) over-represented vs the
   V00 baseline among top subsets on an information-free entry engine?

### Scope

- 2,736 candidates (19 variants × 4 holds × 3 domains × 12 instruments); entries pseudo-random
  (splitmix64, lambda=2, 36 pinned streams); exits fixed hold only; `SlPrice` = sizing-only.
- Bands: TRAIN search 2021-06-02 → 2023-03-08; ranking → 2024-03-28 (4 purged folds, 14-day purge);
  TEST gate → 2024-12-11T08:19Z (**never opened**). Global 30% holdout never loaded.
- Search: LAHC ×12 restarts, budget 21,835, `charge_costs=false` (A-1). Frozen registry v3
  (`537d691a…`), hash-verified.
- Exclusions: no gate spend (0/2), no cost/net read (spread pins never set), no data-analyst stage.

### Results / Observations

- Estimand gate **2,736/2,736 PASS**; candidate gate 2,736/2,736; provenance + fence PASS.
- Eval counts (§10.4): search **255,142** evaluations / **255,142** distinct subsets; certify 2,190.
- Certification: **4 of 12 finalists**. All 12 clear `F_floor` (0.4302) by **8.3×–13.1×**; certified ⇔
  `min_drop_ratio` ≥ 0.70 (plateau screen is the only operative criterion). Keystones on 8/12.
- Certified fold medians: **+0.100 / +0.043 / −0.098 / −0.286**; worst fold −0.689; `pbo_like` 0.25.
- Restart F̂: min 3.566 / median **4.267** / max 5.648 (spread 2.082); 12 distinct terminals.
- Permutation battery v2 (K=10 × 2): permuted median **5.937**; **live median at the 0th percentile**;
  live − permuted = **−1.67 log-wealth**.
- WS-6 null reference (recomputed from `INFR-006/results/ws6_battery_raw.jsonl`): null finalist
  certification **0.75%** (19/2,550); plateau screen alone passes **50.8%**; `F_floor` cleared by
  **0.78%**; null F̂ median 0.193, max 0.533.
- Filter structure (209 finalist member slots): V00 2.4% vs 5.3% universe share = **0.45×**.

### Hypothesis-Specific Conclusion

**MACHINERY-ALARM** (pre-registered band met: "certification rate far above battery null rate" —
33% vs 0.75%). The defect is in the **adjudication layer**: `F_floor` is an absolute threshold on an
extensive statistic (log-wealth) calibrated at 24 candidates / 400 budget, and is inoperative at live
scale. The substantive evidence is noise-consistent, as designed.

### Hypothesis-Agnostic Observations

- The emission layer (engine, fills, estimand gate, provenance, holdout fence, oracle reconciliation)
  held on the first live XENA universe.
- The permutation battery on a bar-close universe scores **live below permuted** — a −1.67 no-structure
  bias that is now the lane's calibration constant for reading other universes.

---

## XENA-002 — MTFCTX-C2: HTF context filters on a NAIVE MOMENTUM control (CTRL-02)

**Status**: COMPLETED — **operator verdict: NO DETECTABLE STRUCTURE**
**Date**: 2026-07-13 (verdict) · 2026-07-12 (adjudication)
**Instruments**: same 12
**Data views / features**: as XENA-001, entries = 3-bar breakout of the confirmed close (deterministic)

### Hypothesis Tests

1. **Mechanism:** short-horizon continuation after a 3-bar range break persists over 0.5–4× the HTF
   span; **HTF context conditions its quality** — read at portfolio level (certification + selection).
2. **FILTER-STRUCTURE (the family-thesis read):** are V01–V18 systematically selected over V00?

### Scope

- 2,736 candidates; market orders at bar open; fixed hold exits; identical bands, folds, registry pin
  and instruments as XENA-001. Search LAHC ×12, budget **34,000**, `charge_costs=false`.
- Exclusions: no gate spend (0/2), no TEST read, no data-analyst stage, no cost/net read.

### Results / Observations

- Estimand gate **2,773/2,773 cells PASS**; candidate gate PASS.
- Eval counts (§10.4): search **397,475** evaluations / **397,475** distinct subsets; certify 1,851.
- Certification: **7 of 12** finalists; all 12 clear `F_floor` by **9.7×–16.4×**; `pbo_like` **0.50**;
  keystones on 5/12.
- All 7 certified finalists have **positive fold medians (+0.063 … +0.246)**.
- Restart F̂: min 4.158 / median **4.786** / max 7.054 (**spread 2.897**); 12 distinct terminals.
- Permutation battery v2: permuted median **6.197**; **live median at the 0th percentile**;
  live − permuted = **−1.41**. Netted vs XENA-001's −1.67 ⇒ **+0.26** relative to the random control.
- Filter structure (322 finalist member slots): V00 **1.18×** its universe share; 1H5M 1.42×; H4X 1.33×.
- `resim frac_folds_below_search_p25` = 1.0 for every finalist (structurally vacuous; audit A3).

### Hypothesis-Specific Conclusion

**NO DETECTABLE STRUCTURE.** The informed universe sits +0.26 above the random control on the battery
comparison — well inside its own restart dispersion (2.90). The 7/12 certification count is
uninformative (F_floor defect, XENA-001). The one genuine difference — positive fold medians on every
certified finalist — does not survive the battery comparison. **Negative evidence for the family arc.**

### Hypothesis-Agnostic Observations

- HTF filter variants are **not** preferentially selected over the unfiltered baseline (V00 1.18×).
- Audit B2 caveat: the costless log-wealth objective pays for **cadence**, and every HTF filter thins
  cadence — so a null filter-structure read in this lane is weaker evidence against HTF conditioning
  than it appears.

---

## XENA-003 — MTFCTX-C3: HTF context filters on a NAIVE REVERSION control (CTRL-03, native limit orders)

**Status**: COMPLETED — **operator verdict: NOT SUPPORTED (magnitude)**
**Date**: 2026-07-13 (verdict) · analysis + adjudication 2026-07-12
**Instruments**: same 12
**Data views / features**: as above; entries = passive trailing limit at the 3-bar extreme, **native
cTrader limit orders + m1 fills** (EXP-013 carve-out); exits = fixed hold OR floating 0.5×ATR profit exit

### Hypothesis Tests

1. **Mechanism:** a passive limit fill at the trailing 3-bar extreme captures snap-back over 0.5–4× the
   HTF span; **HTF context conditions the quality of those fills**.
2. **FILTER-STRUCTURE:** are V01–V18 selected over V00?

### Scope

- 2,736 candidates; search LAHC ×12, budget **27,294**, `charge_costs=false`; identical bands/folds/pin.
- Data-analyst interrogation on the **search band only** (`analysis.md`): 717,967 legs / 240 finalist-member
  candidates; top subset n = 195,056 legs. TEST band never read; holdout never loaded; **gate 0/2**.

### Results / Observations

- Estimand gate **2,777/2,777 cells PASS**; native-fill physicality tripwire **PASS** (51/14,400 flags, all
  tick-stamp/feed-gap ambiguity; no fill at an untouched engine-feed price).
- Eval counts (§10.4): search **322,803** evaluations / **322,803** distinct subsets; certify 1,104.
- Gross **+1.958 bps/leg**, 95% CI **[1.846, 2.073]**, n = 195,056; block-stable (32/64/128), seed-stable;
  per-year 1.87 / 2.07 / 1.63; all 12 instruments positive (1.35–5.92 bps); gross / 2×ATR = 0.022–0.036.
- Decomposition: print premium **+7.496**, forward path **−5.538**, **first mark +1.785 (91.2% of the edge)**,
  rest of hold **+0.172 bps (8.8% — the registered mechanism)**.
- Cost sweep: breakeven added RT spread **0.564 / 0.705 / 1.146 bps** (min/median/max); positive finalists =
  12 @ 0 bps · 5 @ 0.5 · 2 @ 1.0 · **0 @ 1.5 (all F = −32.2, ruin)**. Pre-registered "nets survive" band:
  20–40 bps gross/trade.
- F̂ ≈ 23 = ~150,000 trades × ~1.4 bps × ~1.05× notional leverage, compounded costlessly (notional/equity
  0.93–1.10× ⇒ not a leverage artifact). No-live-stop tail: 1.81% of legs lose > 1R, 0.31% > 2R.
- Discriminating controls (times/exits/sizing held; only the entry price basis moved): ARM-NEXTOPEN F̂
  **0.09–1.93** (below the permuted null 5.66); ARM-OPEN → ruin. Permutation battery v2 is **CONFOUNDED**
  for limit-entry universes.
- Certification **12/12**; `F_floor` cleared **49×–57×**; plateau 0.905–0.955; `keystones: {}`; `pbo_like` 0.0;
  restart terminals near-disjoint (**pairwise Jaccard median 0.108**); **79.9% of the universe is
  gross-profitable standalone** (94.7% on 1H5M; median 1.91 bps/trade).
- Filter structure (364 finalist member slots): **V00 21.2% vs 5.3% = 4.0× over-represented**; 1H5M 75.8%
  (2.3×); H05X 53.3% (2.1×). Median gross/trade V00 1.837 vs filtered 1.922 bps.

### Hypothesis-Specific Conclusion

**NOT SUPPORTED (magnitude).** The edge is real and replicates, but it is **1/15th–1/30th** of the
pre-registered survival band and dies at 0.7 bps of round-trip spread; 91.2% of it is the passive-limit
print, not the registered snap-back mechanism (which contributes 0.172 bps). The analyst's recommendation
(NOT SUPPORTED — magnitude; do not spend a gate slot) and the operator's verdict agree. **The family's
conditioning thesis is contradicted here** (V00 4.0× over-represented).

### Hypothesis-Agnostic Observations

- The permutation battery cannot discriminate on **any** limit-entry universe — it destroys the entry-price
  basis (+7.5 bps/leg) along with the temporal alignment. A design fix is required before the next
  native-fill universe is read.
- Certification on a landscape where ~80% of candidates are gross-profitable confirms **ubiquity**, not
  selection skill: 12 near-disjoint subsets all score F̂ 21–25 and all certify.
- P-10 (passive-limit MR fade) is re-encountered, not escaped: the emission is an ~80%-occupancy two-sided
  passive quoting grid — a market maker being *charged* the spread it would need to be *paid*.
