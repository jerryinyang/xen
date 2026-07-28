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
- **Checkpoint-017:** `docs/experiments-docs/checkpoints/2026-07-23-017-structural-vol-direction-programme/design.md`
  — **CLOSED 2026-07-25** (`retrospective.md`): `STRUCTURAL PACKAGE DELIVERED / EXTRACTION
  UNRESOLVED-AT-POWER`. **SPDR-016 CLOSED — SUPERSEDED, NEVER RUN.** 0 TEST reads, 0 slots,
  status unchanged.
- **Checkpoint-018 (current):**
  `docs/experiments-docs/checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/design.md`
  — **OPEN 2026-07-25**, trade-opportunity modelling / capture geometry; an **extension** of 017,
  not a new family. SoT: `.ignore/what-next/alts/opportunity.md`
- **Governing RAW brief (017):** `.ignore/what-next/alts/vol-direction-structural-programme-raw.md`
- **Distinct from:** `CF-VOLCONV-001` (closed L1 path: assumed vol + late range-break direction)

## 0. Checkpoint-018 binding premise and identity

> **Unconditional direction is dead. Conditional direction is unpowered, not refuted. Volatility is
> a multiplier on a direction term, never a substitute for it.**

**Identity:**

```
E[net per leg] = p·W − (1−p)·L − cost
  p = P(r_h > 0 | state)   W = E[r_h | r_h > 0]   L = E[−r_h | r_h < 0]
  p_be_net = (L + cost)/(W + L)        edge = p − p_be_net
```

Exact by the definition of conditional expectation.

- **The target is not "`p > 0.5`"** — it is "`p` above its own `p_be_net`", satisfiable at
  `p < 0.5` when `W > L`.
- **`W/L` is a real, measurable, unclaimed degree of freedom** and is the natural handle for the
  capture branch.
- **κ is a diagnostic, never a multiplicative term.**
- **Direction is measured, not targeted** — no work in this checkpoint tries to improve `p`,
  select a better entry, or build a direction model. Entries stay simple and fixed.

Axis A (`p`) and axis B (`W`, `L`, `W/L`) are `SPDR-018`. Axis C (`E[|move|]`) is proven and
supplies **selection + parameter scale, never edge**. Axis D (capture) is `SPDR-019`/`SPDR-020`.
Axis E (cost) is blocked on a per-symbol spread pin.

**Refused by construction:** any expectancy claim from exits, holds, or sizing on a joint
`(p, W, L)` that does not clear `p_be_net` at power (the analytic `E[gross]=0` kill —
`CF-VOLHARV-001/HYP-001`, reproduced by SPDR-013's `time` arm).

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
| **D3a** | SPDR-016 refine 014 residual | **CLOSED — SUPERSEDED, NEVER RUN** (2026-07-25). DERIVED feature layer measured inert by SPDR-017; target carried into `SPDR-018` arm C, in the original event-nested form. 0 reads |
| **D3b** | SPDR-017 independent mispricing (#3) | **CLOSED — NOT_WORTH** (2026-07-24) — model IC ≈ 0; DERIVED layer inert; destroys indistinguishable; M-ZONE ≤ Z-VOL |
| **D5** | SPDR-018 power the complete 017 residue | **DESIGN COMPLETE** 2026-07-25 (checkpoint-018); execution unauthorised |
| **D6** | SPDR-019 strategy #1 (naive baseline) + opportunity score + capture test set | **REGISTERED** 2026-07-25 — start-gated on the SPDR-018 reflection |
| **D7** | SPDR-020 event-grammar direction-aware capture | **REGISTERED** 2026-07-25 — start-gated on the SPDR-018 reflection |
| **E** | XENA-VOLDIR-001 (conditional) | Only if a base graduates; not for A–C. **RESERVED, never opened** |

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
| `CF-VOLDIR-001/HYP-D5` | SPDR-018 | For every question checkpoint-017 left **UNPOWERED or INCONCLUSIVE**, measured in its **original statement**: can it be resolved to its own target precision on this data, and if so what is the answer? Covers the complete residue of SPDR-012/013/014/015 (only authorised drop: SPDR-017), plus a uniform `(p, W, L, W/L, p_be_net, edge)` decomposition on every cell carrying a signed return |
| `CF-VOLDIR-001/HYP-D6` | SPDR-019 | Given the `(p, W, L)` picture from D5, does opportunity-modulated capture geometry on a **fixed signed breakout entry** (selection, hold, exits, sizing scaled to forecast move) move the payoff residual `log R = log(W/L) − log((1−p)/p)` reliably above zero — i.e. `p` above its own **gross** break-even — versus the unmodulated baseline? *(Narrowed from partial-net-above-cost-floor by **AMENDMENT-C5**, 2026-07-28; tested layer-by-layer per **AMENDMENT-C6**.)* |
| `CF-VOLDIR-001/HYP-D7` | SPDR-020 | Same question on the SPDR-014 E-TOUCH / E-CLOSE event object under direction-aware capture, with a band that actually selects *(same C5 / C6 amendments)* |
| `CF-VOLDIR-001/HYP-E` | XENA-VOLDIR-001 | Conditional portfolio/search among graduated bases only |

**Checkpoint-018 hypothesis notes.** `HYP-D5` is a **precision experiment**, not a mechanism
experiment: each arm inherits its parent screen's mechanism, object and estimand verbatim, and only
the data behind each estimate changes (parent parity asserted in code). `NOT_RESOLVABLE` — a cell
that cannot reach its target precision in its original form — is a **first-class result**, not a
failure. `HYP-D6`/`HYP-D7` are start-gated on the D5 reflection: no capture rule can produce
expectancy from a joint `(p, W, L)` sitting at `p_be_net`. `HYP-D3` (SPDR-016) is closed superseded;
its intent survives inside D5's arm C.

**`HYP-D6`/`HYP-D7` measurement contract (AMENDMENT-C5 / C6, 2026-07-28).** Both are **gross**
experiments: cost is excluded from every estimand, threshold and comparison, with `p_be_net` and the
cost floor reported per cell as a **disclosed reference only**. The null is the driftless mirror
(`log R = 0`), never zero P&L — 32.5% of SPDR-018's powered cells already clear gross break-even, so a
gross screen scored against zero would re-discover that and call it an effect. Both run the
**layer-by-layer protocol**: phase (a) sequential characterisation (L0 baseline → L1 scale → L2 state →
L3 swing gate → L4 devices individually, each unmodulated *and* modulated → L5 evidence-selected
combination), then phase (b), a full layer × device cross whose **trigger** depends on (a) but whose
**scope does not** — individually-flat layers stay in the grid, and (b)'s estimand is the interaction
term. Full statement: the mid-checkpoint reflection companion, §5.4a and §5.9. **AMENDMENT-C2 still
binds every claim**; C5 governs measurement only.

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
| 2026-07-25 | **CHECKPOINT-017 CLOSED** (`STRUCTURAL PACKAGE DELIVERED / EXTRACTION UNRESOLVED-AT-POWER`).
  Neither frozen end-state honestly claimable: no cost-surviving base graduated, **and** the extraction
  failure was never established (SPDR-014 0/927 powered cells, MDE 20/172/796 bps vs a ≤10 floor — B-5
  forbids reading unpowered as negative). **SPDR-016 CLOSED — SUPERSEDED, NEVER RUN**: its DERIVED
  error-dynamics layer was independently measured inert by SPDR-017 (A1−A0 median −5.8 bps; 5/16 improve),
  and its target (powering the 014 leads) is carried forward as SPDR-018 with ~60–100× the n. Supersede-and-retain;
  0 reads consumed. 0 counted TEST reads; 0 multiplicity slots; XENA never opened. Status remains REGISTERED. |
| 2026-07-25 | **CHECKPOINT-018 OPENED — Trade Opportunity Modelling / Capture Geometry** (extension of 017,
  not a new family). SoT `.ignore/what-next/alts/opportunity.md` operator-signed. Binding premise recorded
  (**unconditional direction dead; conditional direction unpowered-not-refuted; volatility multiplies a
  direction term, never substitutes for it**) together with the organising identity
  `E[net] = p·W − (1−p)·L − cost` (`p_be_net = (L+cost)/(W+L)`, `edge = p − p_be_net`).
  **Registered `SPDR-018` (`HYP-D5`),
  `SPDR-019` (`HYP-D6`), `SPDR-020` (`HYP-D7`)** — designs pending, execution unauthorised; 019/020
  start-gated on the SPDR-018 mid-checkpoint reflection. **AMENDMENT-C1 (NEUTRAL):** cTrader instruments
  (EURUSD/XAUUSD/USTEC, INFR-021 fence) admitted as an **independent replication read only** — never
  pooled into the powered crypto estimate; separate fence (`train_end` 2023-11-22), holdout 2024-12-13+
  sealed. **AMENDMENT-C2 (TIGHTER):** expectancy claims from exits/holds/sizing are refused unless the joint
  `(p, W, L)` clears `p_be_net` at power; blended opportunity scores must carry their term-level decomposition; per-symbol
  spread pin is a prerequisite for checkpoint-018 money reads. Pure direction-agnostic objects deferred by
  operator (parked, not refuted). 0 outcomes, 0 reads. Status remains REGISTERED. |
| 2026-07-25 | **SPDR-018 design complete (execution unauthorised).** A **powering sweep over the complete checkpoint-017 residue**, each item in
  its **original statement, no omissions** — arm A (SPDR-012 residue), arm B (SPDR-013 residue, where
  `W`/`L` are measured on real episodes), arm C (SPDR-014 residue in the original event-nested form,
  incl. `DA-STRADDLE` as **characterisation only**, an operator exception to the direction-agnostic
  deferral), arm D (SPDR-015 residue incl. the never-scored CONFIRM slice). **Only authorised drop:
  SPDR-017** (NOT_WORTH on decisive mechanism grounds — powering an absent mechanism buys nothing).
  Multiplicity **disclosed, not rationed** (operator directive: these are follow-up confirmations of
  registered open questions, not new candidate mining). Reuses the parents' `screen_code/` with **parent
  parity asserted in code**. `NOT_RESOLVABLE` is a first-class result. 0 outcomes, 0 reads. Status remains
  REGISTERED. |
| 2026-07-26 | **SPDR-018 COMPLETE AND CLOSED — `HYP-D5` SUPPORTED (evidence row; NOT a status transition).**
  Powering succeeded and carries **no gating verdict** (checkpoint design §2). Code pin `44c720f82af52b8b…`;
  37,791 cells / 24,098 signed; **18 HARD checks, 0 failed**; parent parity 4.5e-13 / 1.8e-12 / 9.1e-13 / 0.0
  across arms A–D proves **no estimand was re-specified**. **1,413 powered signed cells against SPDR-014's
  0 of 927**; all 27 residue items carry cells; **3,559 `NOT_RESOLVABLE`** delivered as a quantified answer
  (median 7.87× short, p90 27.3×). **Axis-B is discharged — `W`, `L`, `W/L` are now measured**, identity
  `p·W − (1−p)·L = mean` reconstructing to **1.46e-11 bps**: `p` **0.3887**, `W` **128.65**, `L` **75.55**,
  `W/L` **1.4844**, `p_be` 0.4025, `p_be_net` **0.4992**, **edge −0.0728**, gross **−1.18 bps**, net −15.16
  (all medians across powered cells; cross-cell means: `p` 0.3781, `W` 128.81, `L` 84.69, `W/L` 1.7548,
  `p_be_net` 0.4641, edge −0.0860, gross −1.19 — **`edge` is not the difference of the other medians;
  read it from its own column**).
  **0 of 1,413 clear `p_be_net`; 32.5% clear gross break-even.** The gap is **90.7% cost, not rate** (arm C
  98.8%; its rate sits 0.0007 from its own gross break-even). **`W/L` is NOT a free degree of freedom:**
  R² **0.9667** against the driftless mirror `(1−p)/p`, exit geometry moves it **67×** while `p` moves
  inversely, free residual `log R` sd 0.073 with a **negative median (−0.0301) and mean (−0.0356)** — though `log R > 0` in **459 of 1,413 cells (32.5%)**, which is the *same* 32.5% that clears gross break-even, by identity; it is the CENTRE that is negative, never every cell, **82.8%** of powered cells
  indistinguishable from the mirror. **Powered counter-outcome exists and does NOT route** (129 negative
  CI-excl-0 cells vs 1 positive; best flipped +12.93 bps against a 13.1–16.0 floor) → **end-state 3 checked
  and not satisfied at this cost floor**. Surviving live thread: **C2 shock-MOMO**, M-3 live +22.6 bps,
  pct 0.95, n 505. Still `UNPOWERED`-not-refuted: **C3** (1,946 cells = 55% of the unresolved population).
  Recorded gaps: arm-C parity 72.5% complete, median/trimmed CIs on 1.0% of cells while the three statistics
  disagree by 13 bps, M-2 span missing on 13.9%. **0 counted TEST reads; 0 multiplicity slots; no XENA;
  status remains REGISTERED.** Family action deferred to the checkpoint retrospective. |
| 2026-07-26 | **SPDR-018B COMPLETE AND CLOSED — `HYP-D5` PARTIALLY SUPPORTED (evidence row; NOT a status
  transition).** Second universe under AMENDMENT-C1: cTrader EURUSD/XAUUSD/USTEC, INFR-021 fence, **3
  instruments against 25**; 7,578 cells; **11 HARD checks + 1 INFORMATIVE, 0 failed**. **REPLICATION AND
  CREDIBILITY ONLY — never pooled into crypto `n`, never cited as power for the crypto estimate**
  (AMENDMENT-C1 / S1). Cost is **DOUBLY SYNTHETIC** (borrowed from Bybit *and* rescaled); gross primary;
  per-symbol spread pin still **BLOCKING**. **The structural result replicates, and more tightly than on
  crypto:** `p` **0.4868** vs `p_be` **0.4855** (gap **+0.0013**), gross mean **−0.080 bps = 0.006σ**,
  `W` 24.66 / `L` 20.99 / `W/L` 1.0597, `p_be_net` 0.5334, **edge −0.0544**, cost = **95.8%** of the gap,
  **0 of 315 powered cells clear `p_be_net` — at both charges and at ANY charge above 1.39 bps** (best cell
  +1.389 bps gross). **`W/L` mirror replicates at R² 0.9746 / slope 0.9656** (tighter than crypto's 0.9667 /
  0.9408), 93% of cells indistinguishable from the mirror, `W/L` **36.4×** movable with `p` inverse and no
  improvement in the mean — measured with **all five exit geometries**, which SPDR-018's cTrader leg could
  not do. **C2 — the replication target — is NOT REPLICATED AND NOT REFUTED**, and its 018B evidence may be
  cited only as a *"does not transport cleanly"* flag: the comparator is not a neutral yardstick (own mean
  +0.97 EU → +3.46 US → +12.05 Asia; the Asia null lies entirely above zero; blind upward at +20 bps), the
  effect **vanishes in EU** (+0.62, pct 0.443) and concentrates in **Asia** (−13.57, n 184), the like-for-like cell
  (n 290) **was** powered for an effect of crypto's size (its plant curve reads 1.000 at +20 and +40
  bps) and measured the OPPOSITE sign at pct 0.043 — a powered non-replication on that cell, which
  strengthens "not replicated" and removes one of the four supports for "not refuted"; and an independent rebuild reproduces every live
  value but **flips `P-MR`** (pct 0.067 → 0.826). **Three prior headline figures corrected:** powered
  2,401 → **315**, net-clearing 12.9% → **0.0%**, mirror R² 0.311 → **0.9746** — all three traceable to an
  absolute-bps precision bar imported across a 5.6× volatility-scale boundary (**L-50**; correction applies
  to 018B only, SPDR-018 **not reopened** by operator ruling). Coverage gaps closed under **native**
  definitions: C7 (627 pairs, flip rate 40.99% below chance, bands agree to 0.65 bps `n`-weighted), C8 (339
  cells, weightings agree to 0.0009), B3 (159 cells — **0 of 159 powered, 16.4× short**). **OPEN / NOT RUN and
  never to be read as nulls: C9 (`DA-STRADDLE`), D3, D4.** Recorded exposures: **seven inherited HARD checks do
  not exist** (determinism among them, on a resumed run; plus the Bybit-holdout assertion on the §5 guard =
  the only residual Phase-0 exposure), the cost deflator is **circular with a defensible range 0.185–0.703**
  (**L-53**), no median/trimmed CIs and no fragility sweeps emitted at all, power flag not regenerable
  (317 vs 315). New unregistered lead **P6**: Asia magnitude×shock ≈ +10 bps vs ≈ 0 in EU on 162–184 rows —
  **must be registered before it is screened**. **0 counted TEST reads; 0 multiplicity slots; no XENA; status
  remains REGISTERED.** |
| 2026-07-28 | **MID-CHECKPOINT REFLECTION — VOLATILITY EVIDENCE + CAPTURE-GEOMETRY MODEL (evidence + amendment row; NOT a status transition).**
  Artifact: `docs/experiments-docs/checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/reflection-mid-volatility-model.md`
  (companion to `reflection-inputs.md`, whose §9 operator decision remains unsigned). Consolidates every
  confirmed volatility observation from SPDR-012/013/015 and SPDR-018/018B into a 28-row inventory (V1–V28),
  **each carrying an explicit evidence class** — powered-at-target `[P]`, scored-without-a-bps-target `[S]`,
  disclosure `[D]`, unpowered `[U]` — and states the capture-geometry model they support: a five-layer stack
  (units → scale ŝ → shock/level state → swing gate → capture parameters) constrained by the identity.
  **Three corrections booked against the first draft of that document** (independent audit; no source
  experiment affected): (i) the free residual is the **exact** `log R = log(W/L) − log((1−p)/p)` — slope 1,
  intercept 0, forced by `E[gross]=0` — **not** the fitted-slope form; the exact residual reproduces
  SPDR-018's reported median −0.0301 / mean −0.0356 / sd 0.0729 / 32.5% positive, whereas the regression
  residual is centred at zero by construction (median +0.0019, 51.8% positive) and **cannot be a target**;
  (ii) the **67× `W/L` movability is `[U]`** — `stop`, `time` and `trail` each have **0 of 1,022 cells at
  target precision** on crypto, so the powered `W/L` span is **5.3×** (0.998 → 5.25; cTrader 5.0×), and the
  powered statement is "a 5.3× range produced no lift"; (iii) `1 − R²` is unexplained cross-cell variance,
  **not** an opportunity budget. D2 (run-length) and the ambient-base reads reclassified `[D]`; D7 confirmed
  `[S]` (60/75 SUPPORTED, no bps target); A-IC's 165-cell figure **verified exactly** (CONFIRM × H1 ×
  per-symbol × 11 models, 100% CI-excluding-zero, median 0.3262 — of which 68.9% also meet target precision).
  **AMENDMENT-C5 (NARROWING — operator directive 2026-07-28): cost is excluded from every SPDR-019/020
  exploration test.** `HYP-D6` and `HYP-D7` as registered ask for *partial-net expectancy above the cost
  floor*; both are narrowed to the **gross** condition `log R > 0 ⟺ p > p_be`. Rationale: failure on cost and
  failure of the capture mechanism are different failures, and charging an unpinned floor conflates them. The
  narrowing costs nothing in rigour — the residual target contains no cost term. **`p_be_net` and the cost
  floor remain reported per cell as a disclosed reference**; the per-symbol spread pin **no longer blocks the
  measurement** but still blocks every money read, expectancy claim and Step-3 graduation. **AMENDMENT-C2 is
  unchanged and still binds every *claim*** — this amendment governs measurement only. Pre-empted risk
  recorded: 32.5% of powered cells already clear gross break-even, so **the driftless mirror is the
  pre-registered null and no capture variant may be scored against zero P&L.**
  **AMENDMENT-C6 (TIGHTER — operator directive 2026-07-28): layer-by-layer test protocol, binding on both
  `SPDR-019` and `SPDR-020`.** Phase **(a)**, sequential and run in full on both strategies: L0 unmodulated
  baseline (its own `p_dir`, `W`, `L`, κ measured first) → L1 scale alone → L2 state alone (shock, level, then
  joint) → L3 swing gate alone → L4 capture devices **one at a time**, each run **twice — unmodulated and
  modulated** → L5 a small evidence-selected combination. Phase **(b)**, the full layer × device cross:
  **phase (a) determines WHETHER (b) runs; it does NOT determine WHAT is in it.** Winners-only combination is
  refused on two recorded grounds — selecting (a)'s winners and combining only those fits the combination to
  the sample that chose its components, and **a layer can be flat alone yet productive in combination**, which
  pruning makes permanently undiscoverable. Consequences: the (b) trigger is **pre-declared before (a) runs**
  (deciding afterwards what counted as promising is optional stopping); (b)'s scope is **fixed and complete**
  regardless of (a)'s outcome, with individually-flat layers retained on equal footing; (b)'s estimand is the
  **interaction** `Δlog R(combined) − Σ Δlog R(individual)`, not the combined main effect; multiplicity
  disclosed across the declared grid; per-cell MDE stated in log units up front, and a grid that cannot
  resolve the interaction is booked `NOT_RESOLVABLE` rather than run and explained. A layer that reads flat is
  a result and is reported as one. **P6 (018B determinism + the Bybit-guard holdout assertion) SKIPPED by
  operator directive** — recorded as an open gap, not a blocker; any future citation of 018B's §5 guard reads
  must carry the caveat. **0 counted TEST reads; 0 multiplicity slots; no XENA; no family action; status
  remains REGISTERED.** Family transitions remain retrospective-only. |
| 2026-07-28 | **AMENDMENT-C7 (NEUTRAL — operator mandate): retire the single canonical power threshold across `SPDR-019` and `SPDR-020`.**
  The mid-checkpoint reflection originally named **+0.03 to +0.07 log units** as the effect a capture policy must
  reach on the payoff residual `log R`, and the two designs turned 0.07 into a `powered` / `unpowered` adequacy
  label. **Both are withdrawn.** The numbers were anchored on `sd(log R) = 0.0729` and `median log R = −0.0301` —
  the **dispersion** and **location** of the observed residual — neither of which is a statement about what effect
  size matters to the research. Two replacements, both operator-approved: **(1) sensitivity analysis** — every cell
  emits a **ladder** `{0.02, 0.03, 0.05, 0.075, 0.10, 0.15}` log units carrying the detection rate and the required
  `n` at each rung, as a presentation grid that admits, excludes, labels and ranks nothing; **(2) precision-first** —
  **no `powered` / `unpowered` / `at_target` / `NOT_RESOLVABLE` flag is emitted anywhere**, each cell reports its
  effect with its **block MDE and CI width bound to the same row**, and adequacy is the reader's judgement, with
  powering left to later verification. Interpretation bands are correspondingly redefined by the **CI's relation to
  the mirror** (above / covers / below) rather than by any magnitude. **B-5 is strengthened, not weakened:** a
  boolean label could be dropped in summary, whereas an effect that cannot be quoted without its own precision
  cannot be read as a negative by omission. Both designs carry the change in their amendment ledgers
  (SPDR-019 AMENDMENT-6, SPDR-020 AMENDMENT-4) and both remain **execution-unauthorised** pending QA run 2.
  **0 counted TEST reads; 0 multiplicity slots; no family action; status remains REGISTERED.** |
