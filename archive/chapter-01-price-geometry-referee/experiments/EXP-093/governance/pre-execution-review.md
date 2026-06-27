# EXP-093 — Pre-Execution Governance Review

**Phase:** 021 (CF-MR-001 batch 2) · **Family / HYP:** `CF-MR-001` / `HYP-002` · **Date:** 2026-06-24
**Artifacts reviewed:** [`scope.md`](../scope.md) · [`analysis-plan.md`](../analysis-plan.md) ·
[`code/run_experiment.py`](../code/run_experiment.py)
**Against:** governance-constraints.md · D0 `D0-predeclarations.md` §D6/4c, §D7 · `D0-amendment-006` (carried
set = 11, Holm-11) · `G-021-gate-criteria.md` · active checkpoint `design.md` §4.

---

## Decision

```
VERDICT: APPROVE
```

EXP-093 is the phase's single binding tradability read (the one experiment authorized to spend counted TEST
reads). Scope, plan, and code are mutually consistent, faithful to the frozen D0 + `D0-amendment-006`, and
holdout-safe. One Info note (Holm family-size handling under the unlikely INDETERMINATE branch) is recorded for
the auditor; it cannot move a verdict at the realized counts and does not block execution.

## Phase alignment

EXP-093 is the design §4 terminal confirmation. The only open D0 decision — the exact carried set — was
operator-ratified at `D0-amendment-006` (all 11 EXP-092 `SEQUENCE_PASS` cells; Holm re-sized to 11). No phase
misalignment; no premature work (EXP-090–092 + EXP-094 complete, screen non-empty → TEST authorized).

## Registry precondition (Stage-4 specific) — PASS

- **Family / lever registered & admitted:** `CF-MR-001` `ADMITTED (BINDING)` (G-020); `HYP-002` active; the
  carried exit `EXIT-RCT` is the pinned surviving exit already in the Phase-021 multiplicity batch. **No new
  countable item** (no new variant/detector/parameter branch/candidate). EXP-093 consumes **0 candidate slots**.
- **Scope change recorded:** carrying all 11 (vs the §8.3 "smallest defensible") is a TEST-plan scope change,
  recorded as the dated, operator-ratified `D0-amendment-006` (Holm re-sized to 11). Not silent.
- **TEST-stratum tally stated (mandatory):** scope §2 states all 11 carried strata are **0/2 counted reads,
  open** (active INFR-003 ledger); each goes **0→1**; EURUSD-1h and EURUSD-4h are distinct strata. The 11
  counted reads are recorded in `test-read-ledger.md` in the same change as the result (Stage 7). The Stage-4
  REVISE trigger ("TEST read without stating the stratum tally") does **not** fire.

## Constraint checks

**OOS holdout (REJECT-class if violated) — PASS.** The binding read is the **analysis-TEST stratum** (last 30%
of the first-70% analysis set), explicitly **not** the final-30% global holdout. Code loads `[0,
analysis_cutoff)` only (`load_analysis_1m`); `analysis_cutoff = int(total·0.7)`; the holdout `[analysis_cutoff,
total)` is never sliced (`frame.height == analysis_cutoff` asserted; `holdout_untouched=true`). The TRAIN region
`[0, train_cutoff)` is loaded as causal indicator warmup only — TRAIN entries are filtered out of the binding
estimand (`_test_entries`: domain `CloseTime ≥ ts_lo`), so the counted read is exactly the TEST-stratum events
(ledger definition). The 1m fill clips at the analysis edge (`train_edge_epoch = mce[-1]`, the last analysis
bar) — no 1m row ≥ the holdout boundary enters any walk. Chronological split by `CloseTime`. ✓

**Look-ahead / timestamp alignment — PASS.** Entry selection and the domain→1m fill are by `CloseTime` epoch,
never bar index; exits resolve causally (bars at/after entry within the MR-tempo cap); right-censored events at
the analysis edge are excluded by the `keep` mask. ✓

**Real-price discipline — PASS.** Net expectancy via `net_return_atr` on real touched fill prices and real OHLC,
ATR(14) units; no HA/Renko synthetic prices anywhere. RCT's "model-derived target price" caveat carried (the
fill price is real). ✓

**Single hypothesis / scope boundaries / success criteria — PASS.** One falsifiable question (do carried cells
CONFIRM on TEST under Holm + margin). Concrete D6/4c rule; measurable TRADABLE/NOT_TRADABLE/INCONCLUSIVE
routing; exclusions explicit (holdout, ERT/conventional arms, deferred levers). ✓

**Gate-threshold calibration — PASS.** Margins = the EXP-090/094-calibrated per-cell MDE (data-derived; 1h
0.0125 / 4h 0.025), re-read from upstream artifacts with hard-fail drift assertions. Holm α=0.05 one-sided,
N_BOOT=10_000, BOOT_ALPHA=0.10 — frozen at D0, not magic constants. Cost table from `D0-amendment-003` (hash
pinned, F=0). ✓

**Per-stratum doctrine (LESSON-001) — PASS.** The binding verdict is emitted **per cell** (`test_adjudication.csv`,
per-stratum `verdict`). `experiment_verdict` (`TEST_CONFIRMED/NOT_CONFIRMED/INCONCLUSIVE`) is an explicit
**G-021 routing readout**, not a collapsed binding boolean — it derives from the per-cell verdicts (≥1 CONFIRM →
TRADABLE route) and the per-stratum table remains binding. No pooled statistic is presented as the verdict. ✓

**Shape-aware / robust+raw endpoints — PASS.** The binding gate is the **mean** (location, D5); `net_median`
and `mae_q05` are co-reported (the family's median-fragility shape read). Both the raw economic endpoint (mean
lower bound) and the robust endpoint (median) are emitted per cell; the GBPUSD-1h / mean-carried 1h disclosures
are carried into interpretation. ✓

**No new selection statistic → no bite-check required — CONFIRMED.** The binding gate remains the frozen
estimator family (`xen.ass` moving-block lower bound) + the standard EXP-032/037/038 one-sided bootstrap-p +
Holm confirmation procedure. No novel gate statistic is introduced (D0 §D4; `D0-amendment-006 §5`), so the
bite-check requirement does not apply. Verified: `_mblock_lower_and_p` ci_low is **bit-identical** to
`xen.ass.moving_block_bootstrap_cis(...).expectancy_lo` (same seed), and `boot_p` is drawn from the same
resample stream. ✓

**Method soundness (no academic-finance pitfalls) — PASS.** Moving-block bootstrap preserves serial dependence;
no normality/i.i.d./stationarity assumption; non-parametric throughout. ✓

**Complexity budget — PASS.** 1 binding test + descriptive companions; 4 plots; 0 new modules (substrate reuse;
one in-script analysis-TEST loader). Within D0 §5. ✓

**Code quality / organization — PASS.** Typed public functions; docstrings; VAL-001 sectioning; dirs created in
`run()` only; no import-time side effects (the EXP-090 import is `main`-guarded and reads no data); concise
logging; `tqdm` over the 11 cells; explicit NaN/edge handling (`keep` mask, `n_resolved<2` → INDETERMINATE,
empty entries → INDETERMINATE); no zero-baseline ratio (absolute ATR bounds vs 0 and margin). Lazy Polars scan →
sort → slice → collect; bounded plot inputs from collected summaries. ✓

**Determinism — PASS.** Seeds fixed (`seed_for(EXP-093,...)`, master `20260623`); replay on USTEC-1h +
EURUSD-4h asserts `net_ci_low`/`boot_p`/`n_resolved` frame-identical. ✓

**Provenance pins — PASS.** Code hard-fails on upstream drift (EXP-091 1h net-clear set, EXP-094 4h MEMBER set,
EXP-092 candidate hash `f6427e83…` + membership == the carried 11, per-cell finite MDE, cost-table coverage).
The carried set cannot silently change. ✓

## Info notes (non-blocking; for the auditor)

- **I1 — Holm family size under INDETERMINATE.** `holm_adjust` forms the family from cells with **finite**
  `boot_p`; an INDETERMINATE cell (`n_resolved<2`) is excluded, so the realized family could be < 11 (the metadata
  records `holm.family_size`). At the expected TEST counts (1h ~1600–1700, 4h ~370–470 resolved) INDETERMINATE
  is effectively impossible, so this is immaterial. **Audit action:** if any cell is INDETERMINATE at run time,
  confirm the realized-finite-p family handling did not move any cell across the Holm boundary; otherwise the
  `D0-amendment-006` "Holm-11" intent stands. Adjusting over tests actually performed is standard and the
  conservative direction is already satisfied by the full set when all 11 are powered.
- **I2 — GBPUSD-1h carried though pre-disqualified.** Below its margin already on TRAIN (`clears_margin=false`,
  median −0.052) → a FAIL is the expected, operator-acknowledged outcome (`D0-amendment-006 §2`); its counted
  read is spent regardless. Disclosed in scope §3 and the plan's interpretation guide. Not a defect — the
  per-stratum table and the disclosure carry it correctly into the G-021 read.

## Materiality

No Critical or Warning findings. No verdict-material issue. Proceed to the manual execution gate.
