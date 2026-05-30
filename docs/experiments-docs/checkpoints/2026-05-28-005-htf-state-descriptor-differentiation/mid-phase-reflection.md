# Phase 005 Mid-Phase Reflection (Post-Stage-A Directive)

**Phase:** 005 — Higher-Timeframe Market-State Descriptor Differentiation
**Date:** 2026-05-29
**Gate:** 7 (Mid-Phase reflection) — issued after the Stage A readiness experiments (EXP-034, EXP-035), before any Stage B return-test scope.
**Inputs:** EXP-034 (Prior-Range Location readiness, SUPPORTED, post-experiment APPROVE); EXP-035 (Market Bias deterministic port + episode readiness, SUPPORTED-conditional, post-experiment APPROVE).

This document is the predeclared reflection directive required by Gate 7. It decides, per candidate, proceed/defer/close; fixes the eligible instrument–timeframe cells; confirms the canonical coverage/aggregation rule for the rest of the phase; confirms the locked primary metric still applies; and assigns return-test IDs. No return-test scope existed before this directive, and none of the decisions below were made by inspecting any return, excursion, or P&L value — Stage A computed none.

---

## 1. Canonical Aggregation Rule (phase-wide, locked here)

**Decision: STRICT (exactly-`N`-bar) `1h`/`4h` aggregation is the canonical Phase 005 rule for all remaining experiments. Tolerant (`min_coverage=0.90`) aggregation is not admissible phase-wide.**

This is the predeclared outcome, not a new choice. The design fixed in advance that EXP-034 establishes the single shared coverage rule, and EXP-034's scope fixed the canonical-selection rule: if strict aggregation already clears readiness on `>=2` distinct instruments at a timeframe, strict is canonical and tolerant aggregation remains diagnostic. EXP-034 cleared strict readiness on all four instruments at both `1h` and `4h`, so strict is retained by rule. The tolerant `0.90` diagnostic also fails the predeclared `0.95` matched-bucket stability threshold at `EURUSD 4h` (`92.67%`) and `BTCUSD 4h` (`90.72%`), which further supports not admitting tolerance phase-wide.

Coverage cost accepted under strict: dropped-window rates of `4.44%–13.13%` at `1h` and `14.10%–24.00%` at `4h` (EXP-034). These are real and must be carried as a robustness caveat into any `4h` return test and into EXP-038 segmentation, but they do not block readiness — strict already clears every row/episode floor for Prior-Range Location.

**Why tolerant is rejected even though it would revive Market Bias.** Admitting tolerant solely for Market Bias would (a) replace the predeclared *single shared* phase rule with a per-descriptor aggregation degree of freedom, and (b) select the aggregation rule by its effect on whether a candidate survives — a result-driven choice the predeclaration discipline exists to prevent. EXP-035 also produced no feature-stability evidence that tolerant windows are safe for the Market Bias EMA chain (it reported only that episode counts differ), so there is not even a feature-level basis to treat Market Bias as a special case. The disciplined call is one rule, strict, applied to every descriptor.

---

## 2. Per-Candidate Directive

### Candidate 1 — Prior-Range Location → **PROCEED to return test (EXP-036)**

Readiness is the strongest possible result for this gate: under canonical strict aggregation, all four instruments pass the row, independent-episode, determinism, and denominator checks at **both** `1h` and `4h` (smallest strict bucket `118` rows / `35` episodes, above the `50`-row / `15`-episode test floors; train floors `100`/`30` also exceeded everywhere). This clears the `>=2`-distinct-instrument requirement with margin on both timeframes.

**Eligible return-test cells (EXP-036):** all four instruments — `EURUSD`, `XAUUSD`, `BTCUSD`, `USTEC` — at both `1h` and `4h`, strict aggregation. No cell is dropped on readiness grounds. (`4h` carries the higher strict dropped-window caveat from §1; this is a robustness note for EXP-038, not an eligibility cut.)

Readiness establishes count-eligibility only, not edge. The open question EXP-034 itself flagged — whether the fixed `0.20/0.80` buckets reflect a tradable market-state property or just broad bucketing — is exactly what EXP-036 must answer against the neutral baseline **and** the matched control.

### Candidate 2 — Market Bias (CEREBR) → **DEFER (readiness-gated no-go for Phase 005); do not return-test**

Under the canonical strict rule fixed in §1, Market Bias passes the independent-episode floor on **only `BTCUSD` at `1h`** — a single instrument, which fails the `>=2`-distinct-instrument readiness requirement. Its predeclared fast-stop therefore triggers: *"stop before any return test if independent-episode counts are inadequate on >=2 distinct instruments"* (design, Candidate 2). Every `4h` cell fails outright (train sign-episodes `4–9` vs the `30` floor), and `EURUSD`/`XAUUSD` fall short at `1h` (`24–28`). The shortfall is structural — the stacked `EMA(100)→HA→EMA(100)` smoothing produces too few state transitions to count, not a state collapse (`DominantShare <= 0.774`) and not a defect; it is the intended discriminator. An exported TradingView reference series would lift the fidelity caveat but would **not** add episodes, so it cannot change this decision.

This is recorded as design Expected Outcome #3 (a readiness-gated no-go), specific to this descriptor under canonical aggregation. It is **not** a refutation of the state-descriptor thesis (no return test ran) and **not** a closure of the Market Bias idea for all time — only a determination that it cannot be cleanly, independently return-tested within Phase 005's data and canonical rule. The deterministic port (`python/src/market_bias.py`, EXP-035) is preserved as validated infrastructure for any future phase that obtains more data or a reference series.

### Candidate 3 — Range Compression/Expansion → **NOT activated**

### Candidate 4 — Renko AE-Control → **NOT activated**

The design permits readiness for the contingent candidates *"only if the directional candidates are both ineligible and phase budget remains."* One directional candidate (Prior-Range Location) is eligible and proceeds. The condition is not met; neither contingent candidate receives an ID. They remain dormant unless a later reflection reactivates them.

---

## 3. Confirmation of the Locked Primary Metric for EXP-036

The locked primary edge metric applies unchanged to Prior-Range Location:

- **Primary:** executable direction-adjusted next-bar log return, observed only after the `1h`/`4h` bar closes, entered at the **next same-timeframe bar open**, exited at that bar's close, on real OHLC.
- **Directional framing:** continuation (locked) — top bucket (`>= 0.80`) → long-direction; bottom bucket (`<= 0.20`) → short-direction; opposing states pooled into one state-aligned return.
- **Neutral baseline:** the middle bucket `(0.20, 0.80)`. Absolute return differences with bootstrap CIs; no percentage-vs-zero baseline.
- **Matched control (binding):** same-timeframe **prior-bar momentum sign**, same executable next-bar convention. Beating neutral but not this control is recorded as descriptive state differentiation, not an edge candidate (Gate 4).
- **Replication:** train/test sign preservation on **≥2 distinct instruments** (instrument is the independence unit; 1h and 4h of the same instrument do not count as independent replication).
- **Inference unit:** independent state episodes / non-overlapping blocks, since range-location states are persistent; naive row bootstrap is diagnostic only.
- **Predeclared secondary horizon:** the single fixed 4-bar hold (enter next open, exit close of the 4th subsequent same-TF bar), same machinery, same neutral + control, evaluated with the predeclared asymmetric gate semantics — it cannot manufacture an edge claim; passing it while failing next-bar is recorded as horizon-dependent state differentiation, not refutation.
- **Secondary diagnostics only:** MFE/MAE in ATR units, hit rate, turnover, persistence.

No metric, bucket boundary, lookback, or control was loosened by this reflection.

---

## 4. Assigned Return-Test IDs

| ID | Status | Scope |
| --- | --- | --- |
| **EXP-036** | **Authorized** | Prior-Range Location executable state-aligned return test (next-bar primary + 4-bar secondary) vs neutral middle bucket and prior-bar-momentum-sign control, four instruments × `1h`/`4h`, strict aggregation, locked primary metric. |
| EXP-037 | **Not created** | Was reserved for a second readiness-passing directional candidate. Market Bias did not pass readiness under canonical aggregation, so no second directional return test is authorized. The ID stays unassigned (never reused). |
| EXP-038 | **Contingent** | Robustness/stress test, opens only if EXP-036 produces a surviving control-adjusted differentiation. |

---

## 5. Gate Compliance

- **Gate 1 (readiness-before-return):** satisfied — only the readiness-passing descriptor (Prior-Range Location) advances.
- **Gate 2 (count/episode floor):** the binding reason Market Bias does not advance (single eligible instrument under canonical aggregation).
- **Gate 3 (single-TF-before-MTF):** EXP-036 is single-timeframe per cell; no MTF combination authorized.
- **Gate 4 (matched control):** carried into EXP-036 as a binding pass condition.
- **Gate 5 (holdout):** untouched; no decision here approaches the final 30% global holdout.
- **Gate 6 (no-test-selection):** respected — every decision above used only Stage A readiness diagnostics (counts, determinism, coverage stability); no return value was inspected because none exists yet.
- **Gate 7 (this gate):** discharged by this directive.

---

## 6. Immediate Next Step

Scope **EXP-036** (Prior-Range Location return test) through the research pipeline at Stage 1, using the eligible cells, canonical strict aggregation, and locked primary metric fixed above. Market Bias requires no further Phase 005 action beyond this record. The phase remains on track for a defensible decision: either Prior-Range Location produces a control-adjusted, replicated state edge that earns an EXP-038 robustness test, or it fails the return test and the state-descriptor thesis is refuted for the cleanest candidate with holdout intact.

---

## 7. Post-EXP-036 Addendum (Post-Stage-B, 2026-05-29)

**Status:** EXP-036 complete — `REFUTED`, post-experiment governance `APPROVE`. This addendum records the return-test outcome and the resulting phase position. Sections 1–6 above are the predeclared pre-return directive and are left **unchanged**; no value below was used to alter any predeclared metric, gate, bucket, or threshold. §6's immediate next step (scope EXP-036) is now discharged.

### 7.1 EXP-036 Outcome

Prior-Range Location is **REFUTED** as a Phase 005 executable state-descriptor edge under the locked primary metric.

- **Next-bar primary fails the edge gate.** No `(instrument, timeframe)` cell passes both `Δ_neutral` and `Δ_control` at `1h` or `4h`; `verdict.json` reports empty `next_bar_neutral_and_control` lists for both timeframes. Zero instruments clear the matched-control gate — this is Evidence AGAINST under the predeclared primary verdict.
- **One localized control-positive cell, insufficient.** The only next-bar matched-control positive cell is `XAUUSD 1h` (`Δ_control = +0.000153`, CI `[+0.000052, +0.000252]`), but its neutral contrast does not pass, so it does not even reach state-differentiation-only status.
- **4-bar secondary does not reopen the thesis.** The secondary passes both contrasts only on `XAUUSD 1h` (`Δ_neutral = +0.000482`, CI `[+0.000088, +0.000855]`; `Δ_control = +0.000317`, CI `[+0.000040, +0.000571]`) — one instrument, below the predeclared `>=2`-distinct-instrument rule. Per the asymmetric secondary semantics, one passing instrument is **not** horizon-dependent state differentiation; it is a localized observation, recorded but not promoted.
- **A return-effect failure, not a power failure.** All 32 metric rows are adjudicable. Minimum post-filter counts (train `326` rows / `89` episodes; test `118` rows / `35` episodes) clear every floor. The descriptor had the observations and still did not differentiate.
- **Train/test discipline held.** Some train cells were positive with CIs excluding zero (e.g. `BTCUSD 4h` train next-bar `Δ_control = +0.000864`, CI `[+0.000152, +0.001590]`) but did not survive test; the sign-preservation rule correctly blocked train-only artifacts from being read as evidence.
- **Gap caveat is moot.** Strict `4h` gap-spanning entries (`20.6%`–`25.2%`) remain an executability caveat, but with no surviving descriptor there is nothing whose robustness to gap exclusion the planned EXP-038 check would protect.

### 7.2 Resulting Phase Position

Both authorized directional candidates are now resolved negatively:

| Candidate | Path | Outcome | Design Expected Outcome |
| --- | --- | --- | --- |
| Prior-Range Location | Readiness PASS → EXP-036 return test | **REFUTED** on matched-control gate | #2 (passes readiness, fails return test) |
| Market Bias (CEREBR) | Readiness only | **No-go** (single eligible instrument, canonical strict) | #3 (readiness-gated no-go) |

The cleanest, lowest-infrastructure-risk directional descriptor — the one with the strongest possible readiness result (all four instruments, both timeframes) — failed the return gate with the holdout intact. There is **no surviving directional state-descriptor candidate** on the phase's authorized path.

### 7.3 Logical Next Steps

1. **Do not open EXP-038.** Its predeclared precondition (an EXP-036 survivor) is not met. `EXP-037` stays unassigned and `EXP-038` stays dormant.
2. **No within-phase tuning of Prior-Range Location.** Adjusting its buckets, lookback, framing, or horizon to chase the localized `XAUUSD 1h` 4-bar cell would be test-selection (Gate 6) and requires a new predeclared experiment in a new checkpoint — not a reinterpretation of EXP-036.
3. **The contingent candidates do not auto-activate.** Per the locked design, Compression (3) and Renko AE-Control (4) become eligible "only if the directional candidates are **both ineligible** and phase budget remains." Prior-Range Location was eligible and was return-tested, so the literal activation precondition is **not** met. Both are also structurally weak for this thesis: Compression is non-directional and cannot produce candidate-manifest language, and Renko AE-Control is near-pre-falsified by EXP-008. Activating either would be a discretionary scope expansion this addendum does not authorize.
4. **Proceed to the Phase 005 retrospective.** With the directional path exhausted, the disciplined next action is to author `retrospective.md` for this checkpoint. The live decision there is between design Expected Outcome **#4 — close the state-descriptor thesis** (directional candidates resolved, contingents weak and not auto-activated) and a narrowly-justified, explicitly-argued contingent activation. That is a phase-level call to be made deliberately in the retrospective, not by silently opening another experiment.
5. **Holdout remains untouched** and no candidate manifest exists. Whatever the retrospective decides, the final 30% global holdout is preserved for a future phase.
