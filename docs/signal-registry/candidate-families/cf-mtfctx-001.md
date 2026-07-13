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

## Evidence (append-only; experiment-level. **Family status is NOT moved here** — open/retire/promote is operator-signed at the checkpoint-011 retrospective)

### 2026-07-13 — XENA-001 (CTRL-01 RANDOM control) — operator verdict **MACHINERY-ALARM**

- Eval counts (§10.4): search **255,142** evals / **255,142** distinct subsets; certify 2,190. Gate slots **0/2**. No counted TEST read.
- Certified **4/12 finalists (33%)** vs WS-6 null finalist certification **0.75%** — the pre-registered design §8 MACHINERY-ALARM band ("certification rate far above battery null rate").
- Root cause PROVEN (adjudication layer, not emission): `F_floor` = 0.4302 was calibrated at 24 candidates / 400 budget (null F̂ median 0.19); at live scale (2,736 candidates / budget 21,835) **12/12 finalists clear it by 8.3–13.1×**, leaving the plateau screen — which passes **50.8% of pure-noise finalists** — as the sole certification criterion.
- Substantively noise-consistent: certified fold medians +0.100 / +0.043 / −0.098 / −0.286; worst fold −0.69; `pbo_like` 0.25.
- Battery v2 constant for the family: live median F̂ 4.27 vs permuted 5.94 → **no-structure live-vs-permuted bias = −1.67 log-wealth** (live at the 0th percentile).
- Filter structure (disclosure): V00 share of finalist slots 2.4% vs 5.3% universe = **0.45×** — no informative filter preference on noise.
- Emission layer clean: candidate gate 2,736/2,736; estimand gate 2,736/2,736 PASS; fence + provenance PASS.
- Record: `python/experiments/XENA-001/report.md`.

### 2026-07-13 — XENA-002 (CTRL-02 NAIVE MOMENTUM) — operator verdict **NO DETECTABLE STRUCTURE**

- Eval counts (§10.4): search **397,475** evals / **397,475** distinct subsets; certify 1,851. Gate slots **0/2**. No counted TEST read.
- Live median F̂ 4.79 vs permuted 6.20 (0th percentile; battery delta **−1.41**). Netted against XENA-001's −1.67 no-structure bias → **+0.26 above the random control, well inside XENA-002's own restart dispersion of 2.90**. Statistically it *is* the random control.
- 7/12 certified — **uninformative** given the `F_floor` defect (12/12 clear the floor by 9.7–16.4×). `pbo_like` 0.50 (worse than the control's 0.25).
- One genuine difference from the control: all seven certified finalists have **positive fold medians (+0.063 … +0.246)**, which XENA-001 cannot claim. **It does not survive the battery comparison.**
- Filter structure (thesis read, disclosure): V00 = **1.18×** its universe share among the 322 finalist member slots — filtered variants V01–V18 are **not** preferentially selected.
- Estimand gate 2,773/2,773 PASS.
- **Negative evidence for the CF-MTFCTX-001 arc.** Record: `python/experiments/XENA-002/report.md`.

### 2026-07-13 — XENA-003 (CTRL-03 NAIVE REVERSION, native limit orders) — operator verdict **NOT SUPPORTED (magnitude)**

- Eval counts (§10.4): search **322,803** evals / **322,803** distinct subsets; certify 1,104. Gate slots **0/2**. No counted TEST read. Full evidence: `python/experiments/XENA-003/analysis.md`.
- Gross edge **+1.958 bps/leg**, 95% CI [1.846, 2.073], n = 195,056 legs — real, block- and seed-stable, per-year stable, positive on all 12 instruments.
- **Cost-fatal:** breakeven round-trip spread **0.564–1.146 bps (median 0.705)**; 5/12 finalists survive 0.5 bps, 2/12 survive 1.0 bps, **0/12 at 1.5 bps (all at F = −32.2, ruin)**. Pre-registered "nets survive" band = 20–40 bps gross/trade ⇒ **1/15th–1/30th of it**. (L-21 shape, as at EXP-025.)
- **91.2% of the gross edge is the single mark from the limit print to the next grid open.** The registered snap-back mechanism (0.5–4× HTF span) contributes **0.172 bps (8.8%)**; the forward path from the fill bar's open is **−5.54 bps** (continuation, not reversion).
- Discriminating control (entry times/exits/sizing held; entry price moved to the adjacent grid open): F̂ 23 → **0.09–1.93**, *below* the permuted null ⇒ the live≫permuted gap is **the limit print**, not predictive timing. **The permutation battery is CONFOUNDED for any limit-entry universe** (it destroys the entry-price basis as well as the alignment).
- RULED OUT: leak/look-ahead (provenance + native-fill physicality PASS), Amendment-4 grid seam (≤0.005% of portfolio money), sizing-leverage compounding (notional/equity 0.93–1.10×), "genuine and cost-surviving". SUPPORTED: passive-limit fill-price advantage (dominant) + a genuine sub-cost reversion residual. The emission is an ~80%-occupancy two-sided passive quoting grid — **P-10 territory**.
- **Family thesis contradicted:** unfiltered **V00 is 4.0× over-represented** among the 364 finalist member slots (21.2% vs 5.3%); the search maximises **cadence** (1H5M 75.8%, H05X 53.3%), not conditioning. Median gross/trade V00 1.837 vs filtered 1.922 bps — a wash.
- Certification uninformative: **79.9%** of the 2,736-candidate universe is gross-profitable standalone (94.7% on 1H5M); the 12 restart terminals are near-disjoint (pairwise Jaccard median 0.108) yet all score F̂ 21–25 and all certify — a degenerate landscape.
- Estimand gate 2,777/2,777 PASS. Record: `python/experiments/XENA-003/report.md`.

### Cross-cutting (all three universes, 2026-07-13)

- **Adjudication-layer audit:** `.ignore/temp/new-referee/post-xena-infr-audit.md` — five root causes (extensive-vs-intensive F statistic; costless cadence-maximizing objective; permutation battery confounded on non-grid-priced entries; plateau screen rewards ubiquity not robustness; governance/process sequencing). Warrants a dedicated INFR redesign. **Audit B2 is load-bearing for this family: a conditioning thesis cannot win under a costless cadence-maximizing objective, regardless of whether it is true** — i.e. the lane as built cannot adjudicate CF-MTFCTX-001's thesis.
- **Governance near-miss (recorded):** design §4 spread pins were never set (`cost_bps = 0.0` on ten of twelve instruments in every universe manifest); a gate spend would have produced a binding GROSS pass with a **vacuous NET block** (the L-22 failure shape). Nothing in the pipeline blocked it.
- **Gate ledger: 0/2 for all three universes; the test-read ledger is unchanged; the global holdout was never loaded.**

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
