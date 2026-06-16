# Pre-Execution Governance Review — EXP-055

**Experiment:** EXP-055 — Long-Horizon Availability (Conditioned HA Harami; AVWAP-analog lifetime MFE/MAE)
**Family / item:** `CF-HA-HARAMI-001 / HYP-008` (Phase 014-B lead 3, registered PLANNED)
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`, `code/availability.py`, `code/run_experiment.py`
**Date:** 2026-06-16

---

## Signal-registry precondition (014-B file-drawer control)

- **Registered:** `CF-HA-HARAMI-001/HYP-008 — EXP-055` is in the Phase 014-B batch of
  `multiplicity-registry.md` (line 383, PLANNED); family `REGISTERED`. **No new countable item** is
  introduced — EXP-055 is a diagnostic of the *existing* `/STRONG`-conditioned signal (the EXP-053
  object); no new variant/detector/parameter branch. PASS.
- **Slot/TEST accounting:** 0 candidate slots, 0 TEST reads (characterization/diagnostic per the 014-B
  D0 addendum). **No TEST stratum is read** (TRAIN-only) → the test-read-ledger tally precondition does
  not apply; scope states this explicitly. PASS.
- **Mandatory-reading precondition (Stage-4 REVISE if absent):** `scope.md` records that
  `014-A-conditioning-gap-and-validation-lessons.md` was read and honours all four rules — (a)
  conditioning (the live `/STRONG-STAT` object), (b) harami-anchor, (c) position-in-move descriptive-only,
  (d) excursion (not first-hit `r`) endpoint. PRESENT. PASS.

## Core constraints

- **Simplicity (§1):** reuses frozen primitives + EXP-053 conditioned-signal construction; one new helper
  module; 4 stat tests / 4 plots / 1 module — all at budget. Median + regime-clustered moving-block
  bootstrap is the simplest robust non-parametric choice; justified vs i.i.d. bootstrap and SE-of-median.
  PASS.
- **No academic-finance pitfalls (§2):** non-parametric median + moving-block bootstrap; no
  normality/stationarity/i.i.d./constant-vol assumption; heavy tails handled by the median endpoint. PASS.
- **Strict scoping (§3):** single diagnostic question (availability fork); explicit boundaries (99-cell
  grid, 5m–4h, TRAIN-only, gross, ATR-normalised); mechanical criteria (MOVE_AVAILABLE three legs; P11);
  no scope creep (no capture rule, no costs, no alternative geometries — those are EXP-056–060). PASS.
- **Holdout (§5):** F01 TRAIN-prefix slice (`train_rows = int(int(total*0.7)*0.7)`,
  `scan.slice(0, train_rows)`); full file never sorted/collected; domain bars fenced to
  `CloseTime ≤ train_end_ts`; excursion windows end at the M_b pivot **inside TRAIN** or are
  DATA_CENSORED-excluded; TEST and final-30% holdout never read. PASS.
- **Look-ahead (§6) — reviewed closely:** the lifetime window end `c2` (2nd confirmed ZigZag pivot
  at/after the harami) is future information relative to the harami entry. This is the **sanctioned
  descriptive completed-move grouping**, not a look-ahead violation: it is identical to the approved
  EXP-047/EXP-022 lifetime pattern, explicitly authorized by P19 ("completed-move grouping is the family
  doc's descriptive allowance") and family-doc lines 139–143, and it feeds **only** the descriptive
  MFE/MAE measurement — never an entry, filter, barrier, or any tradable decision. The signal itself
  (harami + live `/STRONG-STAT`) and `M_sofar` use only the confirmed start pivot and the entry-bar close
  (`live_in_progress_state`/`live_strong_stat`, causal as-of on `ConfirmTime`). Excursions read only
  `[e+1, c2]`. PASS.
- **Real-price discipline (§7):** MFE/MAE, ATR(14) divisor, and the reference band all on real domain
  OHLC; HA candles enter only the harami/impulse detectors; no HA price in any metric. PASS.
- **Safe optimization (§8):** lazy F01 scan; bounded per-cell memory; bounded plot inputs collected in the
  analysis pass (no reloads, no mass pandas conversion); `tqdm` over the 99-cell loop; the per-event
  excursion and `/STRONG-HA` loops are genuinely sequential/bounded (variable-span max/min, mirroring
  `move_size.excursions`); fixed per-cell/purpose seeds; determinism replay guard. PASS.

## Reference-line use (operator P19 "never subtracted; reference only") — reviewed closely

The binding MOVE_AVAILABLE leg compares the **median-MFE bootstrap CI_low against the 1.0-ATR line**
(a lower-bound threshold comparison). This is consistent with "never subtracted — reference only":
the line is never deducted from any excursion (gross throughout); it is used as a comparison yardstick,
exactly as EXP-047's `leg2_floor` (`median_MFE ≥ M × floor`) and "≈5–9× the floor" reporting — which
P19 explicitly says to mirror. The 0.5/1.0-ATR multiples are reporting-only. Furthermore, the experiment
**emits** the per-cell map and the AVAILABILITY_* fork label but **does not self-adjudicate** §8 routing
(G2 desk work) — same discipline as EXP-054. PASS.

## Analysis-plan checks

Each method documents "why this method" + "simpler alternative considered" + assumptions; cross-view
alignment by `CloseTime`; plots purposeful; interpretation guide pre-registered (if-X-then-Y, goalposts
fixed); budget compliant (4/4/1). The matched-random baseline wording was aligned to the implemented
EXP-053 matched-count-random construction (the directly comparable P13 baseline; `move_size.matched_controls`'
regime-end window is incompatible with the end-of-M_b lifetime — disclosed, non-binding secondary).
Plan ↔ code consistent. PASS.

## Code / plan compliance

Implements exactly the plan: end-of-M_b window; ATR-normalised rd-aware excursions (floored at 0);
median moving-block bootstrap (reusing the `block_bootstrap_ci` resampling pattern with `np.median`);
median-diff contrast; mechanical readout; 99-cell member grid; EXP-053 population reconciliation
(count + `n_harami`/`stat_retained` match → DEFECT on mismatch); determinism replay + causality guard.
Type hints and docstrings on public functions; explicit NaN/empty/zero-baseline handling
(`<30 → NOT_VIABLE_BY_POWER`, NaN CI → not-available, `None` ratios where undefined); VAL-001-style
sectioning; no import-time side effects; both files byte-compile. PASS.

## Phase alignment

Lead 3 of the 014-B slate (HYP-008, P19), measured before the single G2; no intermediate gate, no
early closure; emits a characterization readout that feeds G2. Consistent with `014-B-design.md`
§4/§5/§8 and the D0 addendum. PASS.

---

```text
VERDICT: APPROVE
```
