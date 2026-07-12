# Candidate Family Group: CF-MTFCTX-001 — Multi-Timeframe Context Filters on Naive Controls

**Status:** `REGISTERED` 2026-07-10 (chapter 03, first family group). Route: **XENA lane
(default)** — three XENA runs, one universe per control model. No EXP-lane comparative
claim registered; the thesis is read informatively from portfolio-selection outcomes
(operator decision 2026-07-10, Q-A below).
**Provenance:** operator proposal `.ignore/temp/new-referee/mtf.md` (2026-07-10).
**Ledger:** rows in `docs/signal-registry/xena-runs.md` are added per-run at design time
(before search), per ledger rule — with pinned band boundaries + universe manifest.

## Thesis

HTF context (trend direction, trend strength, volatility regime) improves signal quality
of LTF entry models. Tested not as an A/B effect claim but as portfolio selection: filtered
and unfiltered variants enter each XENA universe as equal candidates; the frozen search +
certification + counted gate machinery selects.

## Prior-evidence position (KB, mandatory read done 2026-07-10)

- **P-14 / CF-HTFDI-001 (RETIRED):** HTF ±DI conditioning at 1h→5min is REAL but ≈1–4
  bps/trade — sub-cost. Escape clause: vehicle with ≥10× per-trade capture (longer holds),
  NEW family, **L-21 unit pin at design time**. This group qualifies: holds = 0.5–4× HTF
  span (hours→weeks), new models, new family. Unit pin (ATR units, bps conversion,
  `money_per_unit`) is a mandatory design.md block in every run.
- L-22: gross gate = selection-machinery verdict, never deployability; net informational.

## Locked decisions (operator clarifications, 2026-07-10)

| Q | Decision |
|---|---|
| Thesis adjudication | Portfolio selection only — no separate registered A/B read |
| SlPrice (sizing) | Synthetic **HTF ATR(14) stop, sizing-only** (not a live exit); k pinned at design (robust-to-LTF-noise rationale). **Contract reconciliation (operator, 2026-07-10):** the XENA candidate-gate requirement is a **finite per-leg `SlPrice` field** used as the sizing denominator `|EntryFill − SlPrice|`; a live engine stop order is NOT required. **No live stops anywhere in this family.** |
| Instruments | **Indices basket (10) + XAUUSD + BTCUSD = 12** (all Loaded, VAL-005/VAL-007) |
| CTRL-01 lambda | Fixed at 2 |
| Combo variant counts | Both combo blocks = **6 each** (3 vol × 2 ADX); the proposal's two "(5 variants)" lines (ATR×ADX and ATR×ADX+DI) were typos |
| Hold arithmetic | Proposal's "2x of 4h/15min = 8 bars" examples were arithmetic slips — corrected in source 2026-07-10; multipliers apply to the true HTF span (4h = 16 × 15min → 2x = 32) |
| Implementation | **From scratch** — no reuse of / reference to prior model-specific implementations |

## Shared exploration plane (all three universes)

- **Domain pairs (HTF/LTF):** 1d/1h · 4h/15min · 1h/5min
- **Hold-period multipliers:** 0.5× · 1× · 2× · 4× of HTF span, in LTF bars
  (1d/1h base 24 → {12,24,48,96}; 4h/15m base 16 → {8,16,32,64}; 1h/5m base 12 → {6,12,24,48})
- **HTF context features (confirmed HTF bars only, ≤ t−1):** ADX(14) threshold 25;
  ±DI direction; ATR-based vol regime LOW/MED/HIGH per the proposal appendix (pinned):
  - **ATR model (all HTF ATR uses in this family):** rolling **median** of true ranges,
    window 14 — not the traditional Wilder ATR.
  - **Vol regime:** current ATR ranked as an empirical percentile against the instrument's
    own trailing history (window 200–300 HTF bars — exact value pinned per run at design),
    labeled with hysteresis: HIGH entered > P80 / exited < P65; LOW entered < P20 /
    exited > P35; MID otherwise. Thresholds pre-registered, never tuned on outcomes.
- **Variant set per control (19):** baseline unfiltered (1) + ADX regime (2) + DI direction
  filter (1) + vol regime (3) + ATR×ADX (6) + ATR×ADX+DI (6)
- **Candidates per universe:** 19 variants × 3 domains × 4 holds × 12 instruments = **2,736**

## Control models (entry engines)

| Universe | Model | Entry | Exits |
|---|---|---|---|
| MTFCTX-C1 | CTRL-01 RANDOM | uniform[-1,1]; lambda=2 split → SELL ≤ −0.5, BUY ≥ 0.5; ignore signals while holding | fixed hold-period only |
| MTFCTX-C2 | CTRL-02 NAIVE MOMENTUM | long: close > highest high of last 3 bars; short: close < lowest low of last 3 bars; ignore while holding | fixed hold-period only |
| MTFCTX-C3 | CTRL-03 NAIVE REVERSION | trailing limit at lowest low (buy) / highest high (sell) of last 3 bars; re-quote on new signal pre-fill | hold-period OR profit exit: at any LTF bar close, if close is in profit AND ≥ 0.5 × **current** HTF median-TR ATR(14) (latest confirmed HTF bar, ≤ t−1) beyond entry price → close. Distance **floats with current ATR** (not frozen at entry). No adverse target. |

## Binding constraints

- XENA fills-based emission contract: finite `SlPrice` every leg (HTF ATR sizing stop);
  gate REJECT otherwise.
- **CTRL-03 requires native cTrader limit orders + m1 fills** (EXP-013 lesson: StrategyHost
  OHLC self-adjudication invalid for limit strategies).
- CTRL-01 randomness: fixed seed per candidate, deterministic + regenerable (L-19 D1);
  seed handling pinned at design.
- Frozen registry v3 (sha256 `537d691a…e672a6`) consumed, never re-derived; gate cap
  2/universe; `new_data_attestation` operator-only.
- Bands: `SegmentLayout.from_span` 50/30/20 over the **common analysis span** — start =
  2021-06-02 (common window start); **end = min over the 12 instruments of each file's 70%
  analysis-set cutoff** (the global-holdout fence; NOT end-of-file). Exact ns boundaries +
  per-instrument holdout fences pre-registered in each run's design.md before search. The
  final 30% of every file is never touched.
