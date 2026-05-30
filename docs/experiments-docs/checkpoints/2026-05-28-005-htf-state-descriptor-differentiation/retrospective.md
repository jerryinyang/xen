# Retrospective: Phase 005 Higher-Timeframe State-Descriptor Differentiation

**Checkpoint:** 2026-05-28-005-htf-state-descriptor-differentiation
**Experiments:** EXP-034 through EXP-036
**Design date:** 2026-05-28
**Mid-phase reflection:** 2026-05-29
**Retrospective date:** 2026-05-29
**Status:** Phase Completed - State-Descriptor Thesis Closed With No Candidate Manifest
**Predecessor:** [2026-05-26-004-ustec-breaker-ifvg-selectivity](../2026-05-26-004-ustec-breaker-ifvg-selectivity/retrospective.md)

---

## 1. Scope

This retrospective evaluates Phase 005 against its locked thesis:

> On `1h`, `4h`, and contingent `1d` real-price bars, does a simple predeclared market-state descriptor differentiate executable direction-adjusted forward return relative to its own neutral baseline state and a matched simple control, replicating across train and test on at least two distinct instruments?

Phase 005 deliberately started from a new thesis after the event-chart-as-alpha and ICT-as-alpha paths closed. It tested whether higher-timeframe state descriptors could carry executable forward-return information before any global holdout spend. The phase locked a four-descriptor candidate universe in priority order:

1. Prior-Range Location
2. Market Bias (CEREBR)
3. Range Compression/Expansion (contingent)
4. Renko AE-Control (contingent)

The phase conclusion is **negative**. Prior-Range Location passed readiness but failed the executable return gate. Market Bias produced validated infrastructure but failed canonical strict readiness on the independent-instrument requirement. Compression and Renko AE-Control were not activated because the directional path produced no surviving source and because both contingents are structurally misaligned with the locked directional thesis. No EXP-038 robustness path opens, no candidate manifest exists, and the final 30 percent global holdout remains untouched.

In evidentiary terms, the thesis closes on **one completed return test, not four**. Of the four locked candidates: exactly one (Prior-Range Location) was return-tested and refuted; one (Market Bias) was readiness-gated out before any return test; and two (Compression, Renko AE-Control) were never activated. The closure is therefore a statement about the *predeclared four-candidate search space as resolved by Phase 005's gates* — strong because the one candidate actually tested was the cleanest possible case — not a claim that every conceivable higher-timeframe state descriptor has been falsified.

This is design Expected Outcome #4: **the thesis closes before holdout**.

---

## 2. Experiment Status Summary

| Experiment | Role | Verdict | Key phase finding |
| --- | --- | --- | --- |
| EXP-034 | Prior-Range Location readiness and aggregation rule | SUPPORTED | Fixed `20`-bar range-location buckets pass row, episode, determinism, and denominator checks on all 4 instruments at both `1h` and `4h` under strict aggregation. Strict aggregation remains canonical; tolerant `0.90` is not needed and perturbs `4h` bucket stability for EURUSD and BTCUSD. |
| EXP-035 | Market Bias deterministic port and episode readiness | SUPPORTED (conditional) | The Market Bias port is deterministic and warmup-convergent everywhere, but under canonical strict aggregation only `BTCUSD 1h` passes the sign-state independent-episode floor. Tolerant `1h` would pass BTCUSD and USTEC, but admitting it would break the shared aggregation rule. |
| EXP-036 | Prior-Range Location executable return test | REFUTED | No next-bar cell passes both neutral and matched-control contrasts. The 4-bar secondary passes both contrasts only on `XAUUSD 1h`, below the `>=2` distinct-instrument gate. Counts were adequate, so the failure is return-effect, not power. |

All three experiments received post-experiment governance approval. No experiment inspected or used the final 30 percent global holdout.

---

## 3. Candidate-Level Results

### 3.1 Prior-Range Location: Readiness Passed, Return Edge Failed

EXP-034 established that Prior-Range Location was the cleanest possible Phase 005 directional test case. Under canonical strict `1h`/`4h` aggregation, every instrument and timeframe passed the row-count, independent-episode, determinism, and denominator checks. The smallest strict bucket had `118` rows and `35` independent episodes, above the relevant test floors.

That made EXP-036 a fair return test rather than a sample-size probe.

EXP-036 then refuted the candidate under the locked metric:

- **Next-bar primary:** zero instrument-timeframe cells passed both `Delta_neutral` and `Delta_control`.
- **Only next-bar control-positive cell:** `XAUUSD 1h`, `Delta_control = +0.000153`, CI `[+0.000052, +0.000252]`; its neutral contrast did not pass.
- **4-bar secondary:** only `XAUUSD 1h` passed both contrasts (`Delta_neutral = +0.000482`, CI `[+0.000088, +0.000855]`; `Delta_control = +0.000317`, CI `[+0.000040, +0.000571]`), below the required two distinct instruments.
- **Power check:** all 32 metric rows were adjudicable; minimum post-filter counts were train `326` rows / `89` episodes and test `118` rows / `35` episodes.
- **Train/test discipline:** train-only positives, including BTCUSD `4h` next-bar matched-control strength, did not survive test and were correctly blocked.

The localized `XAUUSD 1h` 4-bar result is recorded as an observation, not as horizon-dependent differentiation. It does not reopen EXP-038 and does not justify within-phase tuning of lookback, bucket thresholds, direction framing, or horizon.

### 3.2 Market Bias: Infrastructure Preserved, Phase No-Go

EXP-035 produced a useful implementation result: `python/src/market_bias.py` is deterministic, warmup-convergent, and aligned with the published Pine formula as a deterministic re-implementation. Because no TradingView reference series was available, the phase correctly avoids claiming Pine-equivalence.

The readiness result did not support a Phase 005 return test under the canonical rule:

- Under strict aggregation, only `BTCUSD 1h` passed the sign-state independent-episode floors.
- Every `4h` cell failed the episode floor, with train sign episodes only `4-9`.
- `EURUSD 1h` and `XAUUSD 1h` were near misses (`24-28` train episodes vs the `30` floor), but near misses are still no-go under the predeclared gate.
- Tolerant `0.90` aggregation would make `BTCUSD` and `USTEC` pass at `1h`, but the mid-phase reflection rejected tolerant aggregation as a per-descriptor rescue because strict was already canonical for the phase and tolerant feature stability was not established for the Market Bias EMA chain.

The result is a readiness-gated no-go for Phase 005, not a universal refutation of Market Bias. Future work may reuse the port if it obtains more data, a verified TradingView reference series, or a newly justified aggregation/design rule.

### 3.3 Compression and Renko AE-Control: Not Activated

The contingent candidates are not opened in this retrospective.

There is an honest textual ambiguity in the design: one sentence says Compression and Renko run only if the directional candidates "fail and the phase still has budget," while the mid-phase activation rule and directive narrowed this to "both directional candidates are ineligible." After EXP-036, both directional candidates are resolved negatively, but not in the same sense: Prior-Range was eligible and received a fair return test; Market Bias was readiness-gated out.

The decisive reason not to activate the contingents is not the wording alone. It is thesis alignment:

- **Range Compression/Expansion** is non-directional. Its primary predicts future absolute movement or excursion, not executable direction-adjusted return. A positive result would likely reconfirm volatility clustering and could not produce candidate-manifest language without a separate directional source.
- **Renko AE-Control** is a risk-management adjunct. Its own design requires adverse-excursion reduction with FE non-inferiority, and EXP-008 already showed Renko confirmation lowers FE alongside AE on all 4 instruments.
- Neither contingent has a surviving directional source to attach to. Opening either now would convert Phase 005 from a directional state-descriptor edge test into a weaker volatility/risk-management scan after the prioritized candidates failed.

That would be a discretionary new scope, not a phase-completion consequence. It should require a new predeclared checkpoint if pursued.

---

## 4. Thesis-Level Result

Phase 005 closes the higher-timeframe directional state-descriptor thesis as tested.

The strongest candidate in the design - Prior-Range Location - was deterministic, count-eligible, conceptually simple, and independent of prior event-chart and ICT failures. It still failed the matched-control return gate. The sourced HA-derived candidate - Market Bias - was implementable but too persistent to provide enough independent episodes under the canonical strict aggregation rule. The two remaining candidates do not answer the locked directional return thesis and are not activated.

The accurate closure statement is:

> On the Phase 005 analysis set, no predeclared higher-timeframe state descriptor produced replicated, control-adjusted executable forward-return differentiation across at least two instruments. No descriptor earns robustness testing, candidate-manifest language, or holdout validation.

This does not prove that no state descriptor can ever work. It does close this checkpoint's locked four-candidate search space and prevents continuation by tuning a failed descriptor or reaching for weaker contingents after seeing negative returns.

---

## 5. Lessons and Model Implications

### 5.1 Readiness is not evidence of edge

EXP-034 was a clean readiness success, but EXP-036 showed that count-eligible state labels can be return-neutral once compared against both their own neutral state and a matched simple control. Future phases should continue separating "can be measured" from "adds return information."

### 5.2 Matched controls are doing real work

The lone next-bar control-positive cell did not also beat the neutral baseline, and the 4-bar secondary replicated on only one instrument. Without the matched-control and distinct-instrument gates, Phase 005 could have over-read a localized XAUUSD result. The control discipline prevented a false promotion.

### 5.3 Independent episodes are the right denominator for persistent states

Market Bias had enough rows but too few independent state episodes under the canonical strict rule. That is not a nuisance technicality; it is the statistical reality of a double-smoothed persistent descriptor. Future long-memory indicators should budget around independent episodes from the start.

### 5.4 A single aggregation rule prevented candidate rescue

The strict-vs-tolerant aggregation decision mattered. Tolerant aggregation would have kept Market Bias alive on `1h`, but only by selecting a rule that helped one descriptor after another descriptor had already passed strict readiness. Keeping a single phase-wide rule preserved the predeclaration boundary.

### 5.5 The global holdout remains intact

No Phase 005 candidate reached analysis-set robustness eligibility. There is no candidate to validate and no reason to spend the final 30 percent global holdout.

### 5.6 Three consecutive thesis closures is itself a programme-level signal

Phase 005 is the **third** major thesis to close with no candidate manifest and the global holdout never spent: event-chart-as-alpha (Phases 001–002), ICT-as-alpha (Phases 003–004), and now higher-timeframe state descriptors (Phase 005). At a third closure this pattern should be read explicitly before Phase 006 locks a direction, because two readings have opposite implications and the programme has not distinguished them:

- **Cumulative negative map (benign).** The programme is systematically and honestly charting where edge does *not* live on this data under disciplined gates. This is the design's stated preferred outcome — a defensible decision over a flattering one — and it compounds: each closed thesis narrows the search space for the next. Under this reading the closures are the intended product, not a failure.
- **The analysis-set gate stack may be near-impassable (the risk to check).** Beating a matched control *and* the neutral baseline, with train/test sign preservation on `>=2` distinct instruments, all before any holdout spend, is deliberately strict. If a genuine but modest edge could not clear that bar even when present, three closures would partly reflect gate calibration, not only candidate quality. This has never been tested.

The correct response is **not** to loosen the gates — that would dissolve the discipline that makes the negatives trustworthy and is explicitly a non-goal. It is to make the Phase 006 design *choose between these readings on purpose*: either move to a materially different domain or data source, or first sanity-check that the gate stack is passable at all (for example, confirm that a deliberately strong or synthetic known-positive baseline would clear it) before spending further candidates. What the programme should not do is drift into a fourth descriptor reframing by default.

---

## 6. Phase Gate Assessment

| design.md gate | Assessment |
| --- | --- |
| Readiness-before-return gate | Met. EXP-034 and EXP-035 ran before any return test; only Prior-Range Location advanced. |
| Numeric count and independent-episode gate | Met. Prior-Range passed everywhere; Market Bias failed the `>=2` distinct-instrument requirement under canonical strict aggregation. |
| Single-timeframe-before-MTF gate | Met. No multitimeframe combination was built. |
| Matched-control gate | Met, negative. Prior-Range failed the required neutral-plus-control return gate. |
| Holdout gate | Intact. No experiment inspected or used the final 30 percent global holdout. |
| No-test-selection gate | Met. No bucket, lookback, horizon, aggregation tolerance, or candidate choice was changed using test returns. |
| Mid-phase reflection gate | Met. The post-Stage-A directive authorized EXP-036 and blocked EXP-037/contingents before any return-test scope existed. |
| Robustness gate | Not reached. EXP-038 requires a survivor; none exists. |

---

## 7. Recommended Next Steps

1. **Close Phase 005.** Do not open EXP-038 or any Phase 005 contingent experiment. EXP-037 was already retired by the mid-phase reflection (its ID is burned and never reused), so there is nothing to reopen there.
2. **Do not tune Prior-Range Location inside this checkpoint.** The `XAUUSD 1h` 4-bar cell is a recorded localized observation only. Changing buckets, lookback, direction framing, instruments, or horizon would be test-selection.
3. **Preserve useful infrastructure.** Keep `python/src/bar_aggregator.py` and `python/src/market_bias.py`; both are validated research infrastructure even though no edge candidate survived.
4. **Start Phase 006 from a genuinely new thesis, and resolve the §5.6 question first.** The next checkpoint should not be a continuation of event-chart-as-alpha, ICT-as-alpha, or Phase 005 state-descriptor tuning unless it brings new design evidence and a new predeclared scope. Before locking that direction, the Phase 006 design must explicitly decide the programme-level question from §5.6 (three consecutive thesis closures): either commit to a materially different domain or data source, or first stress-test whether the analysis-set gate stack is passable when a known-positive effect is present. Do not default into a fourth descriptor reframing.
5. **Keep the holdout untouched.** The global holdout remains reserved for a future candidate that first earns analysis-set validation and robustness.

---

## 8. Final Phase Conclusion

Phase 005 achieved its purpose: it tested a new, falsifiable higher-timeframe state-descriptor thesis without spending holdout and without moving the goalposts. The cleanest directional descriptor passed readiness and failed returns. The sourced HA-derived descriptor produced reusable code but failed canonical strict readiness. The contingent volatility/risk candidates do not answer the locked directional thesis and are not activated.

The valid output is a boundary, not a strategy: simple higher-timeframe state descriptors, as predeclared in Phase 005, do not produce a defensible control-adjusted executable edge. The phase is closed with no candidate manifest and the global holdout intact.
