# SPDR-012 — Volatility characterisation (reliability)

- **Family:** `CF-VOLDIR-001` · **Checkpoint:** 017 · **Lane:** SPDR (TRAIN-only)
- **Status:** `DESIGN COMPLETE — AWAITING OPERATOR EXECUTION AUTHORITY`
- **Hypothesis:** `CF-VOLDIR-001/HYP-A`
- **Governing:** RAW brief §3A/§5.1; checkpoint-017 §5A/§8.1; `chapter-06-governance.md`; `spdr-lane.md`
- **Produces:** standardised vol objects + reliability metrics per arm/stratum + operator PASS/STOP
  recommendation for the **vol-conditioned combination path** (not a family verdict)
- **Must not produce:** tradability/deployability claim; combination design; direction model; TEST/holdout
  contact; local P&L accounting as a verdict

A SPDR result is never a tradability claim. **0 counted reads, 0 slots.**

---

## §0 Scope fence

| | |
|---|---|
| **Vehicle** | Vectorised Python on fenced catalog 1m → aggregated clocks (SPDR lane). No Nautilus; no `estimand_validation` gate |
| **Band** | **DESIGN** `[2021-06-29T06:53Z, 2023-03-01T00:00Z)` = primary estimation + chronological thirds. **CONFIRM** `[2023-03-01T00:00Z, 2023-12-18T00:00Z)` = one TRAIN-internal reliability verification read (labelled **not** programme TEST). **TEST** `≥2023-12-18` never. **Holdout** `≥2025-01-08` never |
| **Symbols** | **Top 25 by 30d USD volume** — family pin `cf-voldir-001-universe.json` / `results/universe_top25.json` (AMENDMENT-U1) |
| **Clocks (frozen)** | **H1**, **H4**, and **D1** — all three are **primary** decision clocks (full arm suite on each) |
| **Warm-up** | Need ≥ max(60 D1 bars, 60 H4 bars, 120 H1 bars) of complete history before first scored forecast |
| **Complexity** | 8 arms (V-* incl. V-REGIME-HMM) × 3 clocks (H1/H4/D1); no post-outcome arm invention |

### Applicability of standard design blocks

| Block | Status |
|---|---|
| Nautilus / `xen.adjudication` / estimand gate | **N/A — SPDR lane** (integrity = fence + causal lag self-check §7) |
| SPREAD-COST-DISCLOSURE | **APPLIES** whenever any bps money unit is shown (§6) |
| Battery / derangement | **APPLIES** — label/time shuffles §5 |
| Future-destroy tripwire | **REPORT LAYER** per **AMENDMENT-T1 (2026-07-23)** — was a hard tripwire; no outcome-side destroy can detect look-ahead. Hard causality now rests on §7 (incl. new §7.3b). Both destroy forms still run and are reported (§5) |

```
SPREAD-COST-DISCLOSURE:
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: any optional cost overlay understates true cost; no fully-net/tradable/deployable claim
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

This screen’s **primary objects are forecast reliability**, not P&L. Money units appear only as
optional conversion of |move| into bps for readability (unit pin §6).

---

## §1 Mechanism + question

**One question:** On the retained Bybit core, is **next-horizon volatility / absolute move**
predictable from causal lagged information well enough — under predeclared metrics — to justify
later vol-conditioned extraction (SPDR-014), or must that combination path stop?

```
MECHANISM: Volatility clusters and persists across adjacent bars/sessions. Lagged realised
volatility, multi-horizon HAR structure, and discrete high/low regimes forecast the *magnitude*
of near-future absolute open-to-open movement (and next-horizon RV), not its sign. The
characterisation object is a one-step-ahead forecast of magnitude/RV/regime state at fixed
clocks (H1, H4, D1 — all primary). No directional P&L is claimed here.

DERIVED:
  estimand = one-step-ahead RV and |open→open move| at horizon h ∈ {H1,H4}; regime state labels
             with state-conditional |move| separation; cross-sectional relative vol rank
  null     = (i) time-shuffled predictor paths (preserve marginals, break lag); (ii) label
             derangement of targets within calendar blocks; (iii) constant/unconditional mean
             forecast baseline
  horizon  = next completed H1, H4, and D1 bars (all primary clocks)
  test     = rank-IC / OOS R² / MAE vs baselines; regime HIGH−LOW |move| gap with date-block CIs;
             shuffle collapse fractions; time-third stability
```

**Anti-L-13:** estimands and nulls are forecast-skill objects native to vol characterisation; they
are not SPDR-011 partial-net episode machinery and not a directional referee stack.

---

## §2 Object identity

```
OBJECT-IDENTITY:
  measurement object == trading object: N/A for primary screen — no trade is executed.
    Measurement object = next-horizon RV / |move| / regime state. Explicitly not a booked P&L object.
  measured conditioning event == traded entry event: N/A — no entry. Conditioning uses only
    information known at forecast origin t (≤ last completed bar at t).
  effect-splitting windows non-overlapping: YES — forecast origin t uses data ≤ t; target is
    strictly the next clock bar (t, t+h]; no overlapping claim of the same bar as both feature and
    target for the same forecast.
```

---

## §3 Frozen definitions

### 3.1 Aggregation

From fenced 1m bars (`ts_event` = bar close):

- `open_ts = ts_event − 1m`
- Clock bars: group by `open_ts.truncate(clock)` for `clock ∈ {1h, 4h, 1d}`
- Complete bar only if last print equals `slot_end` and minute coverage ≥ 80% of expected minutes
  (H1≥48, H4≥192, D1≥1000) — incomplete bars **counted, excluded from forecasts**

### 3.2 Returns and realised measures (per clock)

On completed bar `i` with OHLC:

| Symbol | Definition |
|---|---|
| `r_i` | `log(C_i / C_{i-1})` |
| `rv_cc_i` | `r_i²` (close-to-close squared; single-bar) |
| `rv20_i` | `sqrt(mean(r_{i-19}² … r_i²))` over 20 completed returns (needs i≥20) |
| `parkinson_i` | `sqrt( (1/(4 ln 2)) * (ln(H_i/L_i))² )` |
| `gk_i` | Garman–Klass variance → sqrt (standard formula); 0 if invalid OHLC |
| `abs_oo_i` | `1e4 * |O_{i+1}/O_i − 1|` bps open-to-open of the **next** bar (target for bar i forecast) |
| `rv_next_i` | `rv20` measured at end of bar i+1 (target alternative) |

**Lag rule:** any feature used to forecast targets for origin i may use bars `≤ i` only.
`abs_oo_i` and `rv_next_i` use bar i+1 and are **targets only**.

### 3.3 Forecast origins

For each symbol × clock × complete bar i with warm-up satisfied:

- Origin timestamp = `slot_end_i` (state known)
- Target = next bar’s `abs_oo` and/or next `rv20` as arm-specified
- Drop terminal bar (no next bar inside band)

---

## §4 Arms (first-pass freeze — all axes covered)

| Arm | Axis | Forecast / object | Primary metric |
|---|---|---|---|
| **V-PERSIST** | Clustering | Autocorr of `\|r\|` and `rv20` at lags 1,2,3,5; half-life of `\|r\|` AR(1); HAR-style regressors `rv20`, `rv20_mean_6`, `rv20_mean_24` (clock bars) → next `abs_oo` | lag-1 Spearman IC; HAR OOS R² |
| **V-LEVEL** | Level forecast | **EWMA** σ² with λ=0.94 on `r²` (causal); **OLS** and **ridge** (α=1.0) of next `abs_oo` and next `rv20` on `{rv20, ewma_vol, parkinson, gk}` lagged | OOS rank-IC + MAE vs unconditional mean |
| **V-REGIME** | Regime | 2-state Markov on `rv20` (discretise by rolling median split for emission of states) | HIGH vs LOW mean `abs_oo` gap; CI; transition persistence |
| **V-REGIME-HMM** | Regime (HMM) | **First-pass mandatory:** 2-state Gaussian HMM (Baum–Welch / equivalent causal fit on expanding window) on `r` or `rv20` sequence; decoded state at t from data ≤ t only | same gap metrics as V-REGIME; state persistence; compare to Markov |
| **V-MEASURE** | Realised | Co-report `rv20` (cc), Parkinson, GK as alternative magnitude inputs into V-LEVEL; pairwise rank corr of measures | which measure best predicts next `abs_oo` (IC) |
| **V-CLOCK** | Calendar | Session bucket (UTC 0–8 / 8–16 / 16–24) and DOW dummies; residual `abs_oo` after V-LEVEL fitted mean | incremental R² after V-LEVEL (not a standalone edge claim) |
| **V-XS** | Cross-section | Same-timestamp rank of `rv20` across **all available** universe symbols at that stamp (lexical tie-break); terciles | next `abs_oo` by own tercile; top−bottom gap |
| **V-TAIL** | Tail | Empirical P90/P95 of `abs_oo` conditional on V-REGIME HIGH vs LOW; exceedance rates | HIGH exceedance − LOW exceedance |

**Multiplicity (disclosed):** 8 arms × **3** primary clocks (H1/H4/D1) × ≤25 symbols ≈ 600 primary cells.
Pooled = disclosure-only. No arm promoted solely by a single best cell.

**AMENDMENT-A2 (2026-07-23):** V-REGIME-HMM mandatory first-pass; D1 elevated from disclosure-only
to full primary clock — DIRECTION: **NEUTRAL** (pre-execution completeness; higher compute).

### §0.1 Universe pin (family-wide AMENDMENT-U1)

```
UNIVERSE-PIN:
  metric: sum(close * volume) on fenced 1m bars
  window: [2023-11-18T00:00:00Z, 2023-12-18T00:00:00Z)   # train_end − 30d → train_end
  band: TRAIN
  n: 25
  symbols: BTCUSDT, ETHUSDT, SOLUSDT, AVAXUSDT, ORDIUSDT, 1000BONKUSDT, TIAUSDT,
           DOGEUSDT, XRPUSDT, LINKUSDT, ADAUSDT, BIGTIMEUSDT, BLURUSDT, 1000PEPEUSDT,
           1000LUNCUSDT, MATICUSDT, INJUSDT, SEIUSDT, BNBUSDT, WLDUSDT, PYTHUSDT,
           DYDXUSDT, GALAUSDT, OPUSDT, 1000RATSUSDT
  pin files: results/universe_top25.json ;
             docs/signal-registry/candidate-families/cf-voldir-001-universe.json
  code assert: recompute ranking; fail if symbol set ≠ pin
  coverage: symbols with short DESIGN history stay listed; low-n cells → UNPOWERED
```

**AMENDMENT-U1:** five-name core → top-25 volume universe — DIRECTION: **NEUTRAL** (pre-execution).

---

## §5 Controls and tripwire

```
CONTROL TIME-SHUFFLE-PREDICTORS:
  question answered: is lag structure necessary for reported IC/R²?
  population: within-symbol circular shift of feature rows by U{1..n-1} bars; targets fixed
  DISJOINT: features no longer aligned to true past of the target
  bite/MDE: plant +0.25 rank correlation via synthetic monotone feature; shuffle must destroy plant
  non-vacuity: moves lag-alignment sufficient statistic of IC
  expected if H true: live IC >> shuffled IC distribution; if false: live inside shuffle envelope
  disclosure: collapse = shuffled_IC / live_IC; ≥200 seeds (101..300)
  destroy form: CIRCULAR_SHIFT (not a fixed-point-prone label perm on the same index)
```

```
CONTROL TARGET-LABEL-DERANGEMENT:
  question answered: is reported skill an artifact of target marginals only?
  population: derange next abs_oo within (symbol × calendar-month) blocks; features fixed
  DISJOINT: zero fixed points (L-28)
  bite/MDE: same +0.25 plant must fall inside null after derangement
  non-vacuity: destroys feature→target pairing
  expected if H true: live IC above null p95; if false: centred
  disclosure: one-sided p, collapse fraction; seeds 31000..31199 (≥200; full 2000 if runtime allows —
    SPDR minimum 200 with disclosed seed range; upgrade to 2000 if wall-clock < 30 min)
  destroy form: DERANGEMENT
```

```
CONTROL UNCONDITIONAL-MEAN-BASELINE:
  question answered: does the model beat a constant forecast?
  population: train-mean abs_oo / rv20 as forecast
  DISJOINT: N/A (nested baseline)
  bite/MDE: MAE reduction and IC vs zero
  non-vacuity: nested comparison
  expected if H true: model MAE < baseline MAE with CI on paired difference excluding 0
  disclosure: ΔMAE, ΔR²
```

```
TRIPWIRE: TARGET-FUTURE-DESTROY
  metric: V-LEVEL rank-IC on next abs_oo
  must collapse: replace each target with another symbol-month deranged target (same as label
    derangement); live IC must not remain above null p99 if the metric is acausal
  vacuity check: destroys only future labels, not causal features
  if permutation-based: derangement=YES
  class: future_destroy (HARD for validity of the *forecast claim*; surviving IC ⇒ leak/bug)
```

### AMENDMENT-T1 (2026-07-23) — TARGET-FUTURE-DESTROY becomes a report layer

**DIRECTION: LOOSER** (a hard gate is removed). **Operator sign-off: RECORDED 2026-07-23.**
Raised by fresh-context QA run 1 (`qa-review.md` F-1/F-2/F-3); made **after** first-run
outcomes were seen — disclosed as such.

**Why.** The clause as frozen cannot do the job it names, in two independent ways.

1. *The pinned destroy form cannot be adjudicated for collapse.* Deranging targets **inside
   symbol × calendar-month blocks** leaves the between-month component of the association
   intact by construction, so that null is not centred at zero and its median **rises with
   the strength of the true relationship** (measured: block null median 0.109 against a live
   0.259). Adjudicating collapse on it failed 33 of 90 cells — including the strongest ones.
2. *No outcome-side destroy can detect look-ahead at all.* `E[Spearman(pred, deranged y)] = 0`
   for **any** fixed predictor, leaking or not. Re-specifying the check onto a full
   unrestricted derangement makes it pass everywhere (null median −0.0002, max |median|
   0.005 across 90 cells) — a green gate carrying no information, which is exactly the
   absence-of-evidence-as-evidence-of-absence failure L-32 was written about.

**What changes.** `TARGET-FUTURE-DESTROY` is reported as a **report layer** — `observed` /
`ideal` / `interpretation`, **no `pass` field** (INFR-016, L-32). Both destroy forms are still
run at 2000 seeds and reported per cell: the unrestricted form as the collapse reference, the
design's pinned block form as the §5 CONTROL it declares itself to be
("is reported skill an artifact of target marginals only?"), read in the design's own stated
direction (live IC above null p95).

**What carries the no-leak claim instead.** The construction-level causality asserts, which
stay **HARD**: §7.1/§7.1b/§7.2 (band fence), §7.3 + **§7.3b** (CONFIRM never enters an
estimated coefficient, and a DESIGN target's exit price never comes from CONFIRM), §7.4
(features ≤ origin, target strictly the next bar), §7.5 (derangements fixed-point-free,
**measured** not asserted). The **predictor-side** `TIME-SHUFFLE-PREDICTORS` circular shift is
the operative non-vacuity device. An independent fresh-context QA pass re-derived the
walk-forward path from scratch (max abs difference 0.0 over 608 OOS rows; a deliberately leaky
variant differs by 20.4 bps) and confirmed the causality construction.

**Consequence, stated plainly:** SPDR-012 ships with **no hard leak gate**. Any downstream
reader must treat the L-01 (look-ahead) assurance as resting on the construction asserts and
the independent code review, not on a destroy test.

### AMENDMENT-T2 (2026-07-23) — §6.4 recommendation is not computed

**DIRECTION: NEUTRAL** (no threshold moves). **Operator sign-off: RECORDED 2026-07-23.**
Raised by QA run 1 finding F-4.

§6.4's PASS clauses are unsatisfiable as frozen: the DESIGN band mostly predates the catalog's
trailing 4-year history cap, leaving ~100 unique dates per cell against the ~225 that §6.3's
own UNPOWERED rule requires, and the first literal calendar third is empty for every symbol
but MATICUSDT. Rather than silently reading the recommendation off the CONFIRM band or off a
disclosure label variant, `analysis.md` reports **all three candidate bases side by side**
(CONFIRM + design labels; DESIGN + design labels; DESIGN + disclosure labels) with what each
would imply, and **declines a PASS/STOP call**. The call is the operator's at the gate.

---

## §6 Units, inference, bands, power

### 6.1 Unit pin

```
UNIT-PIN:
  primary magnitude target: abs_oo = 1e4 * |O_{t+1}/O_t − 1| in bps on the decision clock
  RV objects: dimensionless (log-return scale) or annualised only if explicitly labelled
  normaliser for optional money overlay: none required for reliability PASS; if shown,
    "H-clock open-to-open bps" is already in bps — no ATR divisor
```

### 6.2 Inference

- Per-symbol before pooled; pooled disclosure-only.
- Date-block bootstrap on unique UTC dates (block lengths 1/3/7); seeds `101,211,307,401,503`;
  5k–10k resamples (10k preferred).
- OOS protocol: expanding window, first 40% DESIGN for initial fit, walk-forward re-fit each
  calendar month; report OOS only for V-LEVEL / V-PERSIST regression arms.
- Chronological DESIGN thirds (equal elapsed time on `[DESIGN start, DESIGN end)`).

### 6.3 Interpretation bands (labels, not gates — operator judges PASS)

```
BANDS (per symbol × clock, V-LEVEL primary):
  SUPPORTED:   OOS Spearman IC ≥ 0.10 and date-block 95% CI low > 0
  WASH:        |IC| < 0.05 or CI contains 0 with |IC| < 0.10
  CONTRADICTED: IC ≤ −0.05 and CI high < 0
  UNPOWERED:   effective unique dates < 40 or MDE(IC) > 0.10
BANDS (V-REGIME magnitude gap HIGH−LOW abs_oo bps):
  SUPPORTED:   gap ≥ +15 bps and CI low > 0
  WASH:        |gap| < 10 bps
  CONTRADICTED: gap ≤ −15 and CI high < 0
  UNPOWERED:   MDE > 15 bps or dates < 40
POOLED: disclosure-only unless cross-symbol sign agreement ≥ 60% of powered symbols on primary clock.
```

### 6.4 Operator combination-path recommendation (informative stop rule)

Recommend **PASS** vol-conditioned path only if **both**:

1. V-LEVEL **SUPPORTED** on ≥1 primary clock for **≥10 of 25** symbols (or ≥40% of symbols with
   powered cells if fewer than 25 are powered), **or** pooled H4 SUPPORTED with ≥60% of powered
   symbols showing positive IC; **and**
2. Target-label derangement / time-shuffle: live IC not inside null central 90% (collapse
   demonstrates dependence on true alignment); **and**
3. Time-third: IC sign stable in ≥2/3 DESIGN thirds on the winning clock (on the pooled or
   majority-symbol read).

Else recommend **STOP** vol-conditioned SPDR-014 path (SPDR-013 may still run for pure direction
science per checkpoint).

### 6.5 Power (prospective)

```
POWER:
  expected DESIGN H4 bars/symbol ~ 2.5y * 365 * 6 ≈ 5000+ complete; after warm-up ~4800
  expected unique dates ~ 500+
  MDE for Spearman IC (rough): ~ 1.5/sqrt(n_eff); n_eff≈dates → MDE ~0.07 at 500 dates
  strata predeclared UNPOWERED risk: single-symbol H1 short sub-windows; D1-only cells if
    sparse incomplete days — label UNPOWERED, never negative
```

---

## §7 Integrity checklist (code-asserted)

1. Every catalog query `band="TRAIN"`; assert max target timestamp < `train_end_utc`.  
2. Assert no row with `ts ≥ holdout_start_utc`.  
3. Assert CONFIRM not used in estimation coefficients (CONFIRM = verify only).  
   **3b (added by AMENDMENT-T1):** assert a DESIGN target's **exit** price is also inside
   DESIGN — the open-to-open target exits one bar after the target bar, which clause 3 (an
   origin-timestamp comparison) cannot see. QA F-7.
4. Assert feature timestamps ≤ origin; targets use next bar only.  
5. Assert derangements have 0 fixed points (or abort) — **measured** across the whole seed
   battery and reported as a count, not inferred from a literal (QA F-10).
6. Write `results/integrity_selfcheck.json` with all asserts PASS.

---

## §8 Golden traces (hand-checkable)

```
GOLDEN-TRACE:
  G1 BTCUSDT H4: first complete H4 bar after 2022-09-14 00:00Z with full rv20 history —
     recompute rv20 by hand from 20 prior H4 log closes; match screen to 1e-9 rel.
  G2 ETHUSDT H1: one V-LEVEL forecast origin — list feature vector {rv20, ewma, park, gk};
     confirm none use the target bar's open-to-open.
  G3 SOLUSDT: one time-shuffle seed 101 — fixed points N/A; verify IC changes vs live.
```

---

## §9 Deliverables

| Artifact | Content |
|---|---|
| `screen_code/` | Feature build, arms, controls, self-check |
| `results/vol_reliability.parquet` | per origin forecasts + features |
| `results/metrics_by_cell.parquet` | IC/R²/MAE/gaps per arm×symbol×clock |
| `results/controls.json` | shuffle/derangement envelopes |
| `screen.md` | neutral tables |
| `analysis.md` | fresh-context full-facet quantification + PASS/STOP recommendation |

---

## §10 Hard vs informative

```
HARD: holdout/TEST untouched; causal lag; tripwire (surviving IC after target destroy ⇒ invalid);
      integrity self-check.
INFORMATIVE: all IC/R²/gaps/bands; PASS/STOP combination-path recommendation (operator decides).
```

**No direction, no combination, no XENA in this item.**
