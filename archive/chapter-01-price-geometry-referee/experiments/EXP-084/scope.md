# Experiment: EXP-084 — AVWAP-4h Portfolio Confirmation Read of the Net-Surviving Capture Geometry (CF-CAPGEO-001 Phase 018 / HYP-004b)

**Phase:** 018 (CF-CAPGEO-001 data-derived exit / capture geometry; checkpoint
`2026-06-20-018-capgeo-exit-geometry`) · **Registration:** **D0-amendment-003 (operator-ratified
2026-06-22)** — opens the reserved-conditional EXP-084 as a **single AVWAP-4h portfolio confirmation read**,
both gating legs satisfied (leg (a) EXP-085 `NET_SURVIVES`; leg (b) operator ratification). · **HYP:** HYP-004b
— the counted-read confirmation leg of HYP-004, reframed to a portfolio unit. · **Candidate slots:** 0 (the
hash-pinned survivors; no new countable item). · **TEST reads:** **0 counted** — portfolio-aggregate rule
(disclosure against each member stratum; caps preserved).

**Registry precondition (Stage-1 check).** `CF-CAPGEO-001` is `REGISTERED`/SCREENING. The countable item is
the **EXP-084** row in `multiplicity-registry.md` (Phase 018 batch), now `OPENED — portfolio read`
(D0-amendment-003); no new variant/detector/parameter branch is introduced (the binding arm `AVWAP-FH` and the
`SUB-AVWAP` substrate are already registered). **TEST-read ledger (`test-read-ledger.md`):** this read is
entered as a **disclosure** against `NZDUSD-4h`, `USDCAD-4h`, `USTEC-4h` (portfolio-aggregate rule); their
current counted tally is **0/2** and **stays 0/2** (the three become *disclosed*, basket-claim-only, per the
EXP-032 precedent). The EXP-083 valid-set sha `fa4035f3…` and the EXP-085 cost constants are asserted before
any read.

---

## Hypothesis / Confirmation Question

**Confirmation question (one frozen out-of-sample read, NET):** Does the **AVWAP-4h portfolio basket**
(`SUB-AVWAP` events pooled across **NZDUSD-4h + USDCAD-4h + USTEC-4h**, exited by the single pinned
parameter-free rule **`AVWAP-FH`**, NET of the EXP-085 operator-ratified cost model) **CONFIRM** under the
frozen referee suite + the D4 G-018 conjunction, evaluated over one frozen pre-declared `WF-EXPANDING` run
that reaches the analysis-TEST stratum — with the binding pre-TEST separability gate (S1 ∧ S2) now
**adjudicable on the pooled basket** (pooled TRAIN n ≈ 200 ≥ the S2 floor of 120)?

**Falsifiable structure.** The portfolio verdict is one of:

- **`CONFIRM`** — the basket clears the full D4 G-018 conjunction (frozen referee suite PASS on the aggregate
  WF verdict ∧ beats matched-random `CI_low > 0` ∧ separability S1 ∧ S2 PASS on TRAIN) **and** the NET
  co-primary (expectancy ∧ median one-sided `CI_low_1s > 0`) on the pooled basket. Programme-level result:
  *the AVWAP-4h reversal capture geometry is net-tradable out-of-sample as a portfolio.*
- **`NOT_CONFIRM`** — the basket fails ≥1 binding leg with adequate power. HYP-004 closes at G-018; the basket
  is disclosed; 0 counted reads spent.
- **`INCONCLUSIVE_SPANS_ZERO`** — power-limited (pooled TEST n too small to resolve); **pre-registered as an
  acceptable, non-failure outcome** (closes HYP-004 at 0 counted reads). Not upgradable.

This is the single sanctioned out-of-sample contact for HYP-004. It makes a **portfolio** claim only; the
per-stratum and per-arm reads are **disclosure** (no binding stratum-specific inference).

## Question (plain language)

EXP-085 showed the net edge sits entirely in the small, unadjudicated 4h AVWAP cells, robust across exit rule.
Pool those three instruments into one basket, exit them by the simplest parameter-free rule, charge the same
costs, and put the basket to a single honest out-of-sample test under the frozen referee suite — now able to
run the catastrophe-tail separability gate that small per-cell samples blocked. Does the basket hold up?

## Scope Boundaries

- **Data views:** the **5-year, post-INFR-003, VAL-005-admitted** 1-minute time bars → holdout-fenced
  `build_domain_bars` (4h), real OHLC, ATR(14) units, **identical** to EXP-083/EXP-085. The read spans the
  **full analysis set (first 70% of each file)** under `WF-EXPANDING`; the **analysis-TEST stratum** (last 30%
  of the analysis set) is the out-of-sample contact. The **final-30% global holdout is never sliced,
  materialized, inspected, or used** (and is never a WF fold, §D5).
- **Portfolio basket (the binding unit):** `SUB-AVWAP` events on **NZDUSD-4h, USDCAD-4h, USTEC-4h**, **pooled**
  into one event series ordered by event close-time, exited by the single pinned **`AVWAP-FH`** rule. No other
  instrument/domain/substrate enters the basket.
- **Pinned exit (a-priori, frozen before any TEST contact):** **`AVWAP-FH`** (fixed-horizon, parameter-free).
  Pinned on principle per D0-amendment-003 §2 (least-tunable; cross-exit robustness says the arm should not
  matter so pick the simplest; its EXP-083 S2 pass was a genuine continuous-tail pass, not
  stop-truncation-to-point-mass). **Not** selected on net magnitude.
- **Net basis:** NET, carrying the **EXP-085 operator-ratified cost model verbatim** (per-instrument round-trip
  `RT_i` + bar-count financing `F_i`; ATR-unit `net = gross − cost`). No re-derivation or re-tuning of cost
  constants.
- **Binding adjudication:** the **frozen referee suite** (G-017 `DISCOVERY_ONLY` → suite binding; `ASS`
  non-binding disclosure) + the **D4 G-018 conjunction**, over **one frozen `WF-EXPANDING` run** (§D5: initial
  train 0.50 of the analysis set, 5 expanding folds of 0.10, min fold ≥ 30, fold-clustered moving-block
  bootstrap, one aggregate verdict). Separability S1 ∧ S2 re-confirmed on the **pooled-basket TRAIN** (S2 now
  adjudicable at pooled n ≈ 200; frozen `K_tail=3.0, τ_tail=0.06, δ=0.40`, floor n≥120).
- **Disclosure legs (non-binding):** per-stratum net reads (NZDUSD / USDCAD / USTEC individually) and per-arm
  net reads (the other 10 EXP-083 exits on the basket) — reported for transparency, no binding claim.
- **Exclusions:** no holdout contact; no per-stratum or per-arm **binding** claim; no second WF run; no exit
  selection/tuning (arm pinned a-priori); no cost re-tuning; no `ASS` binding leg; no new candidate or
  substrate; no between-fold human selection; the basket and the binding rule are hash-pinned before the OOS
  folds (D4.1 legitimacy condition).

## Predeclared Method (frozen — D0-amendment-003 + checkpoint §D4/§D5)

1. **Pool** the three instruments' `SUB-AVWAP` 4h events (TRAIN region reproduced + reconciled to
   EXP-083/EXP-085 gross within 1e-9), exit by `AVWAP-FH`, apply the EXP-085 NET cost per event.
2. **TRAIN gates on the pooled basket:** G-018a gross + S1 attribution (`X_fav` beats pooled matched-random by
   the synthetic-null margin) + **S2** tail non-residual (post-exit `tailmass ≤ 0.06` ∧ `q05 ≥ q05_control −
   0.40` ATR), now adjudicated at pooled n ≈ 200.
3. **One `WF-EXPANDING` run** over the pooled analysis set → frozen referee suite (materiality / standalone
   significance / portfolio fitness / event-level calibration, EXP-003/012/018 + EXP-027/070-analog, applied
   to the pooled event series as validated in Phase 017) + beats-matched-random, NET, one aggregate verdict.
4. **Binding conjunction (CONFIRM):** suite PASS ∧ beats-random `CI_low>0` ∧ S1∧S2 PASS ∧ NET co-primary
   (expectancy ∧ median) `CI_low_1s>0`, all on the pooled basket.
5. Hash-pin the basket definition + binding rule + cost model before any TEST/OOS fold; freeze seeds; second
   pass byte-identical.

## Success / Failure / Inconclusive Criteria

- **`CONFIRM`:** all four binding legs (§Method 4) pass on the pooled basket with adequate power. Programme
  result: AVWAP-4h capture geometry net-tradable OOS as a portfolio. Disclosed (not counted); does not by
  itself release the holdout.
- **`NOT_CONFIRM`:** ≥1 binding leg fails with adequate power → HYP-004 closes at G-018; basket disclosed; 0
  counted reads. Record which leg failed.
- **`INCONCLUSIVE_SPANS_ZERO`:** the net co-primary CI spans zero under power-limited pooled TEST n →
  pre-registered acceptable outcome; closes HYP-004 at 0 counted reads; non-upgradable.
- **Process-level HALT (not a result):** `fa4035f3…` or cost-constant mismatch; any **holdout** row touched;
  any WF fold reaching the holdout; non-determinism on replay; gross reconciliation failure (re-resolved gross
  ≠ EXP-083 beyond 1e-9). Halts and routes to a fix.

## Complexity Budget

- **Max statistical-method families: ≤ 3** — (1) the frozen referee suite under `WF-EXPANDING` (reused,
  Phase-017-validated); (2) net per-event expectancy + median moving-block bootstrap one-sided `CI_low`
  (reuse `xen.capgeo_screen.one_sided_lo`); (3) the separability S1/S2 legs + matched-random excess (reuse
  `xen.capgeo_screen` S1/S2 + `two_sample_diff_lo`). No new test type.
- **Max visualisations: ≤ 4** — (i) WF-fold net trajectory of the basket (per-fold net expectancy + CI vs
  zero); (ii) pooled-basket net distribution with the S2 tail boundary marked; (iii) per-stratum net
  expectancy disclosure (3 instruments) vs the pooled basket; (iv) per-arm net disclosure (11 exits) on the
  basket.
- **Max new code modules: ≤ 1** under `python/src/xen/` — only if the portfolio pooling + WF-EXPANDING
  application to the event series cannot be composed from existing kernels (`xen.capgeo_screen`,
  `xen.capgeo_cost`, the Phase-017 WF/referee machinery). **Reuse first.**

## Metric Denominators & Zero-Baseline (predeclared)

- **Event denominator:** the pooled basket = the union of the three cells' `AVWAP-FH` resolved events on the
  analysis set (TRAIN reconciled to EXP-083/EXP-085; TEST reached only via WF folds). The cost layer subtracts
  a per-event charge; it never filters the event set.
- **Net expectancy / median:** absolute differences in ATR units (`net = gross − cost`); moving-block bootstrap
  CIs; no percentage-vs-zero-baseline metric. Matched-random excess is a difference under the same cost on
  both arms.
- **Per-stratum / per-arm disclosure:** reported as differences in ATR; explicitly non-binding.

## Frozen Constants (predeclared)

- Pinned arm `AVWAP-FH`; basket = {NZDUSD, USDCAD, USTEC}-4h `SUB-AVWAP`. Cost: EXP-085 `RT_i`/`F_i` table +
  bar-count financing (verbatim). Bootstrap: `N_BOOT = 10_000`, one-sided 95% `CI_low`, moving-block
  `b=max(1,round(m^(1/3)))`. `WF-EXPANDING`: initial 0.50, 5 folds × 0.10, min fold ≥ 30 (§D5). Separability:
  `K_tail=3.0, τ_tail=0.06, δ=0.40`, S2 floor n≥120. Seeds fixed and recorded; second pass byte-identical.
- Provenance: EXP-083 valid-set sha `fa4035f3…` + EXP-085 cost constants asserted; frozen-module hashes
  (`xen.capgeo_screen`/`capgeo_substrates`/`capgeo_geometry`/`domain_bars`/`capgeo_exits`/`capgeo_cost`)
  recorded unchanged.

## Data Requirements

For each of the 3 basket cells: load the 5-year file (latest-glob), slice the first-70% analysis set, build
4h domain bars (holdout-fenced), reproduce the `SUB-AVWAP` entries + `AVWAP-FH` exit (reconcile TRAIN gross to
EXP-083/EXP-085 within 1e-9), apply the NET cost, pool the events by close-time, run the TRAIN separability
gate on the pooled basket, then the one `WF-EXPANDING` frozen-suite run over the pooled analysis set. Emit:

- `results/portfolio_confirm.parquet` / `.csv` — the pooled-basket binding verdict + each leg (suite legs,
  beats-random, S1, S2, net exp/med + CI_low), per-fold WF trajectory, and the per-stratum + per-arm
  disclosure rows (flagged `binding=false`).
- `results/run_metadata.json` — frozen constants, seeds, module hashes, EXP-083 sha + EXP-085 cost assertion,
  reconciliation_ok, determinism replay, `holdout_untouched: true`, `counted_test_reads: 0` (portfolio
  disclosure), `candidate_slots: 0`, the portfolio verdict, and the **disclosure entries** to write to
  `test-read-ledger.md` (NZDUSD/USDCAD/USTEC-4h disclosed, tallies unchanged 0/2).

## Suggested Direction (non-binding)

Reuse the EXP-085 reconciliation + cost overlay machinery to assemble the pooled basket, then apply the
Phase-017-validated `WF-EXPANDING` + frozen referee suite to the pooled event series. Spend the discipline
budget on: (1) asserting `fa4035f3…` + the EXP-085 cost constants + the gross reconciliation before any read;
(2) hash-pinning the basket + binding rule before the OOS folds (D4.1); (3) keeping the holdout sealed and out
of every fold; (4) the determinism replay; (5) honest power reporting (INCONCLUSIVE is acceptable).
