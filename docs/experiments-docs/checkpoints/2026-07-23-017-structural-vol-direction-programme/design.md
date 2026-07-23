# Checkpoint 017 — Structural Volatility + Direction Programme

- **Opened:** 2026-07-23
- **Status:** `OPEN — SPDR-012/013 DESIGNS COMPLETE; UNIVERSE=TOP25; EXECUTION UNAUTHORISED`
- **AMENDMENT-U1:** instruments = top 25 by 30d USD volume (family-wide) — DIRECTION: NEUTRAL
- **AMENDMENT-A2:** full arm/option set mandatory (HMM; D1 primary; M15; SMA50; ZZ mag/vol) — DIRECTION: NEUTRAL
- **Family:** `CF-VOLDIR-001` (`REGISTERED`)
- **Container:** `SPDR-012` (vol) → `SPDR-013` (direction) → mid-checkpoint reflection →
  `SPDR-014` (combination) → conditional `XENA-VOLDIR-001`
- **Authority:** checkpoint opening and family registration approved; **no** SPDR execution,
  outcome read, combination freeze, XENA, TEST, or holdout approved by this open alone
- **Governing RAW brief (substance precedence):**  
  `.ignore/what-next/alts/vol-direction-structural-programme-raw.md`  
  This design **translates** that brief 1-to-1; it does not replace or thin it.

## Why this checkpoint exists

SPDR-011 / `CF-VOLCONV-001` locked vol + **late confirmed range-break** direction into one object and
failed L1 economics. Diagnosis: vol usability and direction were **assumed**, not independently
validated; confirmation arrives after availability is cut. This checkpoint **separates claims** and
tests them in order so failure is diagnosable (vol / direction / capture geometry / compatibility).

This is **not** `CF-VOLCONV-001` reopened. That family may still be retired at checkpoint-016
retrospective without blocking this programme.

---

## 1. Governing sources and precedence

1. `.ignore/what-next/alts/vol-direction-structural-programme-raw.md` — complete approved RAW brief
   (**substance must not change**).
2. `docs/references/chapter-06-governance.md` — live gate and permission boundary.
3. `docs/signal-registry/candidate-families/cf-voldir-001.md` — registered family contract.
4. `docs/references/spdr-lane.md` — SPDR integrity (TRAIN-only, disposition-only, matched controls).
5. This checkpoint — sequence, IDs, ownership, stop conditions, frozen defaults.

Chapter-05 no-spread cost amendment still governs money figures: spread unavailable/not charged;
partial-cost caveat mandatory.

On conflict: RAW substance > this design’s procedural freeze > per-SPDR design narrowings.
Per-SPDR designs may **narrow** arms and horizons; they may not reintroduce refused objects
(range-break primary direction, win-rate primary metric, TEST/holdout, unbounded zoos).

---

## 2. Programme basis — residue subset (from RAW §1)

The programme has not proven “no edge exists.” Thin but real residues keep reappearing while
small-capture vehicles die at capture/cost:

| Residue | What it is | Rough size / note | Status class |
|---|---|---|---|
| **HTF ±DI → LTF sign conditioning** | HTF directional pressure conditions LTF sign / dir-gap | ~1–4 bps short grain; **hold-scaling** | Real; sub-cost as previously scoped |
| **FX VR&lt;1** | Mean-reversion process property | Broad FX agreement | Real; prior harvest vehicle failed structure |
| **Gross bounce / reaction** | Real gross move structure | Multi-bps to tens of bps gross | Gross-real, net-dead as scoped |
| **Maker print / snap-back** | Limit→next-open mark | ~0.7–2 bps | MM product, not direction signal |
| **Secular / index drift** | One-sided time-in-market | Cost-surviving when left as drift | Named confound — not this programme’s target |
| **Outcome shape fingerprint** | Median+/mean-killed, tail-heavy | Recurring | Process observation |

**Cross-cutting:** Mode **B/C** dominant (substrate real; capture/cost or vehicle kills it), not pure
availability≈random. Pure absence mostly directional geometry and tick-volume proxies. Unpulled
levers: **capture (hold × move size)**, honest magnitude endpoints, structure redesign on proven
substrates — not another late-confirmation pattern.

**Narrow premise of this family:** among residues, **volatility/magnitude structure** is the
ingredient to build on; the open problem is extracting **directional, direction-aware, or
direction-agnostic** value without assuming a late confirmation device.

---

## 3. Core premise (RAW §2 — binding)

1. Volatility is comparatively reliable as a market object (clustering, persistence, regime). That
   claim must be **measured**, not taken on faith.
2. Direction is hard. “Safe confirmation” (e.g. completed breakout) is often **too late**.
3. **Separate** vol modelling from direction modelling; quantify each on its own metric stack;
   only then combine.
4. If combination fails after both look adequate in isolation → **capture geometry** and/or
   **compatibility / regime alignment** (predictable vol and direction do not co-occur enough) —
   not “markets empty.”
5. If compatibility fails, **direction-agnostic extraction** (grid-like / both-side / straddle-class)
   is a permitted last structural branch **only if** risk can be managed and only after vol (and
   optionally ZigZag magnitude/volatility) characterisation supports it.

---

## 4. Fixed question (programme)

> Can we **procedurally solidify** (A) how reliably volatility is predicted/modelled on the retained
> catalog, then (B) whether simple fast direction models have positive **expectancy in bps** under
> availability-when-right / damage-when-wrong scoring, then — only if justified — (D) extract value
> from combination or authorised direction-agnostic structure, with failure diagnosed as geometry or
> compatibility rather than vague absence?

```text
MECHANISM:
  Ordered claim separation. A: standardised vol predictability/reliability.
  B: fast direction (SMA benchmark; ZigZag ATR + path-local features) scored by expectancy bps,
     not win-rate; TF capture geometry (cut losers, let winners run).
  C: operator reflection freezes combination design from observations.
  D: vol×direction or authorised direction-agnostic extraction under partial-cost disclosure.
  E: XENA only if D graduates a cost-surviving base.
DERIVED:
  estimands=step-specific (see §7)
  null=time/label shuffles; matched non-signal timing; SMA as direction baseline
  horizon=intraday-relevant, frozen per SPDR design (no multi-day drift product)
  test=reliability (A); expectancy bps (B); combination + diagnosis (D)
```

```text
OBJECT-IDENTITY (per step — binding intent):
  A: measurement object = next-horizon vol / |move| / regime state; not a P&L claim
  B: measurement object = signed policy under declared capture geometry; expectancy bps
     == trading-relevant unit of the screen (not classification accuracy)
  D: measurement object == extraction object frozen at C; no silent object switch
```

---

## 5. Procedural claim order (RAW §3 — binding sequence)

### Step A — Volatility characterisation (must pass before vol-conditioned combination)

**Goal:** Evaluate/quantify how reliably volatility can be predicted or modelled.

- Standardise definitions (raw level vs regime; horizon; instrument class; lag/causality).
- Quantify reliability with **predeclared** metrics (not “looks clustered”).
- **Stop** the vol-conditioned combination branch if reliability bars fail.

No direction model, no combination, no tradability claim at this step.

**Vehicle:** `SPDR-012`.

### Step B — Direction method + expectancy (not win-rate)

**Goal:** Define a small frozen set of direction models and score them correctly.

**Forbidden primary metric:** win-rate / “right X of Y times.”

| When model is… | Measure |
|---|---|
| **Right** | How much is available / captured when correct (**availability when right**) |
| **Wrong** | How adverse when incorrect (**damage when wrong**) |
| **Overall** | Simple **expectancy in bps** of the registered unit |

No combination with vol until this object is honest and predeclared.

**Vehicle:** `SPDR-013`. Default sequence is **A then B** (sequential).

### Step C — Mid-checkpoint reflection (design gate, not a silent skip)

After A and B:

- Decide whether combination is justified.
- Choose combination design(s) from **observations**, not a pre-hoped narrative.
- If A or B failed bars: **stop** or branch explicitly (e.g. direction-agnostic only if vol supports).
- If both pass: freeze combination hypothesis for Step D.

Operator-facing written options + recorded decision. Artifact:
`checkpoints/2026-07-23-017-structural-vol-direction-programme/reflection-mid.md`
(created when C runs — not at open).

### Step D — Combination / extraction test

Only then:

- Extract tradable insight from **vol × direction** (or vol × direction-agnostic structure).
- If fails while A and B adequate → classify **capture geometry** and/or
  **compatibility/regime alignment**.
- Direction-agnostic (grid-like / both-side / straddle-class) = **conditional** branch for
  incompatibility, not free default.

**Vehicle:** `SPDR-014`.

### Step E — XENA (conditional)

If D produces a **cost-surviving base** that survives SPDR integrity + money-floor discipline,
`XENA-VOLDIR-001` may select among candidates / portfolio structure.  
XENA is **not** Steps A–C. Conditioning-only theses without a base do not belong on a
cadence-rewarding portfolio objective.

---

## 6. Vehicle and experiment shape (RAW §4)

| Stage | ID | Vehicle | Notes |
|---|---|---|---|
| A | `SPDR-012` | SPDR TRAIN-only screen | Vol characterisation; lean QA; 0 TEST reads |
| B | `SPDR-013` | SPDR TRAIN-only screen | Direction expectancy; lean QA; 0 TEST reads |
| C | *(none)* | Mid-checkpoint reflection | Not an emission experiment |
| D | `SPDR-014` | SPDR TRAIN-only screen | Combination / extraction; lean QA; 0 TEST reads |
| E | `XENA-VOLDIR-001` | XENA (conditional) | Separate design/QA/authority after D graduates |

SPDR integrity boundary (hard): TRAIN-only fence; causal `t-1` lag; no tradability/deployability
claim; matched-control + seed battery where random controls apply; per-stratum reporting;
no local accounting primitives for verdict P&L; dependence-matched uncertainty.

---

## 7. Research items and sequence

| Order | Item | Purpose | Start gate | Status |
|---:|---|---|---|---|
| 1 | Family + checkpoint open | Register `CF-VOLDIR-001`; freeze sequence | Operator accept RAW brief | **COMPLETE 2026-07-23** |
| 2 | `SPDR-012` design | Freeze vol definitions, arms, reliability bars, universe, horizons | Checkpoint open | **COMPLETE 2026-07-23** |
| 3 | `SPDR-012` run + analysis | Vol reliability characterisation | SPDR-012 design + lean self-check | unauthorised — awaiting operator execution |
| 4 | Operator gate A | PASS / STOP combination path | SPDR-012 analysis | unauthorised |
| 5 | `SPDR-013` design | Freeze SMA/ZigZag params, capture geometry, expectancy unit | Prefer A PASS; operator may allow B after A data even if STOP combo | **COMPLETE 2026-07-23** |
| 6 | `SPDR-013` run + analysis | Direction expectancy bps | SPDR-013 design + gate | unauthorised |
| 7 | Operator gate B | Expectancy adequacy | SPDR-013 analysis | unauthorised |
| 8 | Mid reflection C | Freeze combination or stop/branch | A+B complete | unauthorised |
| 9 | `SPDR-014` design | Freeze extraction object from C | Reflection signed | unauthorised |
| 10 | `SPDR-014` run + analysis | Combination / extraction + diagnosis | SPDR-014 design | unauthorised |
| 11 | Operator gate D | Graduate base / terminal diagnosis | SPDR-014 analysis | unauthorised |
| 12 | `XENA-VOLDIR-001` | Portfolio/search on graduated bases | D graduates + separate design/QA/approval | **RESERVED** |

No historical TEST. No holdout. No automatic family verdict.

---

## 8. Models in scope (RAW §5 — full toolkit preserved)

### 8.1 Volatility (SPDR-012) — academic methods permitted

Volatility is itself academic; standard methods are **in-bounds** if causal, TRAIN-fenced,
predeclared.

**Organising axes (all retained; SPDR-012 design freezes concrete first-pass arms covering these
axes — it may stage secondary arms but must not drop an axis from the programme without operator
amendment):**

| Axis | Examples | Target object |
|---|---|---|
| **Persistence / clustering** | Autocorr of \|r\|, RV, squared returns; half-life; HAR-style multi-horizon lags | “Does prior vol predict next?” |
| **Level forecasting** | OLS/ridge on lagged RV; HAR-RV; EWMA/RiskMetrics-style | Continuous next-horizon RV / absolute move |
| **Regime models** | 2–3 state Markov; Hidden Markov (HMM) on returns or RV | State labels + transition matrix + OOS state persistence |
| **Realised vs range-style** | Close-to-close RV; Parkinson; Garman–Klass; realised range | Robust magnitude under OHLC limits |
| **Calendar / clock effects** | UTC session, day-of-week, event-free baselines | Structured seasonality vs pure AR residual |
| **Cross-sectional rank** | Relative vol percentile across liquid set | Relative HIGH/LOW state |
| **Distributional / tail** | Conditional quantiles of \|move\|; exceedance rates in HIGH state | Not only mean RV |

**Reliability metrics (all retained; numeric floors freeze in SPDR-012 design):**

- Out-of-sample R² / rank-IC / MAE on next-horizon RV or \|move\|  
- Regime hit-rate **only secondary**; primary for regimes = **state-conditional magnitude
  separation** with CIs  
- Stability across time thirds and symbols  
- Collapse under time-shuffle / label-shuffle controls  
- Minimum useful horizon where predictability clears noise  

**Stop rule:** if no predeclared reliability bar is met → do not open Step D vol-conditioned
extraction (RAW §5.1).

**SPDR-012 first-pass arm freeze (all mandatory; AMENDMENT-A2):**

| Arm ID | Axis coverage | Spec sketch (detail in SPDR-012 design.md) |
|---|---|---|
| V-PERSIST | Persistence / clustering | Lagged RV / \|r\| autocorr; half-life; multi-horizon HAR lags |
| V-LEVEL | Level forecasting | Causal EWMA + OLS/ridge on lagged RV → next-horizon RV and \|move\| |
| V-REGIME | Regime | 2-state Markov on RV |
| V-REGIME-HMM | Regime | 2-state HMM — **mandatory first-pass** |
| V-MEASURE | Realised measures | Close-to-close primary; Parkinson and Garman–Klass co-reported |
| V-CLOCK | Calendar / clock | Session / DOW effects as residual after V-LEVEL (not standalone edge claim) |
| V-XS | Cross-sectional rank | Relative vol percentile across top-25 universe (same-timestamp) |
| V-TAIL | Distributional / tail | Conditional quantiles / HIGH-state exceedance co-reported with means |

**Clocks:** H1, H4, **D1** — all three **primary** (full arm suite each).

### 8.2 Direction (SPDR-013) — intentionally simple and fast

**Not** conventional late-confirmation systems. Preference: simple, naive or intentionally dumb,
but fast. **Cut losers quickly; let winners run** (classic trend-following). Capture geometry is
part of the model, not an afterthought.

#### Benchmark — mid-term SMA

- Periods: **14, 25, and 50** — all mandatory (intraday-relevant).  
- **Not 200-SMA** (too long / over-smoothed for intraday).  
- Rule sketch: buy above, sell below.  
- **Angle filter ON and OFF** both mandatory.  
- **Clocks H1 and M15** both mandatory.  
- **Benchmark** that other arms must beat on **expectancy bps**, not win-rate.

#### Proposed — ZigZag ATR-based (deterministic structure)

**Native property:** alternating swing lines. Once a bullish line is confirmed under the
deterministic rule, the next structural alternative is bearish (and vice versa). Direction of the
*next structural leg* is partly given by construction.

**Known weaknesses of plain ZigZag:**

- Fragile to fake confirmations  
- Still misses a large fraction of the **beginning** of moves (confirmation lag, milder than
  multi-hour range-break but real)

**Proposed improved feature set per completed line:**

| Feature | Meaning |
|---|---|
| **Magnitude** | Size of the completed swing |
| **Binary direction** | Up / down of that line |
| **Angle / slope** | Steepness of the line |
| **Noise / volatility around the line** | Clean (price hugs the line) vs volatile (larger whipsaw around it) |

Noise is **relative to the price path that defines the line**, not an arbitrary detached window —
path-local volatility in relation to the structure.

**Uses:**

- Features → AR or light ML to **predict magnitude and/or volatility of the next whole move**
  (move-level aggregation, not only per-bar)  
- Supports **direction-agnostic** extraction even when pure sign skill is weak  
- Direction expectancy still scored with availability-when-right / damage-when-wrong / bps
  expectancy when a signed policy is defined  

**SPDR-013 first-pass arm freeze:**

| Arm ID | Spec |
|---|---|
| D-SMA | Periods **14, 25, 50** all mandatory; angle **on+off** both mandatory; clocks **H1+M15** both mandatory |
| D-ZZ | ATR ZigZag on **H1+M15**; line features; signed next-leg; **mandatory** mag **and** vol next-move heads (AR+ridge) |

**Not in first-pass direction set:** HTF-DI (may be named benchmark only if reflection C
predeclares it). **Not primary:** SPDR-011 daily-range breakout.

---

## 9. Frozen data scope (defaults)

| Item | Decision |
|---|---|
| Catalog | Bybit USDT linear perps; INFR-011 fence |
| Universe | **Top 25 by 30d USD volume** (TRAIN-only rank); pin `cf-voldir-001-universe.json` |
| Ranking rule | `sum(close×volume)` on 1m bars over `[train_end−30d, train_end)`; assert at run |
| Coverage | Sparse DESIGN history → UNPOWERED cells, not silent drop |
| TRAIN | All screens; code-asserted fence |
| DESIGN window (default) | Prefer DESIGN-eligible TRAIN slice aligned to fence; exact dates freeze in each SPDR design |
| CONFIRM | Only if a later frozen rule requires it; not default for A/B characterisation |
| Historical TEST | **Never** |
| Global holdout | **Never** |
| Costs | Fees + discrete funding (+ allowance if used); **spread null / not charged**; partial-cost caveat |
| Execution default for expectancy screens | Open-to-open / next-boundary real marks as frozen per SPDR; no maker-as-free-edge assumption |

---

## 10. What this programme refuses (RAW §6)

- Re-running SPDR-011’s **confirmed daily-range breakout** as the primary direction device without
  new evidence  
- Treating **win-rate** as the direction success metric  
- Jumping to combination or XENA before A and B are quantified  
- Expanding into indicator zoos / unbounded ML search without frozen arms  
- Historical TEST or holdout use for this exploratory path  
- Calling any SPDR result deployable or fully cost-complete under no-spread rules without the
  partial-cost caveat  

---

## 11. Intended checkpoint end-states (RAW §7)

Exactly one of:

1. **Terminal structural package:** vol not reliable enough; and/or direction expectancy ≤ 0 under
   honest damage accounting; and/or combination fails with clear diagnosis (geometry vs
   compatibility). Retrospective records operator family disposition.
2. **Graduated base for XENA / further Nautilus:** combination (or authorised direction-agnostic
   extraction) shows TRAIN availability and expectancy that clear predeclared floors under
   partial-cost disclosure — only then portfolio/search stages.

---

## 12. Family identity (RAW §8)

- **Not** `CF-VOLCONV-001` with a new breakout.  
- **Is** new structural programme: vol reliability → direction expectancy → combination/compatibility
  → optional XENA.  
- `CF-VOLCONV-001` retirement (if any) is a separate checkpoint-016 retrospective act.

---

## 13. Operator compressed intent (RAW §9 — preserved)

> Solidify claims procedurally. First characterise volatility properly and standardised — how
> reliably it can be predicted/modelled; stop if not reliable enough. Next define the direction
> method; score not by win-rate but by how right we are when right (availability), how adverse when
> wrong, and expectancy in bps. Only then combine. Failure at combination after good A/B means
> capture geometry or compatibility/regime misalignment — then maybe direction-agnostic extraction
> if risk is manageable. Vol models: clustering, Markov/HMM regimes, regression on raw levels, plus
> standard vol toolkit. Direction: fast/simple — SMA benchmark (14/25/50, angle filter); ZigZag ATR
> with line features (magnitude, direction, angle, path-local noise) for next-move magnitude and/or
> volatility and possible direction-agnostic use. Checkpoint path: SPDR vol, SPDR direction, mid
> reflection, SPDR combination, then XENA if pass.

---

## 14. Pointers (RAW §10 + formal IDs)

| Resource | Role |
|---|---|
| `.ignore/what-next/alts/vol-direction-structural-programme-raw.md` | RAW source of truth |
| `.ignore/what-next/alts/intraday-way-forward-plan.md` | Prior CF-VOLCONV brief (closed path; do not merge) |
| `.ignore/what-next/reflections/2026-07-14-CONSOLIDATED-verdict-and-direction.md` | Residue set / failure modes / capture lessons |
| `python/experiments/SPDR-011/report.md` | Why late breakout conversion failed economically |
| `docs/references/spdr-lane.md` | SPDR vehicle integrity boundary |
| `docs/signal-registry/candidate-families/cf-voldir-001.md` | Family contract |
| `docs/references/chapter-06-governance.md` | Live gate |
| This file | Checkpoint sequence and freezes |

---

## 15. Registration and ID assignment (executed)

| Object | ID |
|---|---|
| Family | `CF-VOLDIR-001` |
| Checkpoint | `2026-07-23-017-structural-vol-direction-programme` |
| Vol SPDR | `SPDR-012` |
| Direction SPDR | `SPDR-013` |
| Combination SPDR | `SPDR-014` |
| Conditional XENA | `XENA-VOLDIR-001` |

**Next authorised work:** write `python/experiments/SPDR-012/design.md` (vol characterisation freeze).
No execution until that design exists and operator authorises the SPDR run under lane rules.
