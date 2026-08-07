# Checkpoint 018 — Shape of the next experiment

- **Written:** 2026-08-05
- **Revised:** 2026-08-06 — current and complete; supersedes all earlier drafts of this file
- **Authority:** §0 *Operator directive register* (OD-1 … OD-24) is binding. Every other section
  elaborates it and may not contradict it.
- **Status:** `OPERATOR INTERPRETATION PRODUCT — NOT A DESIGN, NOT AUTHORISED`
- **Inputs:**
  - `python/experiments/SPDR-{021,022,023}/analysis.md` (TRAIN-only, amended rerun `20260803T140238Z`)
  - `docs/experiments-docs/checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/confirmation-extraction-021-023.md`
    (11-item ledger, artifact-traced, read across six cells = 3 experiments × 2 universes)
- **Standing:** records the operator's reading and signed-off decisions for a successor experiment.
  Issues no family verdict, ranks no arm, authorises no execution. A successor requires its own
  `quant-designer` design and a fresh-context QA gate.

```
SPREAD-COST-DISCLOSURE (carried unchanged into the successor by operator decision)
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: every money figure understates true cost; reported net is overstated
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

---

## 0. Operator directive register (BINDING — the authority for everything below)

Every directive the operator issued for this successor, 2026-08-05 → 2026-08-06. This table is the
authority; the prose that follows elaborates but never overrides it. **A design or implementation
that contradicts a row here is non-compliant, regardless of what any narrative section says.**

| # | Directive (operator's own terms) | Where it is discharged | Status |
|---|---|---|---|
| **OD-1** | SPDR-021's breakout strategy is the model for the next experiment | D1; design §4 | binding |
| **OD-2** | Test the 4-hour and 1-hour domains **independently** | D2; design §4, §7 | binding |
| **OD-3** | Characterise the baseline strategy **alone, first**, before the volatility components | D3; design §6 arm A | binding |
| **OD-4** | **No commission, no fees — no cost at all.** Reaffirmed against a recommendation to charge spread | D9; design §12 (break-even spread instead) | binding |
| **OD-5** | Run on Nautilus as a **full designed strategy with realistic fills; no vectorisation** | D10; design §4 | binding |
| **OD-6** | **Retain the performance-optimised implementations** from the last experiments | D11; design §4 | binding |
| **OD-7** | **Breadth is fine** — the information gained is worth it | D4; design §4 | binding |
| **OD-8** | **Keep the admission filter**, to be better quantified and validated | D5; design §6 arm D | binding |
| **OD-9** | `drop-worst` / `drop-best` / both, both universes — **per symbol, report-level, not entry tuning**. Report **every cell individually, then pooled, then pooled with the drops** — all reports | D6; design §6E | binding |
| **OD-10** | **Symbol-specific analysis** throughout | D4, D6; design §6E, §11 POOLED rule | binding |
| **OD-11** | **Skip the tested-and-refuted devices** | D7a; design §4, §2.2 | binding |
| **OD-12** | **Keep the tested-but-near-null components** for further quantification and powering | D4, §2.3; design §4 | binding |
| **OD-13** | The "not yet tested" items are the **two blocked questions**, not new components — selection quality and regime-conditional outcomes | §2.4; design §1, E1/E2 | binding |
| **OD-14** | Sizing: **test both continuous and discrete** methods | D7; design §6C | binding |
| **OD-15** | **Devices restricted to SIZE only** | D7a; design §4 | binding |
| **OD-16** | **Drop the REVERSE orientation** arms | D7b; design §4, amendment-1 | binding |
| **OD-17** | **Remove time-derangement entirely** — that robustness class belongs later, at strategy level, where XENA's controls are better designed for it | D8; design §8 (with the note that the future-destroy tripwire is NOT removed) | binding |
| **OD-18** | The next experiment **must emit regime labels per origin and per trade** | E1; design §5, §8 V-C | binding |
| **OD-19** | **If sizing shows evidence of expectancy improvement, measure and report it.** The essence is to measure the effect of the volatility components — drawdown reduction, capture geometry, and everything in between — under **unbiased critical analysis**. No outcome pre-committed | §4.6; E6; design §3, §10; checkpoint §7 refusal narrowed | binding — **see the scope note below** |
| **OD-20** | Try **(A) unchunked trade counts as the sample size** and **(B) chunking by volatility regime, not by day**. Convergence is extra evidence; each is richly informative alone | D12; design §10.1 | binding |
| **OD-21** | Regime chunks must be **sequential / block / episodal** — not all high-volatility trades grouped into one | M2b; design §10.1 V-C rules | binding |
| **OD-22** | **Amend checkpoint-018** to add SPDR-024 (option A) | checkpoint `design.md` item 7b / Step 3b | done |
| **OD-23** | **All cells** carry the sizing magnitude question | O2; design §10 | binding |
| **OD-24** | Both documents **clean and current — no disproved claims, no correction addenda** | this revision | done |

### Scope note on OD-19 — read this before implementing

OD-19 names **capture geometry** among the effects to be measured, and **OD-11 / OD-15** remove the
capture-geometry *devices* (target, stop, trail, hold) from the arm set. These are reconcilable but
the resolution must be explicit:

- The four devices are **not re-run as arms** — they were refuted 6/6 cells (§2.2), and OD-11 is the
  operator's instruction to skip them.
- Capture geometry is still **measured**, as a property of the baseline and of the surviving SIZE
  arms: exit composition (E4), realised hold distribution (E5), the decay curve (H3), and the
  excursion/capture diagnostics carried on every episode.
- **What this run therefore cannot answer:** whether some *differently constructed* capture device
  would help. That is a new mechanism and a new experiment, not a re-run of the refuted four.

If the operator intends capture geometry to return as an arm set, that is a scope change and must
be issued as a new directive — it is not implied by OD-19.

---

## 1. Premise carried from SPDR-021/022/023

Two facts govern everything below.

**The machinery works and the money does not follow.** Every *confirmed* observation across the six
cells is a mechanical consequence of an arm's own definition — hold arms hold longer, size arms cut
dispersion, wider stops lose more. Metrics that are not mechanically forced sit at 0.03–0.7× their
own MDE in all six cells.

**But two of the most interesting questions were never actually asked.** They were blocked by the
emission, not answered by it:

- *Does the admission filter select better trades?* Unanswerable — rejected origins carry
  `outcome_bps = 0.0`, not a counterfactual, on 14,323–695,139 rows per component in both universes.
  `sign_share_difference` inherits the defect: its median (+0.153 cTrader / +0.146 crypto) is just
  the selected side's own win share minus zero.
- *Is any effect regime-conditional?* Unanswerable — the run **gates arms** by volatility state but
  never **labels outcomes** with the realised state. No `vol_state` / `regime` column exists in any
  of the six cells.

So the correct reading is not "the lattice returned its answer". It is: **the lattice answered the
questions it could put, and the two it could not put are the ones worth building for.**

---

## 2. What survived, what died, what is merely under-powered

Three categories. Keeping them apart is the whole point: a device that was tested and refuted and a
component that was merely never powered are not the same object and do not license the same action.

### 2.0 How to read every `est/MDE` ratio below — sample size and dependence, both measured

Two facts govern every ratio in this section. Both are measured on the Step-3 artifacts.

**The sample is far smaller than the row counts suggest.**
`native_parameter_shared_trades.parquet` carries one row **per arm per trade** — each baseline trade
appears a median of 40 times (max 64) across 64 arms. Row counts are not trade counts:

| Cell | rows in the table | **distinct baseline trades** | per symbol (min / median / max) |
|---|---|---|---|
| cTrader H1 | 72,477 | **1,698** | 502 / 570 / 626 |
| crypto H1 | 346,894 | **8,469** | 25 / 420 / 850 |

Row-count statements elsewhere in this document (e.g. "exactly zero on 100% of rows") are stated as
**rows** and remain exactly true as written. They are attestations of an identity across the arm
grid, not sample-size claims.

**Serial dependence is not detectable, so the Step-3 block width was conservative.**
Autocorrelation of the per-trade outcome series, per symbol, ordered by entry time:

| Cell | autocorrelation, lags 1–20 (median) | max abs | 95% noise band | variance ratio, b = 2…25 (iid ⇒ 1.0) |
|---|---|---|---|---|
| cTrader | −0.029 … +0.036 | 0.071 | ±0.082 | 0.83 – 1.14 |
| crypto | −0.005 … +0.038 | 0.153 | ±0.093 | 0.95 – 1.05 |

Every value sits inside its own noise band. The mechanism is transparent: the strategy holds **one
bar** and fires sporadically, so consecutive trades are typically days apart — none of the usual
sources of block dependence (overlapping holding windows, persistent exposure) is present. The
Step-3 24-bar block was **inherited, not derived**, and discounted the sample ~0.7× against a
dependence the data does not show.

**Consequence for every ratio below — stated once, applies throughout.** All Step-3 `est/MDE`
figures were computed under the fixed 24-bar block treatment. Recomputed unchunked they would rise
by roughly **1.19×** (√(570/405) on cTrader; √(420/287) on crypto). That shift is small but not
cosmetic:

- **The four device refutations hold.** Their ratios run 0.00–0.60; at 1.19× they reach at most
  ≈0.71 — still short of resolution, still nulls.
- **The strongest sizing cells become borderline rather than short.** 0.97 × 1.19 ≈ **1.15**. The
  sizing magnitude question may already be *partly* resolved in the Step-3 data, which is a reason
  to power it properly, not a reason to treat it as answered.
- The ~4.5% per-cell resolution rate reported in `confirmation-extraction-021-023.md` §0.3 is
  consistent with correctly-sized-to-mildly-wide intervals, as expected under a modestly
  conservative block width.

`SPDR-024` therefore computes uncertainty **three ways** and reports all three (D12).

### 2.1 Survived — one lever

**State-gated position sizing reduces drawdown depth.** Of every row where the interval was tight
enough to resolve, **236 of 236 landed on the drawdown-reducing side, across 6/6 cells**. Under the
measured null (≈4.5% resolution, symmetric sign) that pattern is effectively impossible by chance.

Two boundaries on it:
- **Magnitude is unresolved, though closer than it first appeared.** Median est/MDE runs
  **0.20–0.97** under the Step-3 block treatment — below the detection floor in every cell.
  Unchunked (§2.0) the strongest cells reach ≈**1.15**, i.e. borderline. In σ̂ units the effect is
  **0.022–0.150 σ̂**. Direction is near-certain; size is not established, and settling it is the
  point of the successor.
- **It is specific to the discrete gate.** Under continuous `SCALE_NORMALISED` the pattern collapses
  (023 crypto: 3 positive / 3 negative, median −347). The finding is about the flag, not about
  vol-aware sizing generally.

This is a **risk transform, not an edge**. It makes no expectancy claim and attaches to whatever
entry survives.

### 2.2 Died — four devices, refuted 6/6 cells

Do not re-test:

| Device | What it does | What it does not do |
|---|---|---|
| **Hold length**, vol-gated | Changes elapsed time and decay: 89.6–100% of rows, 2.40–4.78× MDE | Change trade value: 0.03–0.60× MDE, mixed sign, 6/6 cells |
| **Stop distance**, vol-gated | A tighter stop gives a smaller loss — that is the *distance* | The gate subtracts: gating **shrinks** the effect 1.3–18× versus the plain fixed distance |
| **Trail width**, vol-scaled | Gives back more of the peak when wider: 48.5–73.3% of rows | Bank more of the favourable move: 17.2–32.6% resolve, sign a coin flip, 0.00–0.24× MDE |
| **Recovery after stop** | — | Resolves on 0–17% of rows, positive share 38–56% — a coin flip, including a clean 0-of-41 |

### 2.3 Merely under-powered — all eight components stay in

No volatility component separated itself from any other on the origin lens: median effect
**0.00–0.20× MDE**, resolution **0–17%** against a 4.5% chance rate, signs mixed. Across
`RANGE_SCALE`, `SWING_SCALE`, `LEVEL_NOW`, `LEVEL_FORECAST_K4`, `LEVEL_FORECAST_K12`, `SHOCK`,
`SWING_GT_CUR`, `TAIL_RISK`.

**That is under-powering, not refutation.** Operator decision: **keep all eight**, quantify and power
them properly rather than drop them. **No new components are added** (O1) — the component list for
the successor is exactly these eight.

### 2.4 Never tested — two questions, not a component list

Distinct from §2.3. These are not weak results; they are questions the apparatus could not put at
all, for the reasons in §1: **selection quality** (blocked by the excluded-origin zero-fill) and
**regime-conditional outcomes** (blocked by the missing regime label). They are carried into the
successor as emission requirements **E2** and **E1**, not as new arms.

---

## 3. Apparatus facts that constrain any successor

Each is artifact-traced in the extraction ledger. Each changes what the successor may measure.

| # | Fact | Consequence |
|---|---|---|
| **F1** | **022 and 023 are one substrate.** `E_CLOSE` fixed baselines sum to **exactly 0.0** symbol by symbol (25/25 crypto, 3/3 cTrader, max residual 1.8e-15); origin-lens estimates correlate **r = −0.9893 / −0.9467**. On *devices* they do not mirror — they duplicate (**r = +0.76 / +0.41**, same sign 65–70%). | Direction-paired screens are never two cells. A replication axis built on them is fake. |
| **F2** | **Admission rules never change shared-trade value.** Paired delta exactly `0.0000` on 100% of rows for `BREAKOUT_THRESHOLD`, `PENDING_EXPIRY` and `BAND_H` — ~2.3M rows. `BAND_Z` is the exception (a price offset; ~24% of pairs differ). | Selection levers are unreadable on the trade lens **by identity**. Budgeting power for a trade-lens read of an admission rule spends it on a guaranteed null. |
| **F3** | **Absorbing devices make their own rate metric unreadable.** `reach_rate` Δ exactly `0.0000` on 100% of pure-TARGET arms in 6/6 cells, `observed = comparator = 1.000`. `stop_rate` likewise 98.5–100% on the four breach cells. | The paired population is selected by the quantity being measured. A shared time cap fixes it (see D5). |
| **F4** | **TARGET emits no free metric at all.** `realised_capture_bps`, `missed_excess_bps` and `time_to_target` are all monotone in target distance; `reach_rate` is degenerate. | TARGET is currently unfalsifiable by construction. |
| **F5** | **`TIME_DERANGEMENT` is vacuous.** Identical to its paired real estimate on 100% of rows in all six cells, max \|Δ\| 1.1e-16. A mean over origins is invariant to permuting time labels. | Not a control that passed — a control that is not there. Removed (D8). |
| **F6** | **Three cTrader instruments is not a substrate.** SPDR-021 pooled native mean **−0.00851 → +0.01910** when XAUUSD is dropped — sign flips. Both figures are ~10× *smaller* than the median MDE (~0.12), so neither is a real quantity. 11 of 13 resolving rows are XAUUSD, all negative. | Never report a pooled cTrader figure without its leave-one-symbol-out table. |
| **F7** | **Cost and selection-check columns are empty in the analysis artifacts.** `payoff_scale_ratio` is NaN on all 9,100 rows; `spread_cost_status`, `cost_scope`, `spread_rt_bps`, `partial_cost_mean_bps` are null on 903–19,961 rows per cell. Disclosure lives only in `run_summary.json` / `config.json`. | Cost scope must be carried *into* the analysis artifacts, not left upstream. |
| **F8** | **Device-combination arms are scored against single-device comparators.** Hold caps stacked on level exits cost **4.4–60.1 bps/trade**, 2.11–2.82× MDE, 6/6 cells — but part of that gap is "two devices vs one". | Any combination arm needs a comparator with the same device count. |

---

## 4. Operator decisions for the successor

Signed 2026-08-05. These are decisions, not proposals.

### 4.1 Base and scope

| # | Decision |
|---|---|
| **D1** | **SPDR-021's breakout strategy is the model.** 022/023 are not re-run (F1). |
| **D2** | **Run the 4-hour and 1-hour signal domains independently** — separate cells, never pooled. SPDR-021 ran the H1 signal domain with native 1-minute execution; **H4 is the new second domain**. |
| **D3** | **Characterise the baseline strategy on its own first**, before any volatility component is layered on. The strategy-level levers (D2, D9, D10) are the first-class object of this run, not a preamble to it. |
| **D4** | **Breadth is accepted over narrowing.** All eight components stay; both sizing forms stay; the pool-filter reads are added; per-symbol reads throughout. Rationale on the record: the performance-optimised implementations from SPDR-021/022/023 are retained, which absorbs much of the added cost, and the information gained is judged worth the remaining budget. |

### 4.2 Arms

| # | Decision |
|---|---|
| **D5** | **Keep the admission filter** — to be properly quantified and validated, not dropped. Its value is currently unknown, not disproven (§1). |
| **D6** | **Pool-filter reads:** `drop-worst-from-pool`, `drop-best-from-pool`, and both, on both universes. **Operator clarification 2026-08-05: these are PER-SYMBOL and REPORT-LEVEL, not entry-level arms.** Nothing is tuned at entry; no trade is selected on its own outcome. The reporting ladder is fixed: **(i) every cell reported individually, then (ii) pooled, then (iii) pooled with each drop applied** — all three always shown, none substituting for another. This is a **concentration diagnostic** in the same shape as the SPDR-021 XAUUSD leave-one-out (F6), not a strategy branch. |
| **D7** | **Sizing: test both forms head to head** — continuous (`SCALE_NORMALISED`-style) and discrete / state-gated (`STATE_HALVE_HIGH`-style). The last run only established that the discrete form holds direction and the continuous form does not; that comparison must be made deliberately, not incidentally. |
| **D7a** | **Devices restricted to SIZE only** (operator, 2026-08-06). The four Step-3-refuted devices are not re-run. Concentrates budget on the one live question; narrows scope (amendment direction: TIGHTER). |
| **D7b** | **`REVERSE` orientation arms dropped** (operator, 2026-08-06). DIRECT and REVERSE result distributions overlap almost entirely (cTrader `E_TOUCH BAND_Z`: DIRECT −0.134…+0.038, REVERSE −0.116…+0.030) — orientation is behaving as a label, not a distinction. Halves the grid at no information cost, and the saving funds the H4 domain. Removes arms; relaxes no threshold (direction: NEUTRAL). |
| **D8** | **`TIME_DERANGEMENT` is removed entirely** (F5). Operator's reasoning: this class of robustness test belongs later, at strategy level, where the XENA framework's future-destroy controls are better designed for it — not in a volatility-attribution run. |

### 4.3 Execution constraints

| # | Decision |
|---|---|
| **D9** | **No commission, no fees, no spread.** Results stay gross. The standing prohibition on `fully-net` / `cost-complete` / `tradable` / `deployable` claims applies to every number the run produces. |
| **D10** | **NautilusTrader, full designed strategy, realistic fills, no vectorisation.** |
| **D11** | **Retain the performance-optimised implementations** from the SPDR-021/022/023 build (per-symbol parallel analysis, single-pass bootstrap per group). This is what makes D4's breadth affordable. |
| **D12** | **Uncertainty is computed three ways and all three are reported** (operator, 2026-08-06): **V-A unchunked** (trade count as sample size — the treatment the dependence measurement in §2.0 supports), **V-B fixed-length time blocks** (the Step-3 form; comparability and the conservative bound), **V-C regime-episode blocks** (mechanism-native; reuses the E1 regime label). Analysis-side on one emission — no extra engine run. **Reading rule, pre-declared:** agreement is convergent evidence; divergence is a diagnostic about where dependence lives; the **most conservative of the three governs every band label**; no treatment may be chosen after seeing which favours a result. |

### 4.4 Emission requirements — non-negotiable

Each converts a currently unanswerable question into a testable one. Without them the corresponding
arms are unreadable no matter how well powered.

| # | Requirement | Unlocks |
|---|---|---|
| **E1** | **Realised regime label, per origin AND per trade**, assigned from information available at decision time (causal, `t−1`). Stratify the estimand by it. | The regime question, currently confounded — "the rule fired" *is* the regime label in the present emission. |
| **E2** | **Counterfactual outcome for EXCLUDED origins** — what the rejected trade would have returned had it been taken. | Selection *quality*: whether the filter picks better trades. Prerequisite for D5 and D6. |
| **E3** | **A TARGET metric that is not a function of target distance** (F4). | Makes TARGET falsifiable at all. |
| **E4** | **Plumb `exit_reason` AND `entry_ts` through to the analysis artifacts.** Both are null on 100% of analysis rows while the internals (`_exit_reason` = `'HOLD'`, `_entry_ns`) are fully populated — 72,477 / 346,894 native rows. A column-plumbing break, not a missing measurement. | Exit composition (the direct cause of F3/F4 being undiagnosable) and every time-ordered read, including the V-C regime blocks. One-line fix. |
| **E5** | **Realised hold duration per position, in bars of the signal domain**, plus the bind flag for whatever cap applied. | Required by H1–H3 below; M4's bind-rate reporting depends on it. |
| **E6** | **A size-weighted / capital-normalised outcome estimand**, alongside the existing per-trade bps estimand. | **The per-trade bps estimand is structurally blind to sizing** — see §4.6. Without E6 the question "does sizing change expectancy?" cannot be asked at all, in either direction. |

Additionally, carry the cost-scope block **into** the analysis artifacts, not just the run summary
(F7), and populate or remove `payoff_scale_ratio`.

---

## 4.5 The hold horizon — resolution of O3

### 4.5.1 Why the cap cannot be calibrated from the completed runs

Two measured facts, both from the artifacts:

- **The native comparison population always exits after exactly one H1 bar.** `hold_bars = 1` and
  `_exit_reason = 'HOLD'` on **100%** of rows — 72,477 cTrader, 346,894 crypto. Median = p99 = max =
  60.0 minutes. There is no duration spread to take a percentile of.
- **Across all arms the durations do spread** — median 60 min, p90 240, p95 720, p99 ≈ 2,540
  (cTrader) / 2,630 (crypto); a 12-bar cap would bind 1.66% / 1.95%. **But those percentiles are the
  caps already imposed** by the `B2` / `B4` / `B12` arm settings. Setting the next cap at a
  percentile of that distribution calibrates it against the previous arbitrary choice. **Circular —
  do not do this.**

**Conclusion: the hold horizon is currently a declared parameter, not a measured one.** The
successor's job is to convert it into a measured one, without pretending it already is.

### 4.5.2 Plan — three steps, two of them in this run

**H1 — Emit an uncapped baseline arm.** One arm whose only exit is the strategy's own logic, with a
**safety ceiling** (engine sanity only — the completed run contains positions of up to 763,553
minutes ≈ 530 days). The ceiling is declared as a safety valve, **not** as a design parameter, and
its bind rate is reported. This arm produces the strategy's first non-circular exit distribution.

**H2 — Set the comparison cap by a pre-declared rule on the DURATION distribution only.**
For example: *the smallest bar count on the arm grid that binds ≤5% of H1's uncapped positions.*
Fixed in the design document **before** execution, applied mechanically afterwards.
**Why duration and not outcome:** duration is a nuisance quantity, not the estimand, so choosing from
it is a structural design decision. Choosing from the *outcome* would be selection on the thing being
measured, and would need pre-registration plus a holdout to be legitimate.

**H3 — Emit the decay curve as descriptive, feeding the run AFTER this one.** From the uncapped arm,
mean outcome as a function of bars held. **Pre-register that it does not set any cap in this run** —
it calibrates the successor's. This is the mechanism-derived horizon: the cap belongs where the
marginal bar stops adding value, which is a quantity the strategy defines about itself rather than
one imposed on it.

### 4.5.3 Horizon pairing — hold length and forecast length are one parameter

`LEVEL_FORECAST_K4` and `LEVEL_FORECAST_K12` forecast the volatility state **4 and 12 bars ahead**.
The baseline holds **one bar**. The forecast describes a state the trade never lives to see.

Their near-null is therefore **not** evidence that volatility is unforecastable — it is a horizon
mismatch, consistent with the standing lesson that the availability horizon must match the
mechanism. Confirmed by their ranking on the one lever that works (§4.5.4): bottom two of six in
5 of 6 cells, with zero resolving rows in four cells.

**Design rule for the successor: hold horizon and forecast horizon are chosen together, never
independently.** Hold 4 bars → `K4` is the aligned predictor; hold 12 → `K12`. This is itself a
testable claim: if `K4` resolves at a 4-bar hold and stays dark at a 1-bar hold, horizon-matching is
confirmed and something structural has been learned. **D2 supplies this for free** — at the H4
domain a one-bar hold is four hours, so `K4` spans 16 hours and `K12` two days. Read the forecast
components **per signal domain, never pooled across H1 and H4.**

### 4.5.4 Component ordering on the surviving lever

Median `|estimate| / MDE` on SIZE → `drawdown_bps`, per cell. Bold = best in that cell.

| Component | 021 ctr | 021 cry | 022 ctr | 022 cry | 023 ctr | 023 cry |
|---|---|---|---|---|---|---|
| `TAIL_RISK` | **1.06** | 0.69 | **0.91** | **0.91** | **1.35** | 0.75 |
| `SHOCK` | 0.70 | **0.89** | 0.61 | 0.80 | 0.58 | 0.54 |
| `LEVEL_NOW` | 0.55 | 0.69 | 0.55 | 0.79 | 0.71 | **0.81** |
| `RANGE_SCALE` | 0.43 | 0.23 | 0.70 | 0.32 | 0.76 | 0.15 |
| `LEVEL_FORECAST_K4` | 0.35 | 0.32 | 0.44 | 0.52 | 0.61 | 0.46 |
| `LEVEL_FORECAST_K12` | 0.26 | 0.26 | 0.61 | 0.46 | 0.31 | 0.33 |

`TAIL_RISK` carries the **highest effect-to-noise ratio in five of six cells**, and is the only
component to exceed 1.0 under the Step-3 block treatment (three cells). Unchunked (§2.0), `TAIL_RISK`
clears in most cells and `SHOCK` / `LEVEL_NOW` approach it — which sharpens the ordering rather than
changing it. **The ordering, not the individual ratios, is the durable result**: it is stable across
both substrates and both universes, and it is stable across variance treatments because a treatment
change rescales every cell by the same factor.

**Consequence for O2:** all cells carry the magnitude question (operator decision), but the
*component-level* power should be concentrated where the effect already sits — `TAIL_RISK` and
`SHOCK` first, `LEVEL_NOW` next. The two forecast components are the cheapest place to be purely
descriptive **in the H1 domain**, and the most interesting place to look **in the H4 domain**, for
the horizon reason in §4.5.3.

---

## 4.6 Sizing and expectancy — the estimand must be able to see it

**Operator position (2026-08-05):** if sizing shows evidence of expectancy improvement, that must be
measured and reported. The experiment measures the effect of volatility components — drawdown
reduction, capture geometry, and everything between — under unbiased critical analysis. No outcome
is pre-committed.

**The obstacle is not the claim, it is the metric.** Measured on the completed runs:

- The paired outcome delta for every SIZE arm is **exactly 0.000000 on 100% of rows — all 1,400 of
  them, in all six cells** (`per_stratum_estimates.parquet`, `estimate_source = COMMON_CLOSE_TRADE`,
  `device = SIZE`; max `|estimate|` = 0 in every cell).
- The `device_size.parquet` table emits **no outcome metric at all** — only `concentration`,
  `drawdown_bps`, `risk_dispersion`, `tail_loss_bps`.

**Why:** basis points are per unit of notional. Scaling the position scales the money and leaves the
bps unchanged. So a per-trade bps estimand **cannot** register a sizing effect — in *either*
direction. The zeros above are not evidence that sizing does not move expectancy; they are evidence
that the instrument used has no resolution on the question.

**Consequence — E6 is what makes the operator's requirement executable.** A size-weighted /
capital-normalised estimand must be emitted alongside the per-trade bps estimand. Then:

- If sizing moves the capital-weighted estimand, that is a real measurement and is reported as one.
- If it does not, that is a powered null on a metric that *could* have seen it — which is worth far
  more than the structural zero the current emission returns.

**Binding on the report, either way:** a per-trade bps figure may **never** be cited to support or
refute a sizing-expectancy claim. It is blind by construction, and citing it in either direction
would be a measurement error, not a finding.

**Governance note.** Checkpoint-018 §7 currently refuses "sizing reported as improving expectancy —
sizing changes variance, not mean". That refusal is **narrowed by the same amendment that adds
SPDR-024** (see the checkpoint `design.md`, item 7b): measuring the question on a competent estimand
is permitted and required; asserting the conclusion on a blind one remains refused.

---

## 5. Method requirements

These are about *how* to measure. D4's breadth does not excuse any of them — it raises the stakes on
all of them.

**M1 — Fix the power grammar.** Apply the standing ordering **un-nest → σ̂-normalise → pool**.
Estimate one pooled effect with a symbol-clustered interval rather than 3 or 25 per-symbol reads
compared by eye. Per-symbol reads are a *diagnostic* (D6), not the estimand.

**M2 — Compute the predeclared `MDE = 2.8σ/√n` before execution, per cell.** If a cell's MDE exceeds
the effect size worth acting on, mark that cell **descriptive** in the design rather than discovering
after the fact that it landed at 0.5× MDE again. This is the operative safeguard for D4: breadth is
accepted, blind breadth is not.

**M2b — V-C validity constraints (binding).** Regime-episode blocks are legitimate **only** because a
regime episode is contiguous in time — block resampling then still preserves within-block dependence
and resamples across independent stretches. Grouping all high-volatility periods together regardless
of when they occurred would destroy that property and is prohibited.

```text
V-C RULES (frozen at design time; never tuned after seeing estimates):
  regime label   : from volatility only, causal at <= t-1 (E1). NEVER from outcomes — an
                   outcome-derived block boundary is selection on the estimand and voids the read
  block          : one contiguous regime EPISODE (entry into a state -> exit from it)
  minimum length : episodes shorter than 4 signal-domain bars merge into the preceding episode
  reported       : episode count, episode-length distribution, realised block count per cell — so
                   the reader can see whether V-C had more or less resolution than V-B
```

**M3 — Pre-declare a single primary outcome estimand**, with everything else labelled diagnostic. The
last run's 4.2–4.4% CI-exclusion rate across 1,792 / 12,800 cells is exactly interval coverage, so
without pre-declaration the design cannot separate a finding from its own noise floor.

**M4 — Give every arm a common maximum hold** (F3). Under a shared cap the closed population is the
same population on both sides, `reach_rate` becomes a real number in `(0,1)`, and capture stops being
a distance identity. **Two caveats:** hold caps stacked on level exits cost 4.4–60.1
bps/trade (F8), so the cap must bind rarely and **the bind rate must be reported per arm** —
otherwise the measurement fix silently changes the strategy's economics. And the cap value **cannot
be read off the completed runs** — see §4.5.1 for why that is circular, and §4.5.2 for the
replacement procedure (H1–H3).

**M5 — Drop the `REVERSE` orientation arms.** Operator-approved 2026-08-06; recorded as **D7b**.

**M6 — Declare the replication axes in the design and require agreement on all of them.** One-axis
agreement with another-axis failure is noise with structure. The axis set is
**`signal domain (H1/H4) × universe`**. A substrate axis built on 022/023 would be void — they are
one substrate (F1), and the entry-variant axis goes with it; D2's H4 domain supplies a genuine
independent axis in its place.

**M7 — Every effect reports its break-even spread.** Since no cost is charged
(D9), each arm emits `breakeven_spread_rt_bps = |effect| / round-trips`, computed **at that arm's own
turnover and hold duration** — cost does not cancel in a paired difference when arms differ in trade
count. Label it a **NON-EMITTED SCENARIO**. This preserves the cost information without charging
cost.

---

## 6. Standing constraints that keep this successor honest

Forward-looking rules. Each exists because a plausible-sounding alternative was tested against the
artifacts and failed; they are stated as constraints, not as history.

**Gross is the accounting basis, and break-even spread is how cost enters.** No cost of any kind is
charged (D9). That is defensible for a characterisation run and indefensible for an edge claim — so
every effect emits `breakeven_spread_rt_bps` at that arm's own turnover (M7), and no output may use
the words fully-net, cost-complete, tradable or deployable.

**Breadth is permitted; blind breadth is not.** The SPDR characterisation contract allows a
predeclared grid (D4). The safeguard is M2: a predeclared per-cell MDE computed *before* execution,
with cells that cannot resolve marked descriptive in advance. Breadth without M2 reproduces the
Step-3 failure mode exactly.

**`H` is a selectivity object, read on the origin lens only.** Its event-rate change is close to
mechanically forced — a shorter band lifetime admits fewer events by construction. The live question
is whether the admitted ones are *better*, which requires E2 and is unanswerable without it. The
trade-lens delta for any admission rule is exactly zero by identity (F2), so reading it there is a
guaranteed null.

**Direction and magnitude are separate reads, always.** The sizing result is direction-certain and
magnitude-unresolved *simultaneously*: 236 of 236 resolving rows on one side across 6/6 cells, at
0.022–0.150 σ̂. Any band that collapses those into a single label retires a live finding. §11 of the
design keeps them apart.

**Replication axes are `signal domain (H1/H4) × universe`.** A substrate axis built on 022/023 is
void — they are one substrate (F1). D2's H4 domain supplies a genuine independent axis in its place.
Agreement is required on all declared axes; one-axis agreement with another-axis failure is noise
with structure.

**No outcome may set a measurement parameter.** The hold cap comes from the duration distribution,
never the outcome distribution (§4.5.2 H2). Regime blocks come from volatility at ≤ t−1, never from
outcomes (M2a). A variance treatment is never chosen after seeing which one favours a result (D12).
Each of these would be selection on the estimand.

**A powered null is a result, not a failure.** Where a cell can resolve and does not, that is
reported as a powered null. Where it cannot resolve, it is reported as `NOT_RESOLVABLE` with the
shortfall quantified — never folded into a negative.

## 7. Open items

| # | Item | Status |
|---|---|---|
| **O1** | Are any *new* volatility components to be added? | **CLOSED 2026-08-05 — no.** The component list is the existing eight (§2.3), unchanged. The "not yet tested" bucket was never a component list: it is the two **questions** the apparatus could not put — selection quality (blocked by the excluded-origin zero-fill) and regime-conditional outcomes (blocked by the missing regime label). Both are addressed by **E2** and **E1** respectively. No new components, no added arm count from this item. |
| **O2** | Which cells carry the magnitude question for sizing, and which are descriptive (M2)? | **CLOSED 2026-08-05 — all cells carry it.** Component-level power is concentrated per §4.5.4 (`TAIL_RISK`, `SHOCK`, `LEVEL_NOW` first); the forecast components are descriptive in H1 and primary in H4 (§4.5.3). M2's per-cell predeclared MDE still applies to every cell. |
| **O3** | Maximum-hold cap value and its expected bind rate per arm (M4). | **CLOSED 2026-08-05 as a procedure, not a number.** The cap cannot be calibrated from the completed runs (§4.5.1 — circular). Resolved by H1–H3 (§4.5.2): emit an uncapped arm with a declared safety ceiling; set the comparison cap by a pre-declared rule on the **duration** distribution only; emit the decay curve as descriptive, calibrating the run **after** this one. The numeric cap is fixed in the design document before execution, by that rule. |
| **O4** | The safety-ceiling value for the uncapped arm (H1), and the exact percentile rule for H2. | **CLOSED 2026-08-05 in `python/experiments/SPDR-024/design.md` §7.** Safety ceiling = 120 signal-domain bars, criterion = 10× the largest declared comparison cap so it cannot act as a de facto exit; declared an operational safety valve, bind rate reported, >2% invalidates it. Cap rule = smallest value on the declared grid {2, 4, 8, 12, 24, 48} binding ≤5% of the uncapped arm's closed positions, per universe × domain, duration basis only. |
| **O5** | Whether the paired arm-difference series carries dependence the baseline series does not, and the size of cross-symbol contemporaneous correlation. | Open. Neither is covered by §2.0, which measured the baseline series only. Cross-symbol correlation is not a time-series dependence and is never addressed by time blocking — it is why the interval stays symbol-clustered (M1) under all three treatments. Measure at preflight. |

---

## 8. Boundary

This file is an interpretation and decision product, not a design. It selects no arm, issues no
family verdict, authorises no execution, TEST band, or holdout, and makes no tradability claim — no
cost of any kind was charged in the runs it reads, and none will be charged in the successor (D9).
Any successor experiment requires its own design under `quant-designer`, a fresh-context QA gate, and
an operator authorisation.
