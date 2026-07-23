# CF-VOLDIR-001 — Structural Volatility + Direction Programme

- **Status:** `REGISTERED` — 2026-07-23, checkpoint-017, operator-authorised
- **Chapter:** 06
- **Route:** `SPDR-012` (vol) → `SPDR-013` (direction expectancy) → mid-checkpoint reflection →
  `SPDR-014` (combination / extraction) → conditional `XENA-VOLDIR-001`
- **Reads:** TRAIN only; 0 counted TEST reads; global holdout sealed
- **SPDR-012/013:** designs complete 2026-07-23; execution not authorised
- **Checkpoint:** `docs/experiments-docs/checkpoints/2026-07-23-017-structural-vol-direction-programme/design.md`
- **Governing RAW brief:** `.ignore/what-next/alts/vol-direction-structural-programme-raw.md`
- **Distinct from:** `CF-VOLCONV-001` (closed L1 path: assumed vol + late range-break direction)

## 1. Falsifiable thesis (programme-level)

Volatility is comparatively reliable as a market object and must be **measured** to a reliability
standard before use. Direction is the hard part and must be scored by **availability-when-right,
damage-when-wrong, and expectancy in bps** — never win-rate. Only after both are quantified may
combination (or conditional direction-agnostic extraction) be attempted. Failure after adequate A
and B is a **capture-geometry** or **compatibility/regime-alignment** diagnosis, not “markets empty.”

```text
MECHANISM:
  Separate claims in order: (A) vol predictability/reliability on retained catalog;
  (B) fast direction models scored by expectancy bps under TF-style capture geometry;
  (C) operator reflection freezes combination design from observations;
  (D) vol×direction or vol×direction-agnostic extraction; if A+B ok and D fails →
  geometry or compatibility; (E) XENA only if D graduates a cost-surviving base.
DERIVED:
  estimands=step-specific (vol reliability; direction expectancy bps; combination residue)
  null=time/label shuffles; matched non-signal timing; baseline SMA for direction arms
  horizon=predeclared per SPDR design (intraday-relevant; no multi-day drift product)
  test=reliability metrics (A); expectancy bps (B); combination vs diagnosis (D)
```

This is a **structural decomposition programme**, not a late-confirmation conversion test and not a
re-parameterisation of SPDR-011’s range-break object.

## 2. Lineage and distinctness

| Prior work | Result | Boundary |
|---|---|---|
| Programme residue set (2026-07-14 consolidated) | HTF-DI, FX VR&lt;1, gross bounce, maker print, drift, outcome shape | Premise uses **vol/magnitude** half; not DI re-entry as default direction |
| `CF-VOLCONV-001` / SPDR-011 | L1 NOT SUPPORTED; late breakout assumed direction | **New family**; no primary daily-range breakout direction device without new evidence |
| P-01 directional geometry | Availability ≈ random | Fast SMA/ZigZag expectancy objects, not pattern zoo |
| Capture/cost lessons | Mode B/C dominant | Expectancy includes damage when wrong; combination money floor before XENA |

## 3. Procedural claim order (binding)

| Step | Item | Pass gate to next |
|---|---|---|
| **A** | SPDR-012 vol characterisation | Predeclared reliability bar met |
| **B** | SPDR-013 direction expectancy | Honest expectancy object; primary metric ≠ win-rate |
| **C** | Mid-checkpoint reflection | Operator freezes combination design or stop/branch |
| **D** | SPDR-014 combination / extraction | Cost-surviving base under partial-cost disclosure, or terminal diagnosis |
| **E** | XENA-VOLDIR-001 (conditional) | Only if D graduates a base; not for A–C |

**Stop rules:**

- A fails reliability → do not open vol-conditioned combination (B may still run as pure direction
  science only if operator explicitly authorises; default is stop combination path).
- B expectancy ≤ 0 under damage accounting → no signed combination; direction-agnostic only if A
  (and optional ZigZag magnitude) supports it and operator authorises at C.
- D fails after A+B adequate → geometry and/or compatibility diagnosis; optional direction-agnostic
  branch only if risk-manageable and predeclared at C.

## 4. Hypotheses (registered)

| ID | Vehicle | Question |
|---|---|---|
| `CF-VOLDIR-001/HYP-A` | SPDR-012 | Is volatility reliably predictable/modelable on the retained catalog under frozen metrics? |
| `CF-VOLDIR-001/HYP-B` | SPDR-013 | Do frozen fast direction models (SMA benchmark; ZigZag ATR) deliver positive **expectancy bps** under availability-when-right / damage-when-wrong scoring? |
| `CF-VOLDIR-001/HYP-C` | Reflection | Given A+B, which combination or stop/branch is justified? (not a result-producing hypothesis) |
| `CF-VOLDIR-001/HYP-D` | SPDR-014 | Does frozen vol×direction (or authorised direction-agnostic) extraction clear predeclared TRAIN floors under partial-cost disclosure? |
| `CF-VOLDIR-001/HYP-E` | XENA-VOLDIR-001 | Conditional portfolio/search among graduated D bases only |

## 5. Frozen scope (programme defaults; per-SPDR designs may narrow, not expand silently)

### 5.1 Data and fence

- Primary catalog: Bybit USDT linear perps in `data/catalog/` under INFR-011 fence.
- TRAIN only for all SPDR screens. Historical analysis-TEST and global holdout **never loaded**.
- DESIGN / CONFIRM internal TRAIN bands follow fence manifest unless a SPDR design freezes a
  narrower DESIGN-only window (preferred for first screens).
- Chapter-05/06 cost rule: **spread unavailable / not charged**;
  `cost_scope=PARTIAL_FEES_FUNDING_ONLY`; every money figure carries the understatement caveat.

### 5.2 Instruments (family-wide freeze — AMENDMENT-U1)

**Universe:** the **top 25** Bybit USDT linear perps by **30 calendar-day total traded volume**
(USD notional proxy = `sum(close × volume)` on fenced 1m bars).

```
UNIVERSE-PIN:
  metric: sum(close * volume) over 1m bars, band=TRAIN only
  window: [asof − 30d, asof)
  asof_exclusive: train_end_utc from INFR-011 fence (= 2023-12-18T00:00:00Z)
  n: 25
  pin file: docs/signal-registry/candidate-families/cf-voldir-001-universe.json
  recompute: screen code must rebuild ranking from the same rule and assert symbol set equality
```

**Pinned symbols (descending volume):**  
BTCUSDT, ETHUSDT, SOLUSDT, AVAXUSDT, ORDIUSDT, 1000BONKUSDT, TIAUSDT, DOGEUSDT, XRPUSDT,
LINKUSDT, ADAUSDT, BIGTIMEUSDT, BLURUSDT, 1000PEPEUSDT, 1000LUNCUSDT, MATICUSDT, INJUSDT,
SEIUSDT, BNBUSDT, WLDUSDT, PYTHUSDT, DYDXUSDT, GALAUSDT, OPUSDT, 1000RATSUSDT.

**Coverage rule:** names with insufficient DESIGN warm-up remain in the universe; cells with too
few dates are **UNPOWERED**, never silently dropped from reporting. No post-outcome universe edit.

**AMENDMENT-U1 (2026-07-23):** expand instruments from fixed five to top-25 30d volume —
DIRECTION: **NEUTRAL** (scope expansion pre-execution; no outcome contact yet).

### 5.3 Volatility toolkit (permitted axes — freeze concrete arms in SPDR-012 design)

| Axis | Examples | Target |
|---|---|---|
| Persistence / clustering | Autocorr of \|r\|, RV, squared returns; half-life; HAR-style multi-horizon lags | Next-horizon vol predictability |
| Level forecasting | OLS/ridge on lagged RV; HAR-RV; EWMA/RiskMetrics-style | Continuous next-horizon RV / \|move\| |
| Regime models | 2–3 state Markov; HMM on returns or RV | State labels, transitions, OOS persistence |
| Realised measures | Close-to-close RV; Parkinson; Garman–Klass; realised range | Robust magnitude under OHLC |
| Calendar / clock | UTC session, day-of-week, event-free baselines | Seasonality vs AR residual |
| Cross-sectional rank | Relative vol percentile across liquid set | Relative HIGH/LOW |
| Distributional / tail | Conditional quantiles of \|move\|; exceedance in HIGH state | Not mean-only |

**Reliability metrics (freeze numeric bars in SPDR-012 design):** OOS R² / rank-IC / MAE;
state-conditional magnitude separation with CIs (primary for regimes); stability across time
thirds and symbols; collapse under time-shuffle / label-shuffle; minimum useful horizon.

Academic vol methods are **in-bounds** if causal, TRAIN-fenced, and predeclared.

### 5.4 Direction models (frozen class — concrete params in SPDR-013 design)

Preference: **simple, naive or intentionally dumb, but fast**. Cut losers quickly; let winners run
(classic trend-following capture geometry). Capture geometry is part of the model.

**Benchmark — mid-term SMA**

- Periods in {14, 25} primary; **50 maximum**; **200 forbidden** for this programme.
- Buy above / sell below; optional angle/slope filter for flat markets.
- Benchmark that other arms must beat on **expectancy bps**, not win-rate.

**Proposed — ZigZag ATR-based**

- Deterministic ATR ZigZag; alternating-line structure supplies next-leg direction by construction.
- Weaknesses named: fake confirmations; misses early portion of moves.
- Per completed line features: **magnitude**, **binary direction**, **angle/slope**,
  **path-local noise/volatility** (clean vs whipsaw relative to the line’s own price path — not an
  arbitrary detached window).
- Features → AR or light ML to **predict magnitude and/or volatility of the next whole move**
  (move-level aggregation, not only per-bar).
- Supports direction-agnostic extraction when sign skill is weak.
- Signed policies still scored with availability-when-right / damage-when-wrong / expectancy bps.

**Forbidden as primary direction device:** SPDR-011 confirmed daily-range breakout without new
independent evidence.

**Forbidden primary metric:** win-rate / “right X of Y.”

### 5.5 Combination (SPDR-014 — frozen only after reflection C)

- Default path: vol state × direction policy under partial costs.
- Conditional path: direction-agnostic (grid-like / both-side / straddle-class) **only if** C
  authorises after compatibility diagnosis and risk is manageable.
- HTF-DI is **not** smuggled as a third direction arm unless separately predeclared as a named
  benchmark at C — first pass is SMA + ZigZag only.

## 6. Scoring contracts

### 6.1 Direction expectancy (binding for HYP-B)

| When model is… | Measure |
|---|---|
| Right | Availability / capture when correct |
| Wrong | Adverse path when incorrect (damage) |
| Overall | Expectancy in **bps** of the registered unit |

### 6.2 Partial-cost disclosure

Any bps figure that touches trading must disclose: fees + funding (+ allowance if used);
spread not charged; reported net **overstated** relative to true cost.

## 7. Refusals (programme-level)

- Re-running confirmed daily-range breakout as primary direction without new evidence  
- Win-rate as direction success metric  
- Jumping to combination or XENA before A and B quantified  
- Indicator zoos / unbounded ML without frozen arms  
- Historical TEST or holdout for this exploratory path  
- Deployable / fully cost-complete claims under no-spread accounting  

## 8. End-states

1. **Terminal structural package:** vol not reliable enough; and/or direction expectancy ≤ 0 under
   honest damage accounting; and/or combination fails with geometry vs compatibility diagnosis.
2. **Graduated base for XENA:** combination or authorised direction-agnostic extraction clears
   predeclared TRAIN floors under partial-cost disclosure.

## 9. Registration ledger

| Date | Action |
|---|---|
| 2026-07-23 | Operator authorised family registration and checkpoint-017 opening from RAW brief
  `vol-direction-structural-programme-raw.md` (including magnitude **and/or** volatility next-move
  target; SPDR-lane pointer). Assigned SPDR-012/013/014; reserved XENA-VOLDIR-001. 0 counted reads;
  no outcome contact yet. |
| 2026-07-23 | **AMENDMENT-U1 (NEUTRAL):** instruments = top 25 by 30d USD volume (TRAIN rank at
  `train_end`). Pin `cf-voldir-001-universe.json`. SPDR-012/013 designs updated. 0 outcomes. |
| 2026-07-23 | **AMENDMENT-A2 (NEUTRAL):** full first-pass options mandatory — V-REGIME-HMM; D1 primary
  clock; M15 clock; SMA 14/25/50; angle on+off; ZZ mag and vol forecast heads. 0 outcomes. |
