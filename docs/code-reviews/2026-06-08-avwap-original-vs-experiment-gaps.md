# AVWAP Original Concept vs. EXP-020–023: Gaps Analysis

**Date:** 2026-06-08
**Context:** Brainstorming document `.ignore/temp/signal-registry/anchored-vwap.md` mapped against the registered experiment chain EXP-020 through EXP-023.
**Trigger:** EXP-021 completed and reported. EXP-022 code written but not yet executed. EXP-023 not started.

---

## 1. Anchor is a running extreme, not a detected pivot

**Original concept (anchored-vwap.md):**
> "When a trend change is confirmed, the anchor point resets to the **last significant pivot**."

**What shipped (EXP-020, `python/src/xen/avwap.py`):**
The anchor is the **lowest Low** (bullish regime) or **highest High** (bearish regime) observed anywhere in the prior segment between regime confirmations. There is no pivot-detection logic — no zigzag, swing-point, fractal, or ATR-based detection. The algorithm tracks running min/max as scalars (`seg_min_low`, `seg_max_high`) and uses the extreme bar at regime change.

**Implication:** An outlier bar (single extreme tick) can become the AVWAP anchor. The original concept of a "significant" pivot (a structural turning point price respected) was replaced with a simpler mechanical rule. The `[REQUIRES_DEFINITION]` tag was resolved by choosing the simplest implementation, not by testing whether the original intent matters.

**Severity:** Minor — the definition was explicitly underspecified. But the difference matters if outlier-driven anchors degrade AVWAP signal quality.

---

## 2. Only 1 of 4 trend detectors implemented

**Original concept (anchored-vwap.md):**
Four methods discussed as parallel options:
1. MA crossover (baseline)
2. Linebreak direction change
3. Market Bias Indicator trend value
4. Pivot High/Low with ATR reversal

**What shipped:** Only MA(20,50) crossover. The other three are registered as non-baseline branches in `docs/signal-registry/candidate-families/avwap.md` (`CF-AVWAP-001/LB`, `CF-AVWAP-001/MB`, `CF-AVWAP-001/ATR`). None have a scope, code, or experiment planned.

**Implication:** The entire experiment chain (EXP-020 through EXP-023) tests only one trend-detection method. The original concept's robustness across detectors is untested. If MA(20,50) has specific failure modes (e.g., whip-saws in ranging markets), no other method is available to compare against.

**Severity:** Major — 75% of the brainstormed detector designs are shelved.

---

## 3. Volume exponent alpha frozen at 0.75, never swept

**Original concept (anchored-vwap.md):**
> "Use `w = TV^α`, 0.5 ≤ α ≤ 0.9. α is tunable. Typical values: α = 1.0 (standard), α ≈ 0.75 (good balance), α = 0.5 (square-root weighting)."

**What shipped:** Frozen at 0.75 in `avwap.py:40`. All experiments use this single value. The alpha-sensitivity branch (`CF-AVWAP-001/ALPHA`) is registered but has no scope or code.

**Implication:** The nonlinear weighting was a core design choice explicitly called out as worth exploring. The sensitivity to this parameter is completely unknown. Results could change materially at α = 0.5 (heavy compression) or α = 1.0 (linear VWAP). No data to assess this.

**Severity:** Major — a key parameter the brainstorm explicitly wanted swept, frozen without testing.

---

## 4. HYP-001 (VWAP as support/resistance) was never tested directly

**Original hypothesis (anchored-vwap.md):**
> HYP-001: "The VWAP line (or range/bands) serves as significant support/resistance levels. Therefore, price is more likely to react off these levels, and make significant moves."

**What was tested instead:**
The registry (`docs/signal-registry/candidate-families/avwap.md`) remapped the original HYP-001 into:
- EXP-021: After a bounce trigger (price crosses VWAP in the bounce direction), does it keep moving that way?
- EXP-022: Do band-target/trend-change completions resolve more favorably than controls?

Neither tests whether price respects the VWAP line as S/R. They test **bounce continuation** and **target completion** — different phenomena. The original question "does price actually react at the VWAP line?" was never answered. The `[REQUIRES_DEFINITION]` tag on "significant moves" and "price reaction" was resolved by redefining the question, not by answering the original.

**Implication:** The foundational assumption of the strategy — that the AVWAP line functions as S/R — is untested. If price does not actually respect the line, the bounce mechanism is just noise filtered through a regime gate. EXP-021's positive result is consistent with the S/R thesis but does not prove it.

**Severity:** Major — the core thesis was redefined before testing.

---

## 5. Risk-adjusted return metric (Sharpe ratio) not implemented

**Original concept (anchored-vwap.md):**
Performance metrics included:
- "risk-adjusted return metric (e.g Sharpe ratio) of the returns series of the model compared to the raw/traditional (log) returns of the price series"

**What shipped:** EXP-020/021/022 explicitly exclude all P&L, costs, and strategy-level metrics. They are component studies. The risk-adjusted comparison was deferred to EXP-023, which has no scope, no code, and no execution timeline.

**Implication:** The original metric book is incomplete. A positive component result (bounces have directional edge) does not mean the strategy has positive risk-adjusted returns after costs, slippage, and position sizing. The most important metric for strategy viability was deferred to an experiment that doesn't exist yet.

**Severity:** Major — a core deliverable with zero work done.

---

## 6. Streaming cache design differs in implementation

**Original concept (anchored-vwap.md):**
> "The system has to track the most recent 'viable' pivot point, and should maintain a **temporary cache** of the necessary data from that point, until the pivot is 'confirmed'... The temporary cache is very important and should be **different from the main storage structure**."

**What shipped (`avwap.py`):**
The implementation is described as "streaming-safe" — the state machine processes bars sequentially and never uses future data. However, the actual AVWAP calculation at regime change does a **retrospective loop** over already-stored bars from anchor to confirmation:

```python
for k in range(anchor_idx, i + 1):
    cum_wp += typ[k] * weight[k]
    cum_w += weight[k]
```

There is no separate physical cache. The algorithm re-reads completed bars from the main data array. All experiments are batch — no real-time streaming code exists. The streaming safety claim means the *algorithm could* be adapted to streaming, not that it *is* a stream processor.

**Implication:** Works correctly for batch processing (all experiments). A true streaming implementation would need a pre-accumulated cache to avoid re-reading bars on every regime change. This matters if the signal were ever deployed to live cTrader — the batch loop could become a latency issue on long regimes.

**Severity:** Moderate — functionally equivalent for batch research, but the architecture differs from the original design intent, and no live streaming deployment has been tested.

---

## 7. Minor notes

- **Pyramid bounce tagging** — Implemented as event metadata in EXP-020, planned as a diagnostic split in EXP-022. Adequately covered.
- **Treatment of unfinished observations** — Handled correctly in EXP-021 (ignored) and EXP-022 (counted and excluded from target-completion rate). Covered.
- **Cross-timeframe analysis** — Explicitly deferred in the original ("not implemented for first stage"). Not a gap.
- **Binary regimes only** — Consistent with original. Bull/Bear only, no neutral. Covered.

---

## Summary

| # | Gap | Severity | Status |
|---|---|---|---|
| 1 | Anchor is running extreme, not pivot | Minor | Resolved underspecified definition with simplest option |
| 2 | 3 of 4 trend detectors unimplemented | Major | Registered but no scope/code exists |
| 3 | Alpha frozen at 0.75, never swept | Major | Registered but no scope/code exists |
| 4 | HYP-001 S/R thesis never tested directly | Major | Remapped into bounce-reaction, original question unanswered |
| 5 | Sharpe/risk-adjusted return not computed | Major | Deferred to EXP-023 — not started |
| 6 | No separate streaming cache | Moderate | Batch equivalent works; live deployment concern |
