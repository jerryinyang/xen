# Phase 022 — Portfolio Construction, Noise Infusion & Global-Holdout Release (CF-MR-001, batch 3)

**Status:** **OPEN — G0 RATIFIED 2026-06-24 (operator-authorized).** Batch 3 of CF-MR-001 — the
**deployment-economics & out-of-sample-final** step for the bare RSI-2 fade (CORE) with EXIT-RCT, confirmed
net-tradable on the analysis-TEST stratum at G-021. **D0 FROZEN** (`D0-predeclarations.md`); the terminal
global-holdout rubric (`G-022-gate-criteria.md`) and the pre-holdout freeze gate (`G-022a-gate-criteria.md`) are
frozen at **G-022a**, after EXP-095/096 and before EXP-097 reads the holdout. No result-producing code runs
against anything but the frozen D0.

**Family:** [`CF-MR-001`](../../../signal-registry/candidate-families/cf-mr-001.md) — RSI-2 mean-reversion (fade)
entry. **Lever (admitted G-020, tradable G-021):** the **bare RSI-2 fade (CORE) + EXIT-RCT**, intraday.
**Predecessor checkpoint:** [`2026-06-23-021-mr-fade-capture-geometry`](../2026-06-23-021-mr-fade-capture-geometry/G-021-gate-review.md)
(G-021 **TRADABLE**; 8/11 carried cells confirmed OOS on the analysis-TEST stratum).
**HYP:** `CF-MR-001/HYP-003` (deployment economics & global-holdout-final confirmation of the admitted lever).
**Slot status:** CF-MR-001's first candidate slot was consumed at G-020; **Phase 022 consumes no additional
slot** (no new signal candidate — the portfolio/risk model is a deployment wrapper on the admitted lever).

---

## 0. What G-021 handed this phase (and the scope it forbids)

G-021 adjudicated the bare RSI-2 fade + EXIT-RCT **TRADABLE** on the analysis-TEST stratum: **8 of 11 carried
(instrument, domain) cells CONFIRM** under the frozen referee + Holm-11 + per-cell margin, across 7 instruments
and both domains. The deployable evidence tiers (G-021 §1):

| Tier | Cells | Quality |
| --- | --- | --- |
| **4h robust core** | EURUSD-4h, XAUUSD-4h, USDCHF-4h, AUDJPY-4h, EURJPY-4h, GBPJPY-4h | mean-AND-median net-positive OOS (`net ci_low_1s` 0.039–0.094 vs 0.025 margin) |
| **1h mean-carried** | USTEC-1h, US2000-1h | clear the binding mean gate OOS; median fragile (USTEC TEST median −0.026) |
| **non-confirm (retained)** | EURUSD-1h, NZDUSD-1h, GBPUSD-1h | EVIDENCE_AGAINST / INCONCLUSIVE — **not deployable**, retained in the file drawer |

That verdict is a **per-cell, single-trade-expectancy** read net of a flat conservative cost, under an
**idealized at-close entry fill** and **no portfolio construction**. Three deployment-grade questions remain,
and they are this phase:

1. **Portfolio economics** — does combining the deployable cells into a time-aligned, equal-risk portfolio with
   cross-instrument correlation produce a materially better *risk-adjusted* result (annualized Sharpe, MaxDD,
   Calmar) than any single cell — and can the risk model adapt online to a cell that decays?
2. **Fill realism** — does the edge survive a realistic 1-minute entry fill (the G-021 reads filled entries at
   the signal bar's *close*, with zero entry slippage — the one unmodeled execution gap)?
3. **Deployment-grade OOS-final** — does the finalized, noise-aware portfolio confirm on the **final-30% global
   holdout** (the programme's sanctioned, irreversible one-shot, à la EXP-032)?

**Explicitly out of scope (carried from the G-021 routing — not re-litigated here):**

- **The 3 non-confirming 1h cells** (EURUSD-1h, NZDUSD-1h, GBPUSD-1h) — EVIDENCE_AGAINST / INCONCLUSIVE OOS; not
  deployable, not in the portfolio. Retained in the file drawer.
- **The deferred levers** — vol-regime partition (inert), TREND/RSI-FILTER variants (dead), contrarian arm,
  25/75 regime scheme, 15m capture, regime×variant cross-cuts, faster-cost sensitivity, RSI/EMA/ATR/window
  tuning. All **registered-but-deferred**; each needs its own dated `D0-amendment-*` + slot decision. None
  enters Phase 022.
- **Entry / exit / cost re-tuning** — the entry (RSI 2/10/90), exit (EXIT-RCT), adverse side (2.0×ATR + MR-tempo
  cap), and cost model (`D0-amendment-003` conservative table) are **frozen as confirmed at G-021**. Phase 022
  adds a portfolio/risk wrapper and an entry-fill noise model on top — it does not change the underlying signal.

## 1. The phase question (tradability → deployable economics → OOS-final)

**Deployed as a realistic, time-aligned, equal-risk portfolio — sized causally, with cross-instrument
correlation and an online risk guardrail, and executed under a realistic 1-minute entry fill — does the
confirmed RSI-2 fade retain a positive risk-adjusted edge that confirms on the final-30% global holdout?**

The honest prior, carried from the programme: **analysis-TEST already showed uniform TRAIN→TEST shrinkage**
(G-021: Δ net_ci_low −0.005…−0.107); the global holdout is a further-forward, fully-fresh slice that may show
*additional* decay. Diversification should *help* (averaging idiosyncratic decay across weakly-correlated cells)
and the online guardrail should de-risk any cell that deteriorates — but the holdout is a genuine falsification
of the *deployment* claim, not a victory lap. A DEPLOYABLE_CONFIRMED outcome makes the fade the programme's
first deployment-grade price strategy; a DECAYED outcome is recorded permanently and the deployment claim is
not supported OOS-final.

## 2. Binding constraints inherited (not re-derived)

- **Signal / exit / cost (binding, frozen):** entry `RSI(2)` 2/10/90 Wilder; exit **EXIT-RCT** (`P*_t = Close_t +
  (AL_t − AG_t)` long / symmetric short, trailing, 1-minute intrabar fill `xen.intrabar_fill`); adverse side
  `2.0×ATR(14)` + EXP-089 MR-tempo cap; cost = the `D0-amendment-003` Phase-021-local conservative round-trip
  (`F=0`). All inherited byte-for-byte from Phase 021. **No re-tuning.**
- **Deployable cell set (binding):** the **8 confirmed cells** (G-021): 6×4h robust core + USTEC-1h + US2000-1h.
  The portfolio is *studied* on all 8 (the online-adaptability question — see §3 EXP-095); the
  **holdout-frozen deployable set is whatever survives the noise infusion** (decided at G-022a from analysis-set
  evidence — operator decision 2026-06-24: keep all 8 unless noise demonstrably breaks a cell, to test the risk
  model's real-time adaptation rather than pre-pruning).
- **Holdout / read discipline:** EXP-095/096 read only TRAIN + reuse EXP-093's **already-resolved analysis-TEST
  series** as **portfolio-aggregate disclosures** (the portfolio-aggregate rule; no new per-stratum selection or
  inference) → **0 new counted TEST reads**; the 11 carried strata stay at **1/2**. **EXP-097 spends the
  final-30% global holdout** — the programme's single sanctioned one-shot release (à la EXP-032), **outside the
  analysis-TEST ledger entirely**. No global-holdout bar is loaded before EXP-097, and EXP-097 runs only after
  the G-022a freeze.

## 3. The deployment / risk model (the substantive content of "equal-risk with correlation")

Built and frozen at D0 (§D2–D5); parameter-light, causal, **no Sharpe-maximizing optimization**.

- **Sizing — Equal Risk Contribution (ERC / risk parity), not naive inverse-vol.** ERC equalizes each cell's
  *covariance-aware marginal risk contribution* — required because the deployable set has a heavy correlation
  structure (the 4h JPY cluster EURJPY/GBPJPY/AUDJPY shares a common JPY factor; EURUSD/USDCHF share USD/EUR).
  Naive inverse-vol over-allocates to the JPY cluster; ERC does not. ERC has **no free weight parameters** — it
  is determined by the covariance matrix — which keeps the construction clean of academic-finance overfitting.
- **Causal weights (binding).** The covariance / vol driving ERC is a **trailing rolling estimate (past-only),
  rebalanced on a fixed wall-clock cadence**, weights held between rebalances. No full-sample covariance applied
  retroactively (that would be look-ahead). Cadence + window are predeclared (§D3) with a sensitivity bracket,
  **not tuned**.
- **Global risk anchor (binding).** A single global scalar targets a fixed annualized portfolio volatility, so
  the equity curve is a real currency-P&L (MaxDD interpretable). *Sharpe is invariant to this scalar*; it sets
  drawdown/leverage realism only.
- **Concurrent-risk cap (guardrail).** Total open *risk-aware* exposure is capped (correlation-adjusted, so 3
  JPY crosses firing together count as ≈one bet) — the principled form of "max positions open."
- **Online performance circuit-breaker (the adaptability mechanism).** Pure ERC is **expectancy-blind** — it
  rebalances on *volatility*, not *edge*, so a cell whose mean decays but whose vol is unchanged keeps its full
  allocation and bleeds. To get genuine online adaptation, a **causal, parameter-light circuit-breaker**
  de-allocates a cell whose trailing realized performance deteriorates (§D4), restoring it on recovery. This is
  **risk management** (de-risking a decaying book), not return optimization — its threshold is a predeclared,
  conservative guardrail, never a fitted weight. This directly tests the operator's online-qualification /
  adaptability question on the genuinely fragile cells (the 1h mean-carried tier is the natural stress case).
- **Two portfolios, run in parallel and compared (EXP-095 headline).** **A: static-membership ERC** (vol-adaptive
  only); **B: ERC + circuit-breaker** (vol- *and* edge-adaptive). The A-vs-B comparison on the analysis set *is*
  the answer to "can construction adapt to fragile cells online." Once the 8 cells are resolved on holdout
  (the single EXP-097 read), both A and B are weightings of the *same* return streams, so **both curves are
  computable on holdout for free** — the predeclared one is binding, the other is disclosure.

## 4. Planned experiments (proposed; IDs assigned, scope frozen at each Stage-1/D0)

TRAIN + analysis-TEST-disclosure only through EXP-096; the single global-holdout contact is EXP-097, gated
behind G-022a.

| EXP | Role | Reads / slots | One-line falsifiable leg |
| --- | --- | --- | --- |
| **EXP-095** | **Portfolio construction & online-adaptive risk model** (analysis set, noise-free) | 0 / 0 | Built from the 8 deployable cells, does a causal ERC portfolio (static **A** vs circuit-breaker **B**) deliver materially better risk-adjusted performance (annualized Sharpe / MaxDD / Calmar) than the best individual cell, and does **B** measurably de-risk a deteriorating cell vs **A**? Also calibrates (synthetic-null FPR / bite-check) the portfolio-level confirmation statistic that G-022a will freeze. |
| **EXP-096** | **Noise infusion — realistic 1-minute entry fill** (analysis set) | 0 / 0 | Re-resolving entries under the 1-minute entry-fill model (next-open / next-open+slippage / worst-of-k), and re-deriving the portfolio under the binding fill, does the risk-adjusted edge survive — and which cells, if any, does realistic execution break? Decides the G-022a holdout-frozen deployable set. |
| **EXP-097** | **Global-holdout release — one-shot OOS-final** | **1 global-holdout shot / 0 slots** | On the **final-30% global holdout**, does the frozen, noise-aware deployable portfolio (binding construction) confirm a positive risk-adjusted edge within the G-022a-predeclared band? The single sanctioned irreversible read (à la EXP-032). |

EXP-097 is **conditional and gated**: it runs only if EXP-095/096 produce a finalized deployable model that
clears the **G-022a** pre-holdout freeze (a non-empty deployable set + a calibrated, predeclared confirmation
rule and expectation band). If noise infusion empties the deployable set or the portfolio shows no analysis-set
edge, the phase closes at G-022a with **the holdout unspent**.

## 5. Complexity budget (per experiment)

| Item | Budget |
| --- | --- |
| Binding statistical tests | EXP-095: 1 (the portfolio risk-adjusted vs single-cell comparison) + the confirmation-statistic calibration; EXP-096: ≤2 (noise-survival of the portfolio edge); EXP-097: 1 (the binding holdout confirmation) + descriptive companions |
| Visualisations | ≤ 5 per experiment (equity curves A/B/per-cell; correlation/weights heatmap; circuit-breaker de-allocation timeline; noise sensitivity ladder; TRAIN/TEST/holdout drawdown) |
| New code modules | **Target 1–2.** One justified new module — `xen.portfolio` (causal ERC weights from a trailing covariance, vol-target scaling, concurrent-risk cap, circuit-breaker overlay, time-aligned multi-domain equity-curve aggregation). The entry-fill noise model is a small extension to `xen.intrabar_fill` (an entry-side fill rule mirroring the existing exit-side touch logic). Reuse `xen.mean_reversion`, `xen.intrabar_fill`, `xen.capgeo_cost`/`xen.financing`, `xen.ass` (bootstrap), and the EXP-090/093 substrate verbatim for per-cell return streams. |

## 6. Verdict and routing (G-022 — terminal gate; rubric frozen at G-022a)

| Adjudicated state | Consequence |
| --- | --- |
| **DEPLOYABLE_CONFIRMED** (EXP-097 confirms the portfolio within the G-022a band on the global holdout) | The bare RSI-2 fade is the programme's **first deployment-grade price strategy**. The holdout shot is spent; the deployable model (set, ERC, circuit-breaker, fill, cost) is the frozen production spec. Deferred levers become expansion candidates, each under its own slot/D0. |
| **DECAYED / NOT_CONFIRMED** (holdout edge below the band / spans zero / negative) | The analysis-TEST edge did not survive to the fully-fresh final slice as a deployable portfolio. Recorded permanently; the deployment claim is unsupported OOS-final; the holdout shot is spent and non-repeatable. The per-cell file drawer and the analysis-TEST TRADABLE verdict stand unchanged. |
| **INCONCLUSIVE** (holdout read power-limited / CI spans zero, à la EXP-032) | Disclosed; neither confirmed nor refuted as a deployment; the holdout shot is spent (one-shot, non-upgradable, EXP-032 precedent). |
| **G-022a HALT** (EXP-095/096 leave no deployable set / no analysis-set edge / uncalibrated statistic) | Phase closes **before** the holdout is touched; the shot is preserved. The risk-model and noise findings stand as disclosure. |

## 7. Discipline (binding throughout Phase 022)

- **Causal everything.** Portfolio weights, vol estimates, correlations, the concurrent-risk cap, and the
  circuit-breaker use **past-only** information at each point on the equity curve; no full-sample or future bar
  enters any weight. Cross-domain alignment is by **timestamp** (`CloseTime`), never by bar index.
- **No optimization.** ERC is parameter-free in its weights; every guardrail hyperparameter (rebalance cadence,
  covariance window, vol target, concurrent-risk cap, circuit-breaker window/threshold, noise slippage
  magnitude / `k`) is **predeclared at a conservative/conventional value** (§D-table) and validated with a
  **sensitivity bracket, not a tuning sweep**. No value is ever selected because it lifts the analysis-set curve.
- **Real-price outcomes only.** All P&L / expectancy / drawdown on real domain & 1-minute OHLC
  (`RealOpen/High/Low/Close`); HA / brick prices never enter a metric; fills are real touched prices.
- **Read discipline.** EXP-095/096 are **0 counted TEST reads** (TRAIN + the EXP-093 analysis-TEST series reused
  as portfolio-aggregate disclosure; the 11 strata stay 1/2). **EXP-097 is the single sanctioned global-holdout
  release** — recorded as a holdout-governance event; no holdout bar is loaded before the G-022a freeze.
- **New gate statistic ⇒ bite-check.** The portfolio-level confirmation statistic (the holdout decision rule) is
  **new** → it must be calibrated (synthetic-null FPR controlled) and **bite-checked GREEN in EXP-095 before
  G-022a freezes it**, exactly as every prior binding TEST read carried a pre-TEST synthetic-null calibration
  (EXP-037/038 R1; EXP-094 bite-check). The holdout band is predeclared so the one shot can be over- or
  under-confirmed (EXP-032's margin lesson).
- **Deviation handling.** A frozen-design confound is corrected by a dated `D0-amendment-*` + hard-delete + full
  rerun (programme norm), not a silent follow-up.
- **Per-stratum / per-cell doctrine (LESSON-001).** The portfolio is the *binding deployment estimand*, but
  per-cell holdout outcomes are disclosed alongside it (no cell-level result is hidden inside the aggregate).
- **File drawer.** Portfolio A and B, every guardrail-sensitivity result, and every per-cell holdout outcome are
  retained whatever the verdict; nothing is reopened by re-parameterization.

## 8. G0 decisions — operator-ratified direction (frozen at D0)

The following reflect the operator's 2026-06-24 direction (the §pre-design discussion) and are made binding in
`D0-predeclarations.md`:

1. **Deployable set — RATIFIED: study all 8 confirmed cells; freeze the holdout set to noise-survivors.** Keep
   all 8 in the portfolio study to test the risk model's online adaptation to fragile cells (rather than
   pre-pruning the median-fragile 1h pair); the holdout-deployable set is whatever survives EXP-096, decided at
   G-022a.
2. **Risk model — RATIFIED: parameter-free ERC + causal trailing covariance + vol target + concurrent-risk cap +
   online circuit-breaker; NO Sharpe optimization.** Run static-**A** vs circuit-breaker-**B** in parallel and
   compare.
3. **Noise model — RATIFIED: all three variants as a sensitivity ladder; bind the realistic-conservative one.**
   Next-1m-open (mild floor), next-open+slippage (binding), worst-of-next-k (stress ceiling).
4. **Holdout — RATIFIED: included as the gated terminal EXP-097**, behind the hard G-022a freeze (deployable set,
   construction, calibrated confirmation rule, predeclared band) — the single sanctioned one-shot release; the
   binding estimand is the **portfolio** (per-cell disclosed).

**Parameter values set (FROZEN in `D0-predeclarations.md`, G0-RATIFIED 2026-06-24)** with conservative defaults
and sensitivity brackets — see the D0 ratified-parameter table (§ratified table, D2–D6). The terminal holdout
rubric (`G-022-gate-criteria.md`) and the pre-holdout freeze (`G-022a-gate-criteria.md`) are frozen at G-022a
(they depend on the EXP-095/096 analysis-set portfolio estimate for the predeclared band — they cannot be fixed
at G0 without look-ahead into the band itself).

*Companion docs **FROZEN** (G0-RATIFIED 2026-06-24): [`D0-predeclarations.md`](D0-predeclarations.md). To be
frozen at **G-022a** (after EXP-095/096, before EXP-097): `G-022a-gate-criteria.md` (pre-holdout freeze) +
`G-022-gate-criteria.md` (terminal holdout rubric). Family spec:
[`../../../signal-registry/candidate-families/cf-mr-001.md`](../../../signal-registry/candidate-families/cf-mr-001.md).*
