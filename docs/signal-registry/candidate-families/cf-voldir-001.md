# CF-VOLDIR-001 — Structural Volatility + Direction Programme

- **Status:** `REGISTERED` — 2026-07-23, checkpoint-017, operator-authorised (**no status change**)
- **Chapter:** 06
- **Route:** `SPDR-012` → `SPDR-013` → Reflection C (O3 + Decision A) →
  `SPDR-014` (zone/event — screen done, pin NONE) → `SPDR-015` (conditioners) → `SPDR-016` (refine 014 residual — open by override) →
  `SPDR-017` (independent predicted-price mispricing; operator original #3) →
  conditional `XENA-VOLDIR-001`
- **Reads:** TRAIN only; 0 counted TEST reads; global holdout sealed
- **SPDR-012/013:** complete (analyses binding). **Reflection C:** signed 2026-07-23.
  **SPDR-014:** screen complete 2026-07-24 — INCONCLUSIVE / UNPOWERED_NOT_NULL (B-5), `residual_status=NONE`,
  0 powered cells, integrity PASS, 0 TEST reads; **SPDR-016 OPENED by operator override** on coherent SUGGESTIVE
  leads (not a powered residual). **SPDR-017:** screen complete, `residual_status=NONE`.
  **SPDR-015:** screen complete 2026-07-24 — **WORTH_EXPLORING (per-arm, operator-signed)**; integrity PASS
  (hard_pass; golden G1–G4); QA run1 REVISE→run2 APPROVE; 0 TEST reads. Ordinal swing-size gate (T-GT-CUR;
  21/21 coins × 3 models, hit ~+20pt over base, IC≈0.37, CI-backed) + vol level-state labels (next-|oo| gap
  +35 bps HMM / +16 bps R-MARKOV) + R-MARKOV multi-bar gate k=4/12 (16/16 coins H1; ΔBrier −0.025 k4 / −0.114
  k12, CI excl 0) route on; k=1 next-bar NOT_WORTH. Conditioners fold into 014/016 by amendment only; no
  family status change; no XENA. (No `residual_status` — conditioner science, not a residual object.)
- **O3 sequence brief:** `.ignore/what-next/alts/cf-voldir-o3-zone-event-sequence.md`
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
| **A** | SPDR-012 vol characterisation | **COMPLETE** — H1/H4 range level adequate for conditioning |
| **B** | SPDR-013 direction expectancy | **COMPLETE** — signed not adequate; ZZ mag positive |
| **C** | Mid-checkpoint reflection | **SIGNED** — O3 only; Decision A sequence |
| **D1** | SPDR-014 zone/event / MOMO–MR | **SCREEN COMPLETE (2026-07-24)** — INCONCLUSIVE / UNPOWERED (B-5); `residual_status=NONE` (0 powered cells); no terminal residual named; SPDR-016 opened by operator override on SUGGESTIVE leads |
| **D2** | SPDR-015 conditioner science | **SCREEN COMPLETE (2026-07-24)** — **WORTH_EXPLORING** (operator-signed): ordinal swing-size gate + vol level-state labels + R-MARKOV multi-bar gate (k=4/12) route on; k=1 next-bar NOT_WORTH. Improves gates/labels for 014/016 by amendment only |
| **D3a** | SPDR-016 refine 014 residual | **OPEN by operator override** (2026-07-24) — pin is NONE; opened on 014's coherent SUGGESTIVE leads, residual object + policy deferred to 016 design |
| **D3b** | SPDR-017 independent mispricing (#3) | Own model; **not** gated on 014 residual NONE |
| **E** | XENA-VOLDIR-001 (conditional) | Only if a base graduates; not for A–C |

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
| `CF-VOLDIR-001/HYP-D1` | SPDR-014 | Zone / mispricing event / post-event MOMO vs MR residual ≠ ambient? |
| `CF-VOLDIR-001/HYP-D2` | SPDR-015 | Level-regime transition skill vs persistence; ordinal ZZ “bigger than” skill? |
| `CF-VOLDIR-001/HYP-D3` | SPDR-016 | Do error-dynamics features refine the **014 residual** without open ML zoo? (014-gated) |
| `CF-VOLDIR-001/HYP-D4` | SPDR-017 | Independent predicted-price mispricing (proven + error dynamics + weak-dir features) characterised like 014 — residual ≠ ambient? |
| `CF-VOLDIR-001/HYP-E` | XENA-VOLDIR-001 | Conditional portfolio/search among graduated bases only |

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

### 5.5 O3 extraction sequence (frozen after Reflection C Decision A)

- **Signed vol×direction product: closed** (013 evidence).
- **SPDR-014:** likelihood zone from vol level / ZZ mag → breach event → characterise MOMO vs MR
  (do not assume). Primary product science.
- **SPDR-015:** level-HMM/Markov transitions vs persistence; ordinal ZZ magnitude gates.
- **SPDR-016 (3a):** refine named 014 residual; start-gated on 014 pin — **opened by operator override 2026-07-24** (pin NONE; on 014's SUGGESTIVE leads).
- **SPDR-017 (3b):** operator original #3 — independent predicted-price mispricing + 014-style
  MOMO/MR characterisation; **not** gated on 014 residual success.
- **AMENDMENT-S1:** per-symbol SUPPORTED allowed; multi-symbol agreement = credibility only.
- HTF-DI not a direction arm unless separately predeclared. No range-break primary.

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
| 2026-07-23 | **Reflection C SIGNED:** O3 only; Decision A. Sequence brief
  `cf-voldir-o3-zone-event-sequence.md`. SPDR-014/015/016 designs registered. **AMENDMENT-S1
  (NEUTRAL):** per-symbol sufficiency for O3 screens. Status remains REGISTERED. 0 outcomes. |
| 2026-07-24 | **SPDR-017 registered (NEUTRAL):** operator original Group-3 intent as independent
  predicted-price mispricing (HYP-D4). SPDR-016 kept as 014-gated refine (3a). Design complete.
  Status remains REGISTERED. |
| 2026-07-24 | **SPDR-014 / HYP-D1 disposition (evidence only):** screen complete. Analyst INCONCLUSIVE /
  UNPOWERED_NOT_NULL (B-5); `residual_status=NONE`, 0/927 powered cells; integrity PASS; band non-selective
  (p_event≈1), continuation ≈ coin-flip; DESIGN→CONFIRM sign flip (12/17). Coherent SUGGESTIVE leads:
  shock-MOMO (pooled CI excl 0), E-TOUCH/E-CLOSE asymmetry, L→H vol-flip MOMO. 0 counted TEST reads.
  **SPDR-016 OPENED by operator signed override** (`016_start_basis=OPERATOR_OVERRIDE`) on the SUGGESTIVE
  leads — NOT a powered residual; residual object + policy deferred to 016 design. Status remains REGISTERED. |
| 2026-07-24 | **SPDR-015 / HYP-D2 disposition (evidence only):** screen complete, operator-signed
  **WORTH_EXPLORING (per-arm)**. Integrity PASS (hard_pass; golden G1–G4); control = true L-28 derangement both
  arms (collapse≈0; +0.05 bite detected 98%/73%); QA run1 REVISE→run2 APPROVE; 0 counted TEST reads.
  **Route on:** 2b ordinal swing-size gate T-GT-CUR (21/21 coins × 3 models; hit ~+20pt over base; IC≈0.37;
  CI-backed) + 2a vol level-state HIGH/LOW labels (next-|oo| gap +35 bps HMM / +16 bps R-MARKOV) + 2a R-MARKOV
  multi-bar gate k=4/12 (16/16 coins H1; ΔBrier −0.025 k4 / −0.114 k12 = ~15%/33% less error than persistence,
  CI excl 0). **NOT_WORTH:** k=1 next-bar (R-MARKOV thin; H4 k1; R-HMM-RV forecast); R-SHOCK comparator only.
  Conditioner science — folds into 014/016 gates/labels by amendment only; no `residual_status`; no XENA. Status
  remains REGISTERED. |
