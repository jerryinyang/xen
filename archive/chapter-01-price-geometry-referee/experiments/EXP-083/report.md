# EXP-083 — TRAIN-Only Candidate Screen Behind the Separability Gate (CF-CAPGEO-001 Phase 018 / HYP-004a)

**Status:** COMPLETED · **Date:** 2026-06-22 · **Verdict:** `SCREEN_DELIVERED` (TRAIN-only eligibility — **not** an edge/tradability claim)
**Phase 018** (CF-CAPGEO-001 data-derived exit / capture geometry), checkpoint `2026-06-20-018-capgeo-exit-geometry` · **HYP-004a** (the TRAIN-screen leg of HYP-004 per D0-amendment-001).
**Binding artifacts:** [`results/`](results/) (`screen_results.parquet`/`.csv`, `valid_candidate_set.json`, `run_metadata.json`) · [`results.md`](results.md) · [`audit.md`](audit.md) (binding verdict = the **Re-Audit** section) · [`code/run_experiment.py`](code/run_experiment.py) · new module `xen.capgeo_screen` · [`governance/pre-execution-review.md`](governance/pre-execution-review.md).
**Hand-off (frozen):** `valid_candidate_set.json` **sha256 `fa4035f3…`** + the Holm-over-grid rule — imported verbatim and hash-asserted by the deferred EXP-084.

---

## Research question

On TRAIN data only and gross, which `{exit-candidate × substrate × instrument × domain}` combinations are **valid candidates** — clear the cheap **G-018a** gross screen (positive expectancy + median + matched-random excess) **and** pass the binding **separability gate** (S1 attribution ∧ S2 tail non-residual) — across the 3 frozen data-derived exits (`D1-MEDIAN-CAPTURE`, `D2-TAIL-ROBUST`, `D3-CAPTURE-EFFICIENT`) plus the full enumerated conventional benchmark grid, applied to the frozen-substrate held positions over the 46 EXP-080 member cells? The crux (EXP-082): the derived adverse leg reproduces the CF-HA-HARAMI-001 "harvest the median, leave the catastrophe" geometry, so **S2 is the binding shape-guard** and was expected to be the leg most candidates fail.

## Scope boundaries & exclusions

- **Data:** 5-year post-INFR-003 VAL-005-admitted 1-minute bars → holdout-fenced `build_domain_bars` (`min_coverage=0.90` + analysis-boundary fence). Real OHLC only, ATR units (Wilder ATR(14)). **Read region: TRAIN sub-split `[0, int(analysis_rows·0.7))` only** — the analysis-TEST stratum and the final-30% holdout were never sliced.
- **Substrates (frozen, never tuned):** `SUB-AVWAP`, the harami entry population, `SUB-RANDOM` (matched control). *(See the harami consolidation under Audit history — the two registered harami substrates were screened as one stratum.)*
- **Cost treatment:** GROSS (operator 2026-06-22). The cost-calibrated frozen referee suite was **not** invoked (it binds at EXP-084). `ASS` non-binding (G-017 `DISCOVERY_ONLY`).
- **Exclusions:** no counted TEST read, no TEST-stratum slice, no holdout contact, no `WF-EXPANDING` run, no referee-suite adjudication (all EXP-084); no entry tuning; no barrier grid search; no cross-stratum pooling as a binding statistic (LESSON-001).

## Method summary

Per member cell: build domain bars on the TRAIN slice, generate the frozen substrate entries, resolve each candidate exit's per-event real-price first-touch path (causal, adverse-first P15 fill), then compute — per `{substrate × cell × candidate}` — the G-018a gross legs (moving-block bootstrap one-sided lower bounds; matched-random excess), the **S1** attribution decomposition (`X_full = X_fav + X_tail`; PASS iff the no-stop `X_fav` independently beats the per-cell matched-random control by a synthetic-null-calibrated margin `m_cell`), and the **S2** tail-non-residual legs (post-exit `tailmass ≤ 0.06` ∧ `q05 ≥ q05_control − 0.40` ATR; deferred + disclosed below the `n ≥ 120` floor). Surviving `{candidate × stratum}` are frozen, canonicalized, and sha256-hash-pinned with the Holm rule. Determinism replay byte-identical. Frozen constants `K_tail=3.0, τ_tail=0.06, δ=0.40, EVENT_FLOOR=30`; `derive_barriers` sha256 `34d03f45…` asserted against the EXP-082 pin.

## Key quantitative results

- **`SCREEN_DELIVERED`** — `n_valid = 26` of 2070 `{substrate × cell × candidate}` rows. `determinism_ok = true`, `holdout_untouched = true`, `test_stratum_touched = false`, `counted_test_reads = 0`, `candidate_slots = 0`.
- **The 26 survivors split by the binding shape-guard (read per-stratum, not flat):**

| Group | Count | Cells | n | S2 | Candidates |
|---|---|---|---|---|---|
| **S2-PASS (fully gated)** | **4** | `SUB-HARAMI-V2A × AUDUSD × 1h` (1 cell) | 988 | Evaluated, PASS | `AVWAP-FH`, `RR-1.5`, `RR-2`, `RR-3` |
| **S2-DEFERRED (S2 unadjudicated)** | **22** | `SUB-AVWAP × {NZDUSD, USDCAD, USTEC} × 4h` (3 cells) | 44–78 (<120) | Not evaluated | derived D1/D2/D3 + RR + PARTIAL + VP-POC |

- **All 26 survivors trace to 4 underlying cells.** Breadth is narrow; "26" is candidate-count over strata, not population breadth.
- **98.2% (2033/2070) died at the cheap G-018a gross screen**; the binding separability gate decided only 8 strata (7 fail@S2, 1 fail@S1). The expensive S1∧S2 machinery rarely bound.
- **Mechanism — favourable-capture attribution, not the EXP-082 trap:** all 26 survivors have `x_fav > 0` (min 0.81, mean 1.33 ATR) and `x_tail ≤ 0` (range −0.199…0.0). **Zero** tail-truncation artifacts; the adverse stop subtracts (never manufactures) expectancy.
- **Central finding — the data-derived exits earned no distinctive TRAIN support:** the 4 binding (S2-passed) survivors are all **conventional** arms (`AVWAP-FH`, `RR-1.5/2/3`). The derived `D1/D2/D3` survive **only** in the S2-deferred AVWAP-4h cells (NZDUSD-4h, USDCAD-4h; n≈77), alongside (not in preference to) the conventional arms. On the one cell where S2 actually bound, conventional exits cleared the full gate and the bespoke derived exits did not. **The family's "data-derived beats conventional" thesis is unsupported on TRAIN.**
- **Gate-shape caveat:** the 3 RR S2-passers clear S2 by mechanical stop-truncation-to-point-mass (`tailmass = 0`, `q05_post = q05_control = −MAE_q90 ≈ −7.28 ATR`). S2 certifies "no separated continuous catastrophe mode" but is silent on the −7.28-ATR-per-stop **magnitude** — correctly deferred to EXP-084's cost-calibrated referee suite. `AVWAP-FH` passes S2 on a genuine continuous-tail measurement (`tailmass 0.022`).

## Audit caveats & fix-and-rerun history

The first-pass run (`SCREEN_DELIVERED`, 28 survivors, sha `0796530c…`) was **REVISE**'d on a Critical, verdict-material audit finding:

- **C1 (Critical, fixed):** the two registered harami substrates (`PARTIAL-V2A`, `V2A-ADVNONE`) have byte-identical entries (gross_exp diff = 0.0) yet drew **different** matched-random nulls (control seeded by substrate index), and that control-draw noise alone flipped `AVWAP-FH` between them — changing `n_valid` and the pinned sha256. **Operator-directed fix: dedupe the harami pair to one canonical screened stratum** (`SUB-HARAMI-V2A`; 4→3 screened substrates).
- **W1 (Warning, fixed):** `m_cell` was calibrated once per cell and reused, anti-conservative for the larger-target RR arms. **Operator-directed fix: recompute `m_cell` per candidate** from each arm's own no-stop control reference.

Both fixed and the experiment re-run. **Re-audit PASS** (run `fa4035f3…`): the harami inconsistency is gone, the mechanism is unchanged, and — notably — the per-candidate `m_cell` flipped **no** prior survivor (RR-3 survives correct calibration; one new *deferred* survivor USTEC-4h RR-1 appears). Remaining non-blocking caveat **W2 (VP-POC selection-on-geometry):** `/EXIT-VP` is scored on a geometry-selected subsample; it survives only at USDCAD-4h (deferred, 1 candidate), does not touch the 4 binding survivors, and is carried to EXP-084/parity work.

## Conclusion

**`SCREEN_DELIVERED` — TRAIN-only eligibility, no edge or tradability claim.** Survival is narrow (4 cells) and concentrated, the binding (S2-adjudicated) evidence is a **single well-powered cell** (AUDUSD-1h harami) where only **conventional** exits survive, and the data-derived exits — the actual family hypothesis — earned **no** binding TRAIN support. The mechanism for the survivors is genuine favourable-capture attribution, not the feared tail-truncation trap.

## Disposition / recommendation (operator decision)

Spending a lifetime TEST read is the operator's call at EXP-084's own D0. The screen advises a **weak-to-marginal** case for opening EXP-084: a counted read here would test conventional exits on one cell, not the derived-exit thesis. Two defensible routes:

1. **Decline EXP-084 — close HYP-004 at G-018 on the TRAIN screen, 0 lifetime reads spent** ("data-derived exits do not distinctively beat conventional exits; survival narrow and largely S2-unadjudicated"). Consistent with the falsification-first / file-drawer-control posture; the reserved-conditional EXP-084 exists precisely so this can be declined cheaply.
2. **Ratify a narrowly-scoped EXP-084** on the 4 conventional `AUDUSD-1h` survivors under the pinned Holm rule + the cost-calibrated referee suite — framed as a test of *conventional capture-geometry exits on one well-powered harami cell*, explicitly **not** a vindication of the derived exits. The 22 S2-deferred AVWAP-4h candidates should not anchor a counted read.

Either way the GROSS→cost gap is decisive for the RR arms (magnitude-unpriced −7.28-ATR stop), so any EXP-084 must let the cost-calibrated referee suite bind before any tradability claim. *(A per-event cost layer or a faithful per-event VP profile is a new scope at its own D0, not an extension here.)*

## Signal-registry disposition (registry-relevant — updated in this change)

- **`candidate-families/cf-capgeo-001.md`:** HYP-004a TRAIN-screen outcome recorded — `SCREEN_DELIVERED`; **data-derived exit thesis unsupported on TRAIN** (no derived arm in the binding S2-passed set); eligible set narrow/conventional; **G-018 decision pending operator ratification** of the deferred EXP-084. Family stays `REGISTERED`/SCREENING.
- **`multiplicity-registry.md`:** Phase 018 batch item outcomes recorded (EXP-083 row): the 3 `/EXIT-DERIVED` candidates (`D1/D2/D3`) did **not** survive the binding gate on the well-powered cell → **inconclusive / non-distinctive on TRAIN, retained in the ledger** (never deleted); the benchmark branches `/EXIT-RR` (`RR-1.5/2/3`) and `/EXIT-PARTIAL` (`AVWAP-FH`) produced the 4 binding S2-passed survivors; `/EXIT-VP` 1 deferred survivor (selection-on-geometry disclosed); `/EXIT-TRAIL`, `/SIZE-VOLADJ` no survivors. **Harami slate consolidation recorded:** the two registered harami substrates (`SUB-HARAMI-PARTIAL-V2A`, `SUB-HARAMI-V2A-ADVNONE`) were screened as **one** stratum (entry-identical; fully redundant under uniform candidate application) → harami count consolidated for this screen, history retained.
- **`test-read-ledger.md`:** TRAIN-only screen, **0 counted reads** — a **disclosure, not a counted read** (EXP-074/075/080/081/082 precedent). All 48 strata stay **0/2 open**; ledger tallies unchanged. EXP-083 disclosure entered.

## Follow-up (separate future scopes, not extensions)

- **EXP-084** (reserved-conditional): the counted-read `WF-EXPANDING` confirmation on exactly the `fa4035f3…` valid set under the frozen referee suite — opened only on operator ratification (route 2 above).
- A per-event **cost/slippage + financing layer** (EXP-072/073-analog), and a faithful **per-event VP reference-move profile** (resolving W2) — each its own D0, conditional on a ratified EXP-084.
