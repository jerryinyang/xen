# Phase 021 D0 — Amendment 003 (cost-table coverage for the EXP-090 member universe)

**Date:** 2026-06-24. **Status:** **FROZEN — RATIFIED 2026-06-24 (operator-authorized).** **Nature:** a
**frozen-parameter specification gap** surfaced at EXP-091 Stage 3 (implementation), resolved by defining a
**Phase-021 per-instrument transaction-cost table** covering the instruments the screen must price, under a
documented conservative rule, with the **financing leg zeroed** (operator decision). The shared frozen
`xen.capgeo_cost.COST_CONSTANTS` (Phase-018 / EXP-085) is **NOT edited** — the Phase-021 table is a separate,
experiment-local object, so Phase-018 reproducibility/hash integrity is preserved. **Slot / read impact:** 0
candidate slots, 0 counted TEST reads. Holdout untouched.

**Checkpoint:** `2026-06-23-021-mr-fade-capture-geometry` · **Amends:** `D0-predeclarations.md` §D3 (cost model).

---

## The gap (verdict-material)

D3 freezes the cost model as *"`xen.capgeo_cost` / `xen.financing` … Per-instrument `(RT_i, F_i)` table
**inherited unchanged**."* But the inherited table — `xen.capgeo_cost.COST_CONSTANTS` — defines constants for
**only 4 instruments** (AUDUSD, NZDUSD, USDCAD, USTEC). The **EXP-090 member set spans 13 instruments**:

> EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, XAUUSD, USTEC, US2000, JP225.

Only 3 priced instruments (AUDUSD, NZDUSD, USTEC) have member cells (4 cells total) — below the EXP-091 quorum
of **≥5 net-clearing cells over ≥3 instruments** (D6/4a). Left unaddressed, a `SCREEN_EMPTY` → **G-021
NOT_TRADABLE** verdict would be **forced by cost-table coverage, not economics**. Supplying the missing
constants is a frozen-parameter change requiring this dated amendment.

## A global data-derived RT rule was attempted and **empirically refuted** (recorded)

Per the operator's preference for a principled global rule over hand-set tiers, the transaction leg was tested
for derivation from the data itself. The dataset has **no quoted spread** (8-col schema, no bid/ask), so the
only global route is an **OHLC effective-spread estimator**. Both standard estimators were run on **TRAIN-only
daily real OHLC** (first 49% per file, holdout-fenced) over the 13 member instruments:

| Instrument | Abdi–Ranaldo `RT=4ĉ` | Corwin–Schultz `RT=4ĉ` | documented anchor RT | verdict |
| --- | --- | --- | --- | --- |
| EURUSD | 28.4 | 31.9 | **3.0** | ~9–10× too high |
| AUDUSD | 32.7 | 44.5 | **4.0** | ~8–11× too high |
| USTEC | 58.0 | 83.0 | **5.0** | ~12–16× too high |
| XAUUSD | **0.0** | 46.6 | **6.0** | degenerate / divergent |
| USDCHF | **0.0** | 32.7 | — | degenerate / divergent |
| GBPJPY / AUDJPY | **0.0** | 37.3 / — | — | degenerate |

**Conclusion: the global data-derived route is not viable on this dataset.** At the only available frequencies
the high–low range is **dominated by volatility, not spread**, so the estimators either inflate ~10× (EURUSD's
true effective half-spread is well under ~0.5 bps; the estimator returns ~7–8 bps) or clamp to 0 on negative
covariance. The two estimators disagree by 2–∞×. This is exactly the academic-finance pitfall the programme
rejects (an estimator whose assumptions fail on the data). **The attempt is recorded as a refuted approach;** the
cost table reverts to documented anchors. *(Preview code retained in the session scratchpad; not an experiment
artifact — TRAIN-only, 0 reads, holdout untouched.)*

## Resolution — conservative RT from documented anchors; **financing F = 0**

**Transaction leg (RT), binding.** `RT_i = 4 · c_i` (CONSERVATIVE = 2×BASE = 4× one-way — the existing rule; it
reproduces the 4 EXP-085 constants exactly, e.g. USTEC `4×1.25 = 5.0`). `c_i` is taken from a **documented prior
ratified cost read** where one exists, else assigned to a **liquidity tier at the conservative (higher) end** —
the safe direction for a tradability falsification (higher cost ⇒ harder screen). The non-anchored tier
assignments are now *additionally* justified by the refuted global rule above: no credible data-derived value is
recoverable, so a transparent conservative anchor is the best available.

**Financing leg (F = 0), binding (operator decision 2026-06-24).** Swap/carry is an external broker rate, absent
from the OHLC dataset and not derivable from it. The admitted edge is a **~3-bar fade**, for which financing is
an immaterial slice of total cost: with the prior conservative `F=1.2 bps/day`, the financing share at the
**typical ~3-bar hold** is ~1% (15m) to ~4% (1h) of the transaction cost, and reaches ~3–12% only at the 40-bar
cap. The operator sets **F = 0 for all instruments** — a small, disclosed, mildly anti-conservative
simplification (it under-charges only the minority of events that run to the long-hold cap; the dominant cost is
the conservative RT). `event_costs` is called with `fin_bps_day = 0.0`; the cost is RT-only.

### Frozen `(RT_i, F_i)` for the 13 member instruments (CONSERVATIVE RT; F = 0)

| Instrument | Class | `c_i` | **`RT_i`** | **`F_i`** | RT provenance |
| --- | --- | --- | --- | --- | --- |
| **EURUSD** | FX major (tightest) | 0.75 | **3.0** | **0.0** | documented (EXP-030 `c`) |
| **GBPUSD** | FX major | 1.00 | **4.0** | **0.0** | tier (AUDUSD/USDCAD anchor) |
| **USDJPY** | FX major | 1.00 | **4.0** | **0.0** | tier |
| **USDCHF** | FX major | 1.00 | **4.0** | **0.0** | tier |
| **AUDUSD** | FX major | 1.00 | **4.0** | **0.0** | RT unchanged (EXP-085); F zeroed |
| **NZDUSD** | FX major | 1.125 | **4.5** | **0.0** | RT unchanged (EXP-085); F zeroed |
| **EURJPY** | FX cross | 1.50 | **6.0** | **0.0** | tier (conservative) |
| **GBPJPY** | FX cross | 1.50 | **6.0** | **0.0** | tier (conservative) |
| **AUDJPY** | FX cross | 1.50 | **6.0** | **0.0** | tier (conservative) |
| **XAUUSD** | Metal | 1.50 | **6.0** | **0.0** | documented (EXP-030 `c`) |
| **USTEC** | Equity index | 1.25 | **5.0** | **0.0** | RT unchanged (EXP-085); F zeroed |
| **US2000** | Equity index | 1.50 | **6.0** | **0.0** | tier (small-cap, wider than USTEC) |
| **JP225** | Equity index | 1.50 | **6.0** | **0.0** | tier (conservative) |

- The Phase-021 RT values for AUDUSD/NZDUSD/USTEC **equal** their EXP-085 RT (4.0 / 4.5 / 5.0) by construction
  (same `RT=4·c` rule), but this is a **separate Phase-021 table** — the shared `COST_CONSTANTS` object is not
  mutated, so EXP-085 / Phase-018 still reads its own `(RT, F)` (incl. `F>0`) unchanged.
- Out-of-member-set instruments (BTCUSD, US500, DE30, USDCAD) are not member-screened and not in the Phase-021
  table.
- The faster-turnover sensitivity companion (D3) uses `RT_i/2` (1×BASE), F still 0.

## Implementation note (binding)

The Phase-021 cost table is an **EXP-091-local frozen constant** (e.g. `MR_COST_RT_BPS` in
`code/run_experiment.py`), **not** an edit to the shared `xen.capgeo_cost.COST_CONSTANTS` (which stays
byte-identical, preserving Phase-018 / EXP-085 hash integrity). EXP-091 imports only the **cost mechanics** —
`xen.capgeo_cost.event_costs` (signature already takes `rt_bps`, `fin_bps_day` as arguments) and
`holding_days` — and calls them with the Phase-021 `RT_i` and `fin_bps_day = 0.0`. The `event_costs` /
`holding_days` / `financing` logic is unchanged (financing evaluates to 0 with `fin_bps_day = 0.0`). A provenance
hash of the Phase-021 table is recorded in EXP-091 `run_metadata.json`.

---

*FROZEN — RATIFIED 2026-06-24 (operator-authorized). The §D3 extension (+ F=0) is reflected inline in
`D0-predeclarations.md` with a back-pointer here. EXP-091 resumes at Stage 3. The G-021 adjudication checklist
reads the cost model against this amended table.*
