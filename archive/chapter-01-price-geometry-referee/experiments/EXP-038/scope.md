# Experiment: EXP-038 — EURUSD-4h A1-Cell TEST-Stratum Temporal-Stability Subsample Check (one-shot)

**Registry ID:** `CF-AVWAP-001/HYP-004-TI-TEST` (one-shot TEST-stratum
**temporal-stability subsample check** of the registered HYP-004-R baseline estimand
for the A1 strict-pass cell; **0 candidate slots**, registered within Tier B per
design §8.4 as amended F02; relabeled per R1.7).
**Honest framing (R1.7):** this is NOT an independent out-of-sample confirmation.
The cell was selected by D0's rule on EXP-030 **full-analysis** disclosures and
passed EXP-034 on the **full analysis set** — both computations already include the
TEST stratum (~30% of the EXP-034 estimate). The TEST read is therefore a dependent
subsample of the data that both selected the cell and produced the pass: it adds
real stratum-level freshness (this subset was never isolated or read alone) but is
weaker evidence than "out-of-sample" implies. The sealed holdout remains the only
disjoint final arbiter; TRAIN is the only disjoint complement inside the analysis
set, hence the nomination precondition below.
**Revision R1 (2026-06-10, pre-execution, before any TEST read — design §11):**
phase-level G2 Holm family (R1.1); pre-TEST synthetic-null calibration with binding
margin (R1.2); relabel + TRAIN-consistency nomination precondition + LOCO fragility
diagnostic (R1.7).
**Phase:** 008 (`docs/experiments-docs/checkpoints/2026-06-10-008-avwap-clinical-tradability/design.md`, §8.4, §3).
**Gate provenance:** EXP-034 A1 strict pass — EURUSD-4h `SEQUENCE_PASS_ALPHA05`
(net +11.77 bps, one-sided CI_low +3.90, boot_p 0.009). Per §8.4 (F02) an A1 strict
pass is **necessary-but-not-sufficient** for holdout: it routes EURUSD-4h into this
one-shot TEST read. See `G1-gate-review.md`.
**Depends on:** EXP-034 (A1 strict pass + frozen cost/financing layer + inference tail),
EXP-030 (frozen costs, population partition), EXP-027 (frozen inference tail, hash
`e50873d12a9f68d9`), EXP-022/020 (event population + triggers).

## Hypothesis

On the **held-back TEST stratum** (last 30% of the analysis set), EURUSD-4h retains
positive **net** per-event expectancy (the **same registered baseline estimand** as
EXP-034 — BTC exit, pyramids included, frozen CONSERVATIVE cost + financing):
net one-sided 95% lower bootstrap bound > **m** (the R1.2 calibrated margin) AND
raw bootstrap p ≤ 0.05 entering the **phase-level Holm family** (R1.1: this cell +
EXP-037's realized cells; adjudicated in the checkpoint's `G2-gate-review.md`).

## Question

Does EURUSD-4h's A1 strict pass — which selected its cell from EXP-030 disclosures and
tested on the full analysis set — remain temporally stable on the stratum that
EXP-034 did not isolate? This is the only evidential step that can lift EURUSD-4h
from `A1_STRICT_PASS_TEST_CONFIRMATION_REQUIRED` to G2-eligible, while honestly a
dependent-subsample check rather than an independent confirmation (R1.7).

## TRAIN/TEST discipline (LOCKED — design §3, §7.3)

Nested split inside the **analysis set** (first 70% of full data; global holdout =
final 30%, never touched):

- **No TRAIN fitting:** the baseline estimand has no free parameters — nothing is
  selected or tuned on TRAIN. The "freeze-before-TEST" requirement is therefore
  satisfied by construction; the registered estimand definition is the frozen object.
- **TEST** = last 30% of the analysis set, evaluated **exactly once**. Honest caveat
  (design §3): the aggregate full-analysis EURUSD-4h result is known from EXP-030/034,
  but the EURUSD-4h **TEST-stratum subset has not been isolated or read before** — this
  read is fresh at the stratum level.
- **Stratum membership (predeclared, causal):** an event is in TEST iff its
  **entry-confirmation (trigger) timestamp** falls in the TEST window (last 30% of the
  analysis set). Known at entry; no look-ahead. Lifetimes may extend past the boundary;
  the membership key is the entry bar.

## Scope Boundaries

- **Data Views:** EXP-022 `results/lifetime_observations.csv` (`role = event`,
  `reportable_event = true`); EXP-020 `results/avwap_events.csv` triggers; rebuilt 4h
  domain series (EXP-031-identical) for stratum timestamps. **EURUSD-4h only.**
- **Parameters (all FROZEN — identical to EXP-034, no re-derivation):**
  - RT cost CONSERVATIVE: EURUSD 3.0 bps.
  - Financing, adverse-side: EURUSD 0.6 bps/calendar-day, charged
    `0.6 × elapsed_calendar_days(trigger, completion)` (fractional days; same rule as
    EXP-034). **No post-result iteration of any cost component.**
  - Inference: frozen EXP-027 regime-cluster bootstrap (1000 resamples) + one-sided
    bootstrap p, pinned hash `e50873d12a9f68d9`.
  - **Exit rule: the registered baseline BTC (band-target/trend-change) exit** — this
    is a confirmation of the *same* estimand EXP-034 passed, NOT the FH variant
    (that is EXP-037). Pyramids included exactly as in EXP-030/034.
- **Time range:** analysis set; TEST stratum read once. Global holdout never loaded.
- **Real-price outcome discipline:** `lifetime_bps` are real-OHLC (EXP-022 provenance).
- **Look-ahead prevention:** stratum membership keyed on the causal trigger bar; no
  post-completion data in any per-event net.
- **Exclusions:** no FH/exit variant (EXP-037); no conditioning strata; no other
  instruments or domains; no cost-model change; no TRAIN read of EURUSD-4h beyond
  (a) the partition itself, (b) the R1.2 calibration's mechanical TRAIN-dispersion
  inputs, and (c) the predeclared non-binding transparency disclosures; no holdout;
  no re-read of TEST after the verdict (the in-run LOCO/seed-robustness diagnostics
  are part of the single predeclared read).

## Estimand and procedure (LOCKED)

- **Estimand:** event-weighted mean of `net_e = lifetime_bps_e − 3.0 − financing_e`
  over EURUSD-4h **TEST-stratum** events (pyramids included; identical per-event net
  definition to EXP-034).
- **Binding TEST rule (G2-strict, design §8.4 as amended R1.1/R1.2):** **net
  one-sided 95% lower bootstrap bound > m** (the calibrated margin, frozen before
  the read) **AND raw bootstrap p ≤ 0.05 surviving the phase-level Holm family**
  (this cell + EXP-037's realized cells, ≤ 4 members; if EXP-037 freezes
  `B2_NO_ROBUST_HSTAR` the family is this single test). This experiment emits the
  raw p and a **provisional** flag; the final `A1_CELL_TEST_PASS` exists only in
  the checkpoint's `G2-gate-review.md`. No `g2_satisfied` flag is emitted here.
- **Pre-TEST null calibration (R1.2, PREDECLARED):** before the TEST bootstrap,
  calibrate the frozen method at the cell's structure — TEST entry attributes
  (direction, regime-cluster sizes) + TRAIN-stratum dispersion (method-of-moments
  σ_b/σ_w from demeaned TRAIN nets); R = 2000 zero-mean Gaussian cluster-model
  replicates scored by the frozen 1000-resample bootstrap. Persist (before the TEST
  read) the measured small-n FPR and the binding margin
  `m = max(0, Q95 of null ci_low_1s)`. Mechanical; no post-result iteration.
- **Descriptive label** (non-binding) from the two-sided 95% CI: EVIDENCE_FOR /
  EVIDENCE_AGAINST / INCONCLUSIVE_SPANS_ZERO.
- **Zero-baseline:** baseline is exactly 0 bps net; absolute bps only.
- **LOCO fragility diagnostic (R1.7, accompanies — never gates):** for each TEST
  regime cluster, drop it and recompute `ci_low_1s` (frozen bootstrap, deterministic
  seeds); disclose whether the margin-adjusted bound survives every drop. Must
  accompany any provisional pass.
- **Nomination precondition (R1.7):** the operator may nominate this package for
  the one-shot holdout only if the non-binding TRAIN-stratum net point estimate is
  also > 0 (directional consistency on the only disjoint complement).
- **Integrity guards (must pass before the TEST verdict):** (1) TRAIN∪TEST EURUSD-4h
  event counts reconcile **exactly** to the EXP-030/034 full-analysis EURUSD-4h count
  (39) — no dropped/duplicated events; (2) the per-event net definition reproduces
  EXP-034's to ≤ 0.01 bps on any overlapping event; (3) frozen-tail hash pin verified;
  (4) same-seed determinism replay; (5) the TEST partition (member event IDs) **and
  the calibration margin** are written to disk before the TEST bootstrap is computed;
  (6) **no-second-read guard:** the TEST inference refuses to run if
  `test_inference.csv` already exists; a rerun after a post-partition crash must
  reproduce the persisted partition exactly (R1.6 recovery semantics).

## Predeclared power statement (mandatory)

EURUSD-4h has 39 events in the full analysis set; the TEST stratum (~last 30% by
trigger time) holds **~12 events**. With the EXP-030 4h dispersion (per-event SD large
relative to the mean), a 12-event one-sided bootstrap is **power-limited**: a clean
pass requires the TEST-stratum mean to remain well clear of zero. The honest
expectation is that `INCONCLUSIVE_SPANS_ZERO` is a likely outcome and is **not** an
experiment failure — it means the A1 pass could not be confirmed at the stratum level
at this sample size, and the holdout stays sealed (G2 not satisfied via this route).
A pass is the optimistic case; the experiment's value is that it is the only fresh
stratum-level read available before the holdout (an honest but **dependent**
subsample check — R1.7).

## Success / Failure Criteria

- **Evidence FOR (phase-binding, adjudicated in `G2-gate-review.md`):**
  `A1_CELL_TEST_PASS` (one-sided CI_low > m AND phase-family Holm p ≤ 0.05) →
  satisfies strict G2 → EXP-032 holdout-release checkpoint becomes admissible for
  the EURUSD-4h baseline package, **subject to the TRAIN-consistency nomination
  precondition** (operator selects one package if multiple G2 passes exist across
  EXP-037/038 — noting the two routes share nearly the same EURUSD-4h events and a
  joint pass is NOT independent corroboration). This run records a provisional flag
  only.
- **Evidence AGAINST:** net CI_high < 0 on TEST.
- **Inconclusive:** TEST CI spans zero (power-limited; expected per the statement) →
  recorded `A1_STRICT_PASS_TEST_CONFIRMATION_FAILED`; holdout stays sealed.

## Complexity Budget

- Statistical test families: 1 (regime-cluster bootstrap CI + one-sided p, one cell;
  the R1.2 null calibration and R1.7 LOCO are verification/fragility machinery of
  the same frozen family — synthetic data and predeclared subsets, not new tests).
- Visualisations: 2 (TEST-stratum per-event net distribution with CI vs zero;
  full-analysis vs TRAIN vs TEST EURUSD-4h net comparison for transparency).
- New code modules: 0 — reuse the EXP-034 cost/financing/bootstrap path unchanged;
  the new logic is the trigger-time stratum partition plus the predeclared
  calibration/LOCO routines inside the orchestration script.

## Data Requirements

Identical event provenance and per-event net machinery as EXP-034, restricted to
EURUSD-4h and partitioned by trigger timestamp into TRAIN/TEST. The TEST member set is
persisted before any outcome statistic is computed (guard 5).

### Standard Loading Pattern

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob("timebars/timebars_*.parquet"))[-1]

scan = pl.scan_parquet(path).sort("CloseTime")
total_rows = int(scan.select(pl.len()).collect().item())
analysis_cutoff = int(total_rows * 0.7)          # global holdout never read
train_cutoff = int(analysis_cutoff * 0.7)        # TRAIN/TEST boundary on the analysis set
# EURUSD-4h events with trigger time in analysis rows [train_cutoff, analysis_cutoff)
# constitute the one-shot TEST stratum; read once, after the partition is persisted.
```

## Suggested Direction

This is the thinnest possible experiment: take EXP-034's EURUSD-4h pipeline verbatim,
add a trigger-time partition, and run the identical bootstrap on the TEST subset once.
The reconciliation guards (counts to 39; net to ≤ 0.01 bps) ensure the only difference
from EXP-034 is the sample restriction — making this a clean stratum-level
temporal-stability read of the same estimand (a dependent subsample, not an
independent out-of-sample confirmation — R1.7).
