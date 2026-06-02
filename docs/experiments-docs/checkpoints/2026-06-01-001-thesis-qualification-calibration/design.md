# Phase 001 — Thesis-Qualification System: Referee Calibration

**Phase number:** 001
**Design finalised:** 2026-06-01
**Status:** ACTIVE (design complete; execution begins at EXP-001)

**Provenance:**
- Problem framing: `docs/planning/thesis-qualification-system-problem-statement.md` (referenced as *PS§n*).
- Full rationale + dissection: `docs/planning/thesis-qualification-phase1-planning.md` (the planning artefact this design distils).
- Practical specimen reference: Masters-style permutation testing (`docs/planning/transcript.txt`).

---

## 1. Phase objective

Build a **referee** — a system that judges whether a candidate trading thesis deserves scarce validation resources — and, in the same phase, **measure what that referee can and cannot see**. The operator's 5-check gate stack is implemented as the candidate referee, but it is held to the problem statement's real deliverable: **measured stringency** (PS§6, PS§8) — a referee whose false-positive / true-positive rates and **economic minimum detectable effect (MDE)** are known, so a "reject" verdict means *"no edge, or an edge below detectable magnitude X,"* with X measured.

This is a **meta / infrastructural thesis**: the deliverable is a validation methodology, not a market edge. It is falsifiable (§4), obeys full holdout discipline (§9), and fits the falsification-first culture — success is *knowing the referee's blind spots*, not *the gate stack passing things*.

The organizing decision for the whole phase: **the 5-check gate stack is the object under measurement, not the conclusion.** Shipping it without the calibration harness would reproduce the exact trap PS§4 was written to expose (PS-T1: unquantified operating characteristics).

---

## 2. Predeclared decisions (frozen before any measurement is read)

These were settled at design time and are **frozen** for the phase. Changing any of them requires a new, predeclared design — they may not be adjusted after seeing results (meta-Goodhart guardrail, §10).

| # | Decision | Resolution |
| --- | --- | --- |
| D-op | Primary operating point | **FPR α₀ = 0.05, power target = 0.80**, held constant across all domains. EXP-003 additionally **reports MDE across a predeclared α₀ grid {0.10, 0.05, 0.01} per domain**, so the stringency↔MDE trade-off is a visible measured axis, not a silent choice. Loss-ratio-derived operating points are deferred to the loss-function phase (§12). |
| D-cost | Frictions / materiality model (leg L5) | **Flat conservative round-trip cost, per-instrument and per-domain**; economic threshold also per-domain. The data layer stores OHLC + TickVolume only (no bid/ask spread), so any spread figure would be invented — a flat cost set to cover a plausible spread+commission is the honest choice. Per-domain because a 5m scalp must clear cost on a far smaller move than a 4h swing. |
| D-edge | Planted-edge structure (known-positives) | **Stationary, fixed-magnitude only.** Cleanest power curve and clearest empirical MDE. Non-stationarity / drift handling deferred (PS-T11). |
| D-dom | Test domains | **5-minute (scalping), 1-hour (general intraday), 4-hour (long-horizon)**, resampled from the 1-minute base via `xen.bar_aggregator`. 1-minute is raw source only — too noisy to calibrate against. |
| D-subj | Test-subject population | **Synthetic** known-null / known-positive generators **+ real dogfood**: Donchian-channel breakout and MA-crossover on the 4 instruments. |
| D-ceiling | Plausible-edge ceiling | **A reported sensitivity axis, not a frozen scalar verdict bar.** EXP-003 reports the empirical MDE as a continuous number (bps/trade net of cost) per domain plus its **break-even ceiling** — the edge magnitude, equivalently the break-even κ in `κ · RT_cost_d`, at which the blind-vs-not-blind reading flips. The reading is finalised against an **empirical anchor**: the measured net effect sizes of the real Donchian/MA dogfood strategies (EXP-004), which locate where plausibly-real intraday edges actually live — not a guessed multiple of cost. κ = 3 is retained only as a **labelled reference marker** on that axis, explicitly non-load-bearing. This mirrors how α₀ is reported across a grid (D-op) rather than committed to one value. |
| D-cov | Resampling coverage policy | **Per-domain `min_coverage` for `xen.bar_aggregator.aggregate_ohlc`:** 5m strict (exactly 5 source bars); 1h and 4h tolerant at **min_coverage = 0.90** (≥54/60 and ≥216/240 source bars). The outcome metric is Close-to-Close directional return and `Close` is the exact last source close regardless of partial coverage, so tolerant mode does not distort this phase's outcome — whereas strict mode would delete most session-gapped 4h windows (USTEC, XAUUSD) wholesale. EXP-001 reports retained bar count and dropped-window fraction per (domain, instrument) **across a coverage grid {strict, 0.90, 0.80}**, and confirms the substrate's null-ness and oracle recovery are stable across that grid — so the 0.90 default is shown immaterial to the substrate rather than assumed. ⚠ Confirm the 0.90 default before EXP-001. |
| D-prec | Estimation precision + Monte Carlo budget | ≥1000 known-null draws (split across the two null generators) and ≥500 known-positive draws per m-grid point, per (referee, domain); ≥1000 inner block-bootstrap resamples per verdict; **identical draws fed to both referees (paired)**. **Usable-precision target:** 95% Wilson CI half-width ≤0.03 on FPR and ≤0.05 on TPR at the operating point. A (referee, domain) cell that cannot reach this is **inconclusive** (§11), not forced to a verdict. |
| D-block | Inference unit / block length | **Stationary (Politis–Romano) block bootstrap** over per-bar strategy returns; expected block length L_d = the first lag at which the strategy-return ACF falls below 1/e, computed on the **train segment only** and **frozen per (candidate, domain) before any test/calibration measurement**. Discretely-trading candidates use entry-to-flat **episodes** as the resampling atom; always-in candidates use the block bootstrap. Effective N = number of independent blocks/episodes, reported with every estimate. |

**⚠ Operator-confirmation items.** The per-domain round-trip costs (D-cost — they set the L5 materiality gate and the economic units the MDE is reported in) and the per-domain `min_coverage` default (D-cov) are set here as defensible defaults, **frozen-but-confirmable until EXP-001 executes** — no measurement has been read, so setting them now *is* the predeclaration. Confirm or override at the EXP-001 manual-execution gate; once EXP-001 runs, they are frozen for the phase. **κ is no longer in this list** — the plausible-edge ceiling is now a reported sensitivity, not a frozen threshold (D-ceiling).

---

## 3. Definitions (the notes conflate two of these)

| Term | Definition |
| --- | --- |
| **Candidate thesis / unit of qualification** | A pair `(signal_fn, outcome_def)`: a rule emitting a per-bar position `{-1,0,+1}`, plus the predeclared outcome it claims to predict. Phase 1 fixes the unit as a **standalone directional signal** (incremental-information unit deferred, PS-T6). |
| **Referee** | `referee(candidate, data, frictions, seed) -> verdict`. |
| **Baseline referee** (meta-level) | The *simplest defensible* validation method; the reference point against which the gate stack is judged. **Not a strategy.** |
| **Neutral baseline** & **naive control** (object-level) | Strategy-level comparators *inside* a referee (leg L3): the candidate must beat its own neutral baseline state **and** a matched naive control predictor. **Distinct from the baseline referee.** |
| **Edge** | Dual claim: **statistical existence** (effect distinguishable from neutral baseline under a serial-dependence-aware inference unit) **and** **economic materiality** (effect exceeds the predeclared per-domain threshold net of the flat cost model). A pass requires both. |
| **Operating characteristics** | A *referee's* TPR / FPR / TNR / FNR, plus per-leg pass rates for the gate stack. |
| **Empirical MDE** | Smallest planted edge magnitude (in **economic units**, bps/trade net of cost) at which TPR ≥ 0.80 while FPR ≤ α₀. Reported **per domain**. The PS§3/§6 deliverable. |
| **Known-null / known-positive input** | Constructions guaranteed to contain no edge / a planted edge of known magnitude. A good referee rejects the former and passes the latter once magnitude ≥ its MDE. |

---

## 4. Falsifiable claims

- **H-keystone (EXP-003 measures; EXP-004 anchors):** *On each domain d, the 5-check gate stack's empirical economic MDE (at FPR ≤ α₀ = 0.05) is below the magnitude of plausibly-real intraday edges for that domain.* EXP-003 measures the MDE as a continuous number and reports its **break-even ceiling** (the edge magnitude / break-even κ at which the blind-vs-not-blind reading flips); the reading is finalised against the **empirical anchor** — the measured net effect sizes of the real Donchian/MA dogfood strategies (EXP-004; §2 D-ceiling). **Falsified on a domain if** the MDE sits above where those plausibly-real edges live (structurally blind), **or** FPR cannot be held at α₀ without pushing it there. **No single frozen scalar decides this** — the MDE and its break-even ceiling are reported; only α₀ is frozen (§2 D-op). Either failure is a *finding*.
- **H-substrate (EXP-001, gating):** *The known-null generators produce series with no oracle-recoverable edge, and the known-positive generators carry a planted, oracle-recoverable edge of the specified magnitude, on real analysis-set prices, on each of the three domains.* If this fails, the phase halts — no downstream measurement is trustworthy.
- **H-dogfood (EXP-004):** *Real Donchian / MA-crossover verdicts (per domain) are consistent with where those strategies' measured effect sizes fall on the calibrated MDE map.* Inconsistency flags a synthetic-vs-real DGP gap (§10 risk).

---

## 5. Object-level scope: the candidate-thesis universe

- **Form:** standalone, price-based **directional** signals (position in `{-1,0,+1}`).
- **Complexity:** few parameters (look-back, threshold). **Black-box / high-capacity ML excluded** by tenet.
- **Instruments:** EURUSD, XAUUSD, BTCUSD, USTEC.
- **Domains:** every candidate, generator, and referee run operates on **5m / 1h / 4h** (§2 D-dom). **Timeframe is a first-class dimension: every test repeats per-domain and is reported per-domain, never pooled** (effective samples differ by orders of magnitude).
- **Outcome metric:** direction-adjusted next-step (one bar at the domain's timeframe, or predeclared horizon) return, evaluated on **real bar prices only** — never HA/Renko construction prices.
- **Real dogfood:** Donchian breakout + MA crossover, one stable look-back each, **not tuned** against analysis-set returns.
- **Deferred:** chart-type-based candidate signals; additional timeframes.

---

## 6. The referees under test

Both share the interface `referee(candidate, analysis_set, frictions, seed) -> verdict`, resample **independent episodes / blocks** per §2 D-block (never raw rows; raw-row inference is diagnostic only), and **report effective sample size**, not raw row count. Verdicts record **graded evidence** (effect size + CI + per-leg outcomes), collapsed to pass/reject only at the boundary (mitigates PS-T12). **The gate-stack referee evaluates all five legs unconditionally** — no short-circuit — recording each leg's outcome, so per-leg pass rates (§7) and false-negative attribution are well-defined; the conjunction is applied only at the decision boundary. Both are **predeclared and frozen** before EXP-003.

### 6.1 Minimal baseline referee (the single comparator)
- one chronological train/test split (the mandated 70/30 within the analysis set);
- one effect test: candidate beats its neutral baseline on the **test** segment, block-bootstrap CI on the difference excluding zero;
- no replication, no control predictor, no cost gate.
Purpose: expose how much the extra gate-stack legs buy (FPR reduction) and cost (MDE inflation).

### 6.2 The 5-check gate stack (candidate referee)

| Leg | Operator check | Mechanism | Maps to |
| --- | --- | --- | --- |
| **L1 Readiness** | enough events | predeclared representation floors (min independent episodes per state, per segment) before any outcome is measured | PS§3.2; PS-T9 |
| **L2 Integrity** | no look-ahead / no holdout / real prices | holdout untouched, no data past event timestamp, returns on real prices | §9 |
| **L3 Outcome** | beats neutral baseline **and** naive control | state-conditioned executable return beats both, block-bootstrap CIs exclude zero | PS§3.3; D6; PS-T6 |
| **L4 Stability** | direction preserved train→test | same-signed effect in both segments | D5 |
| **L5 Materiality** | survives conservative cost sensitivity | effect exceeds the predeclared per-domain economic threshold net of flat cost | D1; PS-T4 |

- The stack is **conjunctive** (PS-T2) — we do not assume that is correct; we **measure** joint power and each leg's marginal pass rate (EXP-003).
- Cross-market k-of-N replication (PS§3.5 / PS-T3) is **reduced to the train→test stability leg L4** in Phase 1; full replication + its multiplicity philosophy + cross-unit dependence modelling are deferred (§12).

---

## 7. Calibration harness (the keystone machinery)

Per PS§6, *test the tester* by feeding inputs of known truth, **per domain**.

- **Known-null generators:** (a) bar permutation (transcript algorithm — destroys structure, preserves marginal moments); (b) random-signal control on real prices. Two generators because they fail differently, revealing which null a referee actually protects against.
- **Known-positive generators:** plant a small, **tradable**, predictable component conditioned on an observable state, of **tunable magnitude m** (economic units), into **real analysis-set prices** at the domain's timeframe; sweep `m` from below to above the plausible-edge ceiling to trace the power curve and locate MDE.
- **What we measure (per domain, per referee):** FPR / TNR (from nulls); TPR / FNR as a function of `m` (from positives); **empirical MDE** (statistical and economic) at the α₀ grid; **per-leg pass rates** for the gate stack (which leg dominates false negatives — PS-T2/T9); **effective sample size** + CIs on the rates themselves.
- **Substrate validation (EXP-001):** validation-style, with negative controls, that nulls are truly null and positives truly carry the oracle-recoverable planted edge — **before** any referee measurement is believed.

### 7.1 Known-positive construction (oracle-recoverable, real-price-valid, known magnitude)

The MDE map's validity rests entirely on this generator, so it is specified here, not deferred to experiment scope:

1. **Observable state.** Define a binary state `s_t ∈ {-1,+1}` from a predeclared, signal-independent rule using only information at or before bar `t` (default: the sign of a fixed lagged momentum feature on the domain's real closes; alternatively a fixed-seed pseudo-random state exposed as a candidate input). `s_t` is part of the candidate's observable input — no look-ahead.
2. **Edge injection in return space.** Let `r_{t+1}` be the domain's real Close-to-Close log return. Add a deterministic state-aligned drift `r'_{t+1} = r_{t+1} + s_t · δ`. With the oracle position `p_t = s_t`, the strategy return is `p_t · r'_{t+1} = s_t · r_{t+1} + δ`; because `s_t` is constructed independent of the real return, `E[s_t · r_{t+1}] ≈ 0`, so the **expected gross per-trade return is `δ`** and the **net is `δ − c_d`** (the per-domain round-trip cost, D-cost). To plant a net edge of `m` bps/trade, set `δ = m + c_d`. The mapping is closed-form; EXP-001 confirms it empirically.
3. **Real-price reconstruction.** Rebuild a price path from `r'` by cumulative composition off the real starting price, so returns are still evaluated on a price-space series (real-price discipline preserved — never synthetic chart prices). For small `m` the injection shifts only the conditional mean by a bounded, predeclared amount; marginal return dispersion is essentially unchanged.
4. **Oracle and magnitude sweep.** The oracle is the state-following rule. Sweep `m` over a predeclared grid spanning **from below the round-trip cost to several times it** (bracketing the plausible-edge range, D-ceiling) to trace TPR(`m`) and locate the empirical MDE. EXP-001 verifies the oracle recovers ≈ `m` on positives (within MC error) and ≈ 0 on every known-null.

### 7.2 Measurement budget and precision (per domain, per referee)

- **Draws (D-prec):** ≥1000 known-null draws split across the two null generators, and ≥500 known-positive draws per `m`-grid point; **identical draws fed to both referees (paired)** so the baseline-vs-stack delta is a within-draw comparison with reduced variance and half the generation cost.
- **Inner resampling (D-block):** ≥1000 block-bootstrap resamples per verdict.
- **Reported with CIs on the rates themselves:** FPR/TNR (nulls); TPR/FNR(`m`) (positives); empirical MDE at the α₀ grid {0.10, 0.05, 0.01}; per-leg pass rates; effective N.
- **Usable-precision gate (D-prec):** a (referee, domain) cell is reportable only if the 95% Wilson CI half-width is ≤0.03 (FPR) / ≤0.05 (TPR) at the operating point; otherwise it is **inconclusive** (§11), reported with honest CIs rather than forced to a verdict.

---

## 8. Traceability to the problem statement

**Desiderata (PS§2):** D1 **in**; D2 **partial** (within-evaluation; programme-level deferred); D3 **in — core**; D4 **enforced** (holdout); D5 **partial** (train→test only); D6 **partial** (fixed metric for the narrow universe); D7 **in** (predeclaration + freeze); D8 **in — core**.

**Failure modes (PS§4):** T1 **directly addressed** (raison d'être); T2 **measured** (joint + per-leg power); T3 **partial** (L4 only); T4 **addressed** (economic MDE); T5 **partial**; T6 **deferred** (standalone unit); T7 **addressed** (block inference + effective-N; cross-unit dependence deferred); T8 **flagged**; T9 **addressed** (L1 pass rate measured); T10 **deferred** (needs registry); T11 **fixed** to single chronological split; T12 **mitigated** (graded evidence recorded).

The implicit loss function (PS§5) is made explicit only insofar as one operating point is predeclared (§2 D-op); tunable loss is deferred (§12).

---

## 9. Holdout & discipline constraints

- All generators built on, and all runs use, **only the first 70% analysis set**. The global final 30% is never loaded or inspected.
- Within the analysis set, the mandated 70/30 chronological train/test split applies.
- **Shared split boundary across domains:** the analysis/holdout and train/test cuts are derived **once** as `CloseTime` timestamps from the canonical base and applied to all three resampled domains — never as per-timeframe row fractions (which would leak future bars across domains).
- **Resampling coverage (D-cov):** the 5m / 1h / 4h domains are produced by `aggregate_ohlc` with the per-domain `min_coverage` of §2 D-cov; retained bar counts and dropped-window fractions are reported per (domain, instrument) in EXP-001, so each domain's effective sample is visible before the keystone is interpreted.
- **Validation precondition P0 (gates EXP-001 on 5m/4h):** VAL-001 validated the `aggregate_ohlc` path at {1, 15, 60} minutes only. Before EXP-001 runs on the 5m/4h domains, the temporal-integrity suite (VAL-001's control-per-check standard) must be extended to the **{5, 240}-minute** parameterizations used here — 240-minute in particular has different coverage-retention behavior. EXP-001 on those domains does not start until this passes.
- Real-price outcome discipline, timestamp alignment over bar count, deterministic generation (fixed seeds, recorded), and single-question-per-experiment all hold.

---

## 10. Planned experiments

Next ID is **EXP-001**. Each answers one question; EXP-001 gates the rest; **every experiment repeats across 5m / 1h / 4h and reports per-domain.** If EXP-003 proves too heavy, it splits **by domain**, not by test type.

| ID | One-line question | Depends on | Budget (tests / plots / modules) |
| --- | --- | --- | --- |
| **EXP-001** | Are the known-null generators truly edge-free and the known-positive generators carrying the planted, oracle-recoverable edge, on real analysis-set prices, on each of 5m/1h/4h? | — | validation, ~1–2 / 2–4 / 1–2 |
| **EXP-002** | Do the minimal baseline referee and the 5-check gate stack, on golden-fixture inputs, reproduce hand-computed verdicts and expose each leg independently? | EXP-001 | correctness, ~0–1 / 1–2 / 1–2 |
| **EXP-003** | What are the per-domain FPR / TPR / economic MDE (at the α₀ grid) / per-leg pass rates of each referee, and is the gate stack's economic MDE below the plausible-edge ceiling at α₀=0.05 on each domain? **(keystone)** | EXP-001, EXP-002 | comparative, ~2–4 / 3–5 / 1 |
| **EXP-004** | Do real Donchian / MA-crossover verdicts (per domain) agree with where those strategies' measured effect sizes fall on the calibrated MDE map? | EXP-003 | comparative, ~1–2 / 2–3 / 0–1 |

**Predeclaration freeze (meta-Goodhart guardrail):** referee designs and the harness are frozen before EXP-003; the harness measures them **once**; we do **not** iterate a referee against synthetic results within the phase. Any redesign requires a new predeclared referee and ideally a fresh synthetic draw.

**EXP-003 compute and feasibility.** The run set is `2 referees × 3 domains × 4 instruments × [2 null-generators × ≥1000 draws + M m-grid points × ≥500 draws]`, each verdict running ≥1000 block-bootstrap resamples with all five legs evaluated. Per-bar strategy returns are precomputed once per (candidate, domain, instrument, draw) and reused across legs and resamples; null draws are shared across both referees (paired). Order of magnitude ≈ 10⁵ verdicts × 10³ resamples ≈ 10⁸ vectorised objective evaluations — tractable in numpy/Polars. **Fallback if too heavy:** split EXP-003 **by domain** (not by test type) and reduce `N_pos` on 4h, keeping the D-prec precision gate as the stopping rule.

**EXP-004 consistency rule (makes H-dogfood falsifiable).** For each real strategy × domain, measure its net effect size (bps/trade, block-bootstrap CI on the analysis set) and locate it on that domain's calibrated MDE map. The verdict is **consistent** iff it *passes* when the measured-effect CI lower bound ≥ MDE and *rejects* when the measured-effect point estimate < MDE, with a predeclared grey band of ±1 MC-MDE uncertainty in which either verdict is acceptable. **Inconsistent** = a pass with effect below MDE (false-positive-like) or a reject with effect well above MDE (false-negative-like); either flags a synthetic-vs-real DGP gap, which is exactly what EXP-004 exists to surface. These same measured effect sizes are the **empirical anchor** for the keystone reading (§4 H-keystone, D-ceiling): they define where plausibly-real intraday edges sit, against which EXP-003's per-domain MDE is judged blind or not.

---

## 11. Phase-level success / failure / inconclusive criteria

- **Success:** the harness (a) rejects known-nulls at a measured FPR with **usable precision (D-prec: 95% Wilson CI half-width ≤0.03 FPR / ≤0.05 TPR)**, (b) traces a TPR(m) curve per domain yielding a finite empirical economic MDE for each referee at the α₀ grid, (c) produces per-leg diagnostics for the gate stack, and (d) the dogfood strategies receive interpretable verdicts consistent with the §10 EXP-004 consistency rule. **Success is stating the operating characteristics — not the gate stack passing anything.**
- **Failure:** the synthetic substrate cannot be validated (EXP-001 fails) → phase halts; or H-keystone is falsified on a domain (referee structurally blind there) → recorded as the phase's primary finding.
- **Inconclusive (per domain):** effective sample too small to meet the **D-prec precision target**. **Expected most likely on the 4h domain** — treated as a first-class measured result ("structurally blind / under-powered on the long domain"), not a failure; 4h CIs are reported honestly rather than forced to a verdict.

---

## 12. Explicit non-goals (deferred to later phases, traceable to PS§7)

Programme-level multiplicity / file-drawer registry (PS-T10); multiplicity philosophy beyond baseline — FDR / hierarchical / sequential / Bayesian (PS-T3); walk-forward / regime-stratified / combinatorial purged CV split-protocol comparison (PS-T11; *the MCPT specimen is the natural first addition here*); graded-posterior / expected-value decision output (PS-T12); incremental-information / ensemble unit (PS-T6); tunable context-dependent loss function (PS§5); chart-type candidate signals; non-stationary / drifting planted edges.

---

## 13. Summary

The problem is not "design better gates" (PS§8). This phase honours the operator's choice to **build the 5-check gate stack now**, but subordinates it to **measured stringency**. The keystone is EXP-003 — the per-domain FPR / TPR / economic-MDE / per-leg map for the gate stack and a minimal baseline — gated by a validated synthetic substrate (EXP-001) and correct referee implementation (EXP-002), reality-checked against real Donchian / MA strategies (EXP-004). We will know what the referee can and cannot see, on each trading domain, *before* we trust what it says.
