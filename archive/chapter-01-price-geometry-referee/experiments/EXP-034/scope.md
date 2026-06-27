# Experiment: EXP-034 — Per-Instrument Cost-Bearing Tradability Screen (with Financing)

**Registry ID:** `CF-AVWAP-001/HYP-004-TI` (per-instrument estimand of the registered
HYP-004-R baseline + frozen cost layer; 0 candidate slots).
**Phase:** 008 (`docs/experiments-docs/checkpoints/2026-06-10-008-avwap-clinical-tradability/design.md`, §5/A1).
**Depends on:** EXP-030 (frozen cost model + per-instrument disclosures), EXP-028/022
(event population), EXP-027 (frozen inference tail), D0 memo §1 (declared family +
fixed-sequence procedure).

## Hypothesis

Under the frozen EXP-030 CONSERVATIVE cost model **plus the predeclared financing
layer**, the faithful selective AVWAP strategy retains positive **net** per-event
expectancy on **EURUSD-4h** (primary declared cell) on the full first-70% analysis
set, at **one-sided α = 0.05** under the fixed-sequence procedure. The binding
operationalization (clarified 2026-06-10, F01, pre-execution): **one-sided 95%
lower bootstrap bound (5th percentile) > 0 AND one-sided bootstrap p ≤ 0.05** —
the two agree up to percentile interpolation; the two-sided 95% CI is reported
descriptively for EXP-030 comparability and is NOT the binding bound (its 2.5th
percentile would be an undeclared one-sided 0.025 test). Secondary declared cells
(USTEC-4h, XAUUSD-1h) are tested only in sequence.

## Question

Does any individual instrument×domain cell carry a tradable net edge that the
EXP-030 equal-weight aggregate masked — formally, with FWER control, and with
duration-bearing financing included?

## Scope Boundaries

- **Data Views**: EXP-022 `results/lifetime_observations.csv`, `role = event` rows
  only (the EXP-028/030 PRIMARY population, pyramids included); EXP-020
  `results/avwap_events.csv` for trigger timestamps; rebuilt 5m/1h/4h domain series
  (EXP-031-identical rebuild) for completion-bar timestamps.
- **Parameters (all FROZEN before measurement):**
  - Round-trip costs, CONSERVATIVE binding: EURUSD 3.0 / USTEC 5.0 / XAUUSD 6.0 /
    BTCUSD 16.0 bps (EXP-030 values, unchanged).
  - Financing rates, adverse-side, per calendar day: EURUSD 0.6 / USTEC 1.2 /
    XAUUSD 1.2 / BTCUSD 10.0 bps. Charged per event as
    `rate_i × elapsed_calendar_days(trigger_time, completion_time)` with fractional
    days from rebuilt-series timestamps (weekends/closures included; triple-swap
    averaged into the daily rate). These rates are operator-amendable **until this
    scope is approved**; frozen thereafter — no post-result iteration of any cost
    component.
  - Inference: frozen EXP-027 regime-cluster bootstrap (1000 resamples) + one-sided
    bootstrap p (the EXP-030 absolute-estimand substitution; sign-permutation remains
    invalid here), pinned hash `e50873d12a9f68d9`.
- **Instruments**: all four loaded for disclosure; **verdict-grade testing only on
  the D0-declared family** {EURUSD-4h, USTEC-4h, XAUUSD-1h}.
- **Time range**: full dataset with nested chronological split. First 70% = analysis
  set — **this experiment uses the full analysis set** (same population as
  EXP-028/030; this is a verdict-grade screen of the registered baseline estimand,
  not a TRAIN-only characterisation). Final 30% = global holdout, never used.
- **Global holdout**: must not be loaded, inspected, or used in any capacity.
- **Look-ahead bias prevention**: every input to the per-event net is determined by
  the event's own lifetime (trigger → completion); no post-completion data is used.
- **Real-price outcome discipline**: `lifetime_bps` outcomes are real-OHLC returns
  (EXP-022 provenance); no synthetic prices in scope.
- **Exclusions**: no cross-instrument aggregation as a binding metric (that was
  EXP-030 and is not re-litigated); no TRAIN/TEST sub-splitting; no conditioning or
  strata (EXP-035); no exit/pyramid variants (EXP-037); no parameter changes to the
  strategy; no alternative cost models; no holdout.

## Estimand and procedure (LOCKED)

- **Per-cell estimand:** event-weighted mean over the cell's events of
  `net_e = lifetime_bps_e − RT_cons_i − financing_e`. Denominator = number of
  `role = event` rows for that instrument×domain in the analysis set (pyramids
  included; identical event sets to EXP-030 — counts must reconcile exactly:
  EURUSD-4h 39, USTEC-4h 36, XAUUSD-1h 207).
- **Fixed-sequence test (D0 §1.2):** (1) EURUSD-4h at one-sided α = 0.05 — binding
  rule: one-sided 95% lower bootstrap bound (5th percentile) > 0 AND bootstrap
  p ≤ 0.05; if PASS, (2) USTEC-4h; if PASS, (3) XAUUSD-1h. Stop at first failure.
  FWER = 0.05.
- **Per-cell verdict labels:** a tested cell that passes the binding rule is
  `SEQUENCE_PASS_ALPHA05`; otherwise its descriptive label from the two-sided 95%
  CI — `EVIDENCE_FOR` (CI_low > 0), `EVIDENCE_AGAINST` (CI_high < 0),
  `INCONCLUSIVE_SPANS_ZERO` (spans) — applies; cells not reached by the sequence
  carry `NOT_TESTED_SEQUENCE`.
- **Zero-baseline behavior:** the comparison baseline is exactly 0 bps net; no
  percentage-of-baseline metrics anywhere. All effects in absolute bps.
- **Integrity guards (all must pass before verdicts):** (1) the no-financing net per
  declared cell reproduces EXP-030 `net_by_instrument.csv` to ≤ 0.01 bps; (2) event
  counts match EXP-030 exactly; (3) frozen-tail hash pin verified; (4) same-seed
  determinism replay.

## Predeclared power statement (mandatory, design §5/A1)

From EXP-030 bootstrap dispersions (pre-financing CI half-widths):

| Cell | n | Half-width | Expectation under financing (predeclared, honest) |
| --- | --- | --- | --- |
| EURUSD-4h | 39 | ≈ 9.4 bps | The live cell: pre-financing CI_low +2.67; financing on multi-day 4h holds ≈ 1–2 bps ⇒ pass/fail genuinely undetermined. |
| USTEC-4h | 36 | ≈ 27.9 bps | Cannot resolve a ≈ +10 bps point; expected `INCONCLUSIVE_SPANS_ZERO`. Declared by the mechanical rule, not by power. |
| XAUUSD-1h | 207 | ≈ 4.9 bps | Point ≈ 0 pre-financing; financing pushes negative; expected fail. |

A USTEC-4h INCONCLUSIVE or XAUUSD-1h fail is an expected outcome, not an
experiment failure. The phase-level G2 consequence depends on EURUSD-4h alone in
practice.

## Success / Failure Criteria

- **Evidence FOR (cell-level):** declared cell passes the fixed-sequence binding
  rule → **A1 strict pass**. Per design §8.4 as amended 2026-06-10 (F02), this is
  **necessary-but-not-sufficient** for holdout release: A1 selects its family from
  EXP-030 disclosures and tests on the same analysis data, so the pass routes the
  cell into a one-shot Tier-B TEST-stratum confirmation (same registered baseline
  estimand on the held-back TEST segment; 0 new slots); only that TEST result can
  satisfy G2 and make EXP-032 admissible.
- **Evidence AGAINST (cell-level):** net CI_high < 0.
- **Inconclusive (cell-level):** CI spans zero (power-limited cells expected per the
  power statement).
- **Lenient continuation (G1, design §8.2):** any declared cell with net point > 0
  and CI not entirely below 0 continues to Tier-B/G2 consideration even without a
  strict pass.

## Complexity Budget

- Max statistical test families: 1 (regime-cluster bootstrap CI + one-sided
  bootstrap p — one family applied per cell in sequence).
- Max visualisations: 3 (per-cell net with CI vs zero line; financing-impact
  waterfall per declared cell; all-12-cell descriptive map).
- Max new code modules: 1 (orchestration script reusing the EXP-030 cost-overlay
  pattern plus a financing helper).

## Data Requirements

Lifetime observations filtered to `role = event` and `reportable_event = true`
(same filter as EXP-030 — verify via the count reconciliation guard). Completion
timestamps from the rebuilt domain series at `completion_idx`; trigger timestamps
joined from `avwap_events.csv`. Events lacking a completion bar inside the analysis
set follow EXP-030's handling exactly (whatever EXP-030 did with open-ended
lifetimes is reproduced unchanged — the reconciliation guard enforces this).

### Standard Loading Pattern

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob("timebars/timebars_*.parquet"))[-1]

scan = pl.scan_parquet(path).sort("CloseTime")
total_rows = int(scan.select(pl.len()).collect().item())
analysis_cutoff = int(total_rows * 0.7)
bars = scan.slice(0, analysis_cutoff).collect()  # holdout never read
```

## Suggested Direction

This is a thin, deterministic overlay on existing artifacts: join timestamps,
compute per-event financing, subtract, bootstrap per declared cell, walk the
sequence. The only genuinely new computation is the financing duration; everything
else must reconcile bit-for-bit (counts) or to ≤ 0.01 bps (no-financing net) with
EXP-030 before any verdict is read.
