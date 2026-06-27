# Experiment: EXP-039 — `/EXIT-X` TRAIN-Only Exit Screen (DIAG-006)

**Registry:** `CF-AVWAP-001/DIAG-006` — 0 candidate slots (diagnostic screen).
**Governing design:** `docs/experiments-docs/checkpoints/2026-06-10-010-exit-exploration-and-line-sr/design.md` (§5/A1, §8.1).
**Date scoped:** 2026-06-10.

## Hypothesis

Exploratory (no binding hypothesis test): on the unchanged AVWAP bounce-entry
substrate, measure the TRAIN per-event **net** expectancy of each registered
candidate exit rule (E1–E5) under the frozen cost model, and determine
mechanically — per the predeclared design §8.1 rule — whether any candidate
qualifies for a one-shot TEST confirmation (EXP-041).

## Question

Does any structurally distinct exit rule beat the best validated exits (FH
H\*=12 on 4h; band-target/trend-change everywhere) on TRAIN, positively and
stably, on the 4h (primary) or 1h (secondary) domain?

## Scope Boundaries

- **Data Views**: 1-minute time bars resampled to 1h and 4h OHLC domains via
  `xen.bar_aggregator` (same coverage conventions as EXP-028/030); Heiken Ashi
  candles generated from the domain bars (for E1/E2 triggers only); the
  canonical EXP-020 AVWAP event substrate (frozen definition: MA 20/50 trend
  detector, `TickVolume**0.75` weight, MAD band multiplier 1.0), unchanged.
- **Entry substrate**: identical to EXP-028/030/037 — AVWAP bounce entries with
  pyramids, **all_legs** policy (Phase 008 frozen winner). No entry-signal,
  anchor, band, or pyramid-policy change. The exit rule is the only varied
  element.
- **Candidate exits (registered; frozen at this scope's freeze)**:
  - **E1 — HA Harami size exhaustion** (full replacement): exit at the domain
    bar close where `max(HAClose_1, HAOpen_1) > max(HAClose_0, HAOpen_0)` and
    `min(HAClose_1, HAOpen_1) < min(HAClose_0, HAOpen_0)` (bar_0 = latest,
    bar_1 = prior), direction-independent. No parameters.
  - **E2 — HA trailing reference** (full replacement): exit at the domain bar
    close where `RealClose` crosses the prior bar's `min(HAOpen, HAClose)`
    (long) / `max(HAOpen, HAClose)` (short). Bar-close market-style trigger
    only. No parameters.
  - **E3 — Last-X high/low trailing** (full replacement): exit at the domain
    bar close where `RealClose` < lowest `Low` of the prior X domain bars
    (long) / > highest `High` of the prior X bars (short). **X ∈ {3, 5, 8}**.
  - **E4 — Adverse-band stop** (band-target leg retained; trend-change leg
    replaced): exit at the domain bar close where `RealClose` crosses the
    adverse-side MAD band of the live anchored VWAP (registered band
    definition, multiplier 1.0). No parameters.
  - **E5 — Target-conditional time-stop** (band-target leg retained;
    trend-change leg replaced): hard exit at the close of the H_ts-th domain
    bar after entry confirmation if the band target has not been hit.
    **H_ts ∈ {8, 12, 24}**.
- **Reference exits (fixed)**: R-BTC = registered band-target/trend-change exit
  (HYP-004-R baseline); R-FH = FH(H\*=12, all_legs) on 4h only (EXP-037
  freeze, hash-pinned; 1h is FH-ineligible per EXP-033 — the 1h bar is R-BTC
  plus positivity).
- **Cost model (frozen, no iteration)**: EXP-030 CONSERVATIVE per-event costs +
  Phase 008 financing (EURUSD 0.6 / USTEC 1.2 / XAUUSD 1.2 / BTCUSD 10.0
  bps/day, adverse-side, fractional calendar days entry-confirmation close to
  exit close), charged per realized position including pyramid legs, exactly as
  in EXP-030/037.
- **Parameters**: domains {1h, 4h}; exit grids as declared above; frozen
  EXP-027 inference tail (hash `e50873d12a9f68d9` family) for bootstrap SEs/CIs
  — descriptive only, no binding hypothesis test in this screen.
- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD — descriptive tables for all
  four; the **binding screen statistics use the surviving-instrument sets**
  (4h and 1h: EURUSD, USTEC, XAUUSD; BTCUSD excluded by the EXP-030/D0
  break-even map). EURUSD rows carry the TEST-cap disclosure (design §7.3).
- **Time range**: **TRAIN only** — first 70% of the analysis set (which is the
  first 70% of each dataset). Boundary = the R1.3 1-minute-row timestamp
  convention (`train_end_ts` = CloseTime of the last TRAIN 1-minute analysis
  row, `train_rows = int(analysis_rows × 0.7)`). An event is TRAIN iff its
  trigger close time ≤ boundary. **No TEST row is read.**
- **Boundary containment (R1.5 analog)**: all selection statistics are
  computed on the boundary-contained TRAIN subset — events whose exit under
  the candidate resolves at or before `train_end_ts`. Events unresolved at the
  boundary are excluded from selection; exclusion counts disclosed per
  exit×domain×instrument. The containment population is computed per candidate
  exit (disclosed), with the shared reference comparisons (§ criteria) always
  evaluated on the **intersection population** of the candidate and both
  references so reference gaps are same-events comparisons. (Predeclared
  deviation from design §5/A1's shared longest-horizon-candidate population;
  recorded in the design §11 amendment log and the D0 registry batch.)
- **Global holdout**: the final 30% of every dataset must not be loaded,
  inspected, or used in any capacity. The TEST stratum (last 30% of the
  analysis set) is likewise not read by this experiment.
- **Look-ahead bias prevention**: every exit condition is computable at the
  domain-bar close that triggers it from data at or before that timestamp; HA
  values from completed domain bars only; AVWAP/band state is the streaming
  state at that close; events ordered and aligned by timestamp, never bar
  index.
- **Real-price outcome discipline**: HA values may appear only in E1/E2
  trigger conditions; **all fills and all P&L use real domain-bar prices**
  (`Close` of the triggering domain bar; same return basis as EXP-028/030).
  No HA or band construction price ever enters P&L.
- **Exclusions**: TEST and holdout reads; any binding inference or verdict on
  market edge (that is EXP-041); stop-style/intrabar triggers; pyramid-policy
  variation; cost/financing iteration; entry-signal changes; 5m; new-universe
  data; equal-weight pooled verdicts (pooled-with-BTCUSD numbers reported
  descriptively only); any post-hoc addition of exit rules or parameter points.

## Mechanical Selection and Qualification (predeclared; design §5/A1 + §8.1)

1. **Within-grid selection (E3, E5)**: one parameter point per domain by
   max-min worst-half net (chronological TRAIN split-halves), smaller-parameter
   tie-break. Selected before any qualification comparison; full grid disclosed.
2. **Qualification (per domain d, candidate E at its selected point)** — ALL of
   (evaluation population pinned per criterion):
   - (i) per-instrument net point estimate > 0 on every surviving instrument
     of d, computed on the candidate's **own boundary-contained** population;
   - (ii) pooled (event-weighted, surviving instruments) TRAIN net > the better
     reference on the same events (4h: max(R-FH, R-BTC); 1h: R-BTC) —
     **intersection population**;
   - (iii) split-half stability: pooled net > 0 (**own-contained**) and the
     reference gap (**intersection**) keeps its sign in both chronological
     TRAIN halves.
3. **Ranking and cap**: qualifiers ranked by max-min worst-half net
   **recomputed on the within-domain qualifier-intersection population**
   (events contained under every qualifying candidate of d and the applicable
   references), so cross-candidate ranking is a same-events comparison; the
   per-candidate-population numbers are disclosed alongside, and any rank
   reversal between the two computations is flagged and **escalates to
   operator adjudication before the EXP-041 freeze**. Tie-breaks: fewer
   parameters, then shorter mean holding time. **At most 2 exits per domain
   reach G1 consideration; at most 2 total (across both domains) may enter
   EXP-041.**
4. **Hard no-promotion rule**: this experiment emits the qualifying set and the
   frozen candidate descriptions only. No TEST read, no analysis-set verdict,
   no edge claim.

## Success / Failure Criteria

This is a diagnostic screen; "success" is delivering the measurement, not a
positive result.

- **QUALIFIED**: ≥1 (exit, domain) cell passes the §8.1 rule above with all
  required disclosures → EXP-041 activates for the capped qualifying set.
- **FLAT**: no cell qualifies → Track A is FLAT; EXP-041 slot unused; the
  design §9 EXIT_FLAT consequence applies.
- **INCONCLUSIVE (cell-level)**: a cell whose containment-surviving event count
  is below the predeclared reportability floor (same floor convention as
  EXP-030: cells with n < 30 events are descriptive-only and cannot qualify)
  is reported but cannot qualify or be declared beaten-by-reference.
- The screen as a whole is **FAILED** only on integrity grounds: reference
  reproduction mismatch (see Data Requirements), holdout/TEST contact, or
  non-deterministic replay.

## Power / Fragility Statement (mandatory before any read)

4h TRAIN holds roughly 90 events per surviving-instrument set (EXP-033
disclosure); per-event net dispersion is ~60–70 bps (EXP-030/032). Reference
gaps of less than roughly one bootstrap SE on this base are not stably
selectable — hence the split-half filter and max-min ranking. The
implementation must compute and report per-cell minimal detectable nets from
the realized bootstrap dispersions **before** the qualification table, and the
report must state which cells were structurally incapable of qualifying.

## Complexity Budget

- Max statistical tests: 0 binding (bootstrap SEs/CIs descriptive only)
- Max visualisations: 5 (per-domain net-by-exit forest plot; reference-gap
  split-half stability plot; holding-time distributions; containment/exclusion
  accounting; E3/E5 grid curves)
- Max new code modules: 2 (`xen.exit_rules` exit-rule library; screen
  orchestration under `code/`)

## Data Requirements

- 1-minute Parquet under `data/timebars/` for the four instruments; lazy scan,
  `CloseTime` sort, analysis slice then TRAIN slice before any collection.
- Domain aggregation and event generation must reproduce the EXP-028/030 event
  population on TRAIN: a **reference reproduction guard** asserts the R-BTC
  per-event net on TRAIN matches the EXP-030 TRAIN-stratum values (and R-FH(12)
  matches the EXP-033/037 contained-TRAIN values) within numerical tolerance
  before any candidate exit is evaluated. Mismatch = hard stop.
- HA candles generated from domain bars by `xen.heiken_ashi_generator`
  (deterministic; no parameters).
- Deterministic replay: a fixed-seed rerun must reproduce all binding tables
  byte-for-byte.

### Standard Loading Pattern

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob("timebars/timebars_<SYMBOL>_*.parquet"))[-1]

scan = pl.scan_parquet(path).sort("CloseTime")
total_rows = int(scan.select(pl.len()).collect().item())
analysis_cutoff = int(total_rows * 0.7)
train_rows = int(analysis_cutoff * 0.7)
bars_train = scan.slice(0, train_rows).collect()   # TRAIN only; TEST never read
```

## Suggested Direction

Reuse the EXP-030/037 event-evaluation pipeline wholesale: generate the event
substrate once per instrument×domain on TRAIN, evaluate each exit rule as a
pure per-event function over the shared substrate (one pass, `tqdm` over
instrument×domain×exit), charge frozen costs+financing identically, and emit
one tidy table feeding both the qualification logic and the plots. The exit
rules belong in a small reusable `xen.exit_rules` module with streaming-
compatible, bar-close semantics so EXP-041 (and any future cTrader port)
consumes the identical definitions.
