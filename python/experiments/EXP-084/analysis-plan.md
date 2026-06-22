# Analysis Plan: Experiment EXP-084 — AVWAP-4h Portfolio Confirmation Read (CF-CAPGEO-001 Phase 018 / HYP-004b)

**Phase:** 018 · **Mode:** single sanctioned OOS confirmation read, **portfolio unit** · **Reads:** 0 counted
(portfolio-aggregate disclosure) · **Governing:** `scope.md`, `D0-amendment-003`, checkpoint `D0-predeclarations.md`
§D4 (separability + G-018 conjunction) / §D5 (`WF-EXPANDING` + D4.1).

## Objective

Decide whether the **AVWAP-4h portfolio basket** (`SUB-AVWAP` events pooled across NZDUSD-4h + USDCAD-4h +
USTEC-4h, exited by the single pinned parameter-free `AVWAP-FH`, NET of the EXP-085 cost model) **CONFIRMS**
out-of-sample under the frozen `WF-EXPANDING` adjudication + the D4 G-018 conjunction, with the separability
gate S2 — undadjudicable per-cell at n<120 — now binding on the pooled basket. Verdict ∈ {`CONFIRM`,
`NOT_CONFIRM`, `INCONCLUSIVE_SPANS_ZERO`}. The holdout is never touched.

---

## What the "frozen referee suite" IS, operationally (binding clarification)

> **Methodological decision — resolve before implementation.** The D4 conjunction names the "frozen referee
> suite (EXP-003/012/018 + EXP-027/070-analog)". The framework-era suite (`xen.referee_calibration`,
> `xen.incremental_referee`) is denominated in **bps on strategy signals** and is **unit-incompatible** with
> the CF-CAPGEO **ATR-unit event-level** frame. The instantiation **validated for Phase 018** (EXP-077, under
> `WF-EXPANDING`) is the **`xen.wf` aggregate verdict + an FPR-calibrated margin**, not the bps gate stack.
> This plan therefore specifies the binding adjudication as:

**Binding suite = `xen.wf.aggregate_walk_forward(net_returns, rng, kind="block")` → `WFAggregate`, judged by
the EXP-070/077 leg rules in ATR units:**
- **event-level calibration / materiality (EXP-027/070-analog, EXP-077 Leg A):** the pooled-basket WF
  expectancy **`ci_low_1s > m`**, where `m` is the **synthetic-null-calibrated FPR margin** for the pooled
  basket (`xen.capgeo_screen.m_cell_margin` analog computed on the pooled matched-random null; the EXP-070 P9
  condition-4 / EXP-077 Leg-A margin that holds null edge-call FPR ≤ 0.05). *Not* a bare `> 0`.
- **co-primary robustness:** the WF **median `ci_low_1s > 0`** (catches the CF-HA-HARAMI mean/median split).
- **standalone significance:** beats the pooled matched-random basket (next section).
- **portfolio fitness:** the portfolio *is* the unit; the fold-clustered aggregate (one verdict over pooled
  test folds) is the portfolio-fitness read.

`ASS` is **disclosure only** (G-017). If during implementation any EXP-070/077 leg cannot be applied faithfully
to a pooled event series, **stop and route back to the pipeline** — do not substitute the bps gate stack.

---

## Methodology

### Step 0 — Provenance + hash-pin (HALT on failure; before any read)

- Assert EXP-083 valid-set internal sha `fa4035f3…` (re-derive per EXP-083 `_freeze_valid_set`) and the
  EXP-085 cost constants. Record the 6 frozen-module source hashes (`capgeo_screen`/`substrates`/`geometry`/
  `domain_bars`/`capgeo_exits`/`capgeo_cost`) unchanged.
- **Hash-pin the basket definition + binding rule** (instruments, `AVWAP-FH`, cost constants, WF schedule,
  margin rule, conjunction) **before any OOS fold** (D4.1(1) legitimacy). Emit the pin.

### Step 1 — Reproduce + reconcile per-instrument events (TRAIN region, EXP-042 same-denominator)

- For NZDUSD-4h, USDCAD-4h, USTEC-4h: reuse the EXP-083/EXP-085 machinery (the `ass_overlay.py`/EXP-085
  interception pattern) to re-resolve `SUB-AVWAP` × `AVWAP-FH` on the **first-70% analysis TRAIN sub-split**;
  assert `n_resolved` and gross mean reconcile to EXP-085's `cost_readgate` rows within 1e-9 (the TRAIN region
  is the only overlap available for reconciliation). Recover the per-event exit bar (`xen.capgeo_cost`
  `fixed_horizon_exit`, reconciled) and apply the EXP-085 NET cost per instrument (`RT_i`/`F_i`, bar-count
  financing) **before pooling** — so each event's net is in its own ATR units with its own instrument cost.
- Extend the resolution to the **full analysis set** (first 70% of the file) — required for the WF folds.
  Domain bars are built on the first-70% analysis slice only; **the holdout is never built/sliced** (the WF
  caller passes only the in-analysis series — `xen.wf` never sees a holdout fold by construction).

### Step 2 — Pool the basket by event close-time (temporal alignment, not bar index)

- Tag each net event with its **real event close-time** (the AVWAP event trigger/close timestamp, `SourceClose`
  / `CloseTime` of the entry bar — never a bar index). **Concatenate the three instruments' net events and sort
  ascending by event close-time** → one chronological pooled net series `basket_net[]` with an aligned
  `instrument[]` tag. Ties broken deterministically (timestamp, then instrument order NZDUSD<USDCAD<USTEC).
- Pooling is dimensionally valid: all returns and costs are **ATR-normalised**, so the pooled series is in
  consistent ATR units across instruments. (Heterogeneity FX-vs-index is disclosed via the per-stratum leg.)

### Step 3 — TRAIN separability gate on the pooled basket (the key new adjudication)

- Compute S1 ∧ S2 on the pooled basket over the **WF initial-train region** (first 50% of the pooled analysis
  series — strictly pre-OOS-fold, no overlap with any test fold). **Assert pooled n ≥ 120** here (expected
  ≈140–165; if < 120, S2 reverts to deferred+disclosed and the key advance is lost → flag, do not fake it).
- **S1 (attribution):** for the stop-free `AVWAP-FH`, the no-stop reference ≡ the arm itself, so `X_tail ≡ 0`
  by construction (EXP-083 confirmed AVWAP-FH `X_tail=0`). S1 therefore reduces to **`X_fav` (= the arm) beats
  the pooled matched-random control by the margin `m`** — i.e. it coincides with the standalone-significance
  leg, and there is **no stop-truncation artifact to attribute** (a clean property of the pinned arm). Compute
  via `xen.capgeo_screen.two_sample_diff_lo` on the no-stop = full returns vs pooled random, `CI_low > m`.
- **S2 (tail non-residual):** `xen.capgeo_screen.s2_tail_residual` on the pooled-basket **net** TRAIN
  distribution vs the pooled matched-random net distribution; PASS iff `tailmass ≤ τ_tail=0.06` ∧ `q05 ≥
  q05_control − δ=0.40` (frozen `K_tail=3.0`). Disclose the gross-frame S2 alongside (cost is a near-constant
  shift; shape ≈ unchanged).

### Step 4 — Pooled matched-random basket (standalone significance / S1 control)

- Reproduce each cell's EXP-083/085 `SUB-RANDOM` control (same `make_entrysets` random arm, same
  `cell_index`/`SEED_RANDOM`), exit by `AVWAP-FH`, recover exit bars (mirror), apply the **same per-instrument
  NET cost**, tag by event close-time, **pool + sort** identically → `random_net[]`. The basket beats-random
  leg: `two_sample_diff_lo(basket_net_oos, random_net_oos, kind="mean") CI_low > 0` on the pooled WF **test**
  returns (independent samples — different entries).

### Step 5 — One frozen `WF-EXPANDING` run on the pooled basket (binding aggregate)

- `folds = xen.wf.make_folds(n_pooled)` (frozen INITIAL_FRAC=0.50, STEP_FRAC=0.10, N_FOLDS=5, MIN_FOLD=30 —
  do not override). `agg = xen.wf.aggregate_walk_forward(basket_net, rng, kind="block", n_boot=10_000)` →
  `WFAggregate` (pooled-test expectancy/median + one-sided 95% `ci_low_1s`, fold sizes, subfloor folds).
  `kind="block"` (real serially-dependent data) is mandatory — **not** `"iid"`.
- **Counted-read accounting (transparency):** build the `xen.wf.RunSpec` (frozen_before_oos=True,
  between_fold_selection=False, predeclared_aggregation=True, holdout_used_as_fold=False) and record
  `xen.wf.counted_reads` per member stratum — but **the binding ledger entry is the portfolio-aggregate
  disclosure** (operator-ratified, D0-amendment-003 §3): the read makes a **portfolio** claim, no per-stratum
  claim, so it is entered as a **disclosure** against NZDUSD/USDCAD/USTEC-4h — **0 counted reads**, caps stay
  0/2. Record both (the per-stratum `counted_reads` scenario is disclosure context; the governing rule is the
  portfolio-aggregate disclosure).

### Step 6 — Binding verdict (the D4 G-018 conjunction, on the pooled basket)

```
CONFIRM iff ALL:
  (1) suite:        agg.expectancy_lo > m            (FPR-calibrated margin, Step "suite")
  (2) co-primary:   agg.median_lo     > 0
  (3) beats-random: two_sample_diff_lo(basket_oos, random_oos) > 0
  (4) separability: S1_pass AND S2_pass   (Step 3, pooled TRAIN)
NOT_CONFIRM iff (any binding leg fails) AND the failing leg is power-adequate
  (the WF aggregate resolved: n_pooled test ≥ ~2*MIN_FOLD and not all folds subfloor)
INCONCLUSIVE_SPANS_ZERO iff the net co-primary CI spans zero under power-limited pooled TEST n
  (agg.expectancy_lo ≤ 0 ≤ agg.expectancy_hi with subfloor-dominated folds / n_pooled too small)
```

- The verdict is **per the frozen aggregate** (one portfolio unit). `INCONCLUSIVE` is **pre-registered as an
  acceptable, non-failure outcome** (closes HYP-004 at 0 counted reads; not upgradable).

### Step 7 — Determinism + integrity

- Fixed recorded seed; second full pass byte-identical (`determinism_ok`). Assert `holdout_untouched`,
  `test_stratum_touched_in_analysis_only`, `counted_test_reads = 0` (portfolio disclosure), `candidate_slots
  = 0`. Any reconciliation/sha/determinism failure → HALT.

---

## Disclosure legs (non-binding; `binding=false`)

- **Per-stratum net WF reads:** run `aggregate_walk_forward` separately on each instrument's net series
  (NZDUSD / USDCAD / USTEC). Report expectancy/median + CI. **No** binding stratum-specific inference (these
  would be ~n=86–130 each — disclosure only, consistent with the portfolio-aggregate rule).
- **Per-arm net reads:** the other 10 EXP-083 exits on the pooled basket (RR-1/1.5/2/3, D1/D2/D3, PARTIAL-V2A,
  V2A-ADVNONE, VP-POC), pooled-basket net WF aggregate — robustness disclosure (does the basket confirm under
  other exits too?). **No** binding arm-specific inference (arm pinned a-priori = AVWAP-FH).

---

## Output schema

### `results/portfolio_confirm.parquet` / `.csv`

One **binding** row (`binding=true`, `unit="portfolio"`): `n_pooled, n_train_sep, m_margin, exp, exp_lo,
med, med_lo, beats_random_lo, s1_pass, s2_tailmass, s2_q05, s2_q05_control, s2_pass, sep_pass, fold_sizes,
subfloor_folds, verdict ∈ {CONFIRM, NOT_CONFIRM, INCONCLUSIVE_SPANS_ZERO}`.
Plus **disclosure** rows (`binding=false`): per-stratum (3) and per-arm (10) net WF aggregates, and the
**per-fold** WF trajectory (fold index, test window fraction, fold n, fold net exp/med) — the per-fold rows
make the [50–70%] selection-overlap vs the fresh [70–100%] region visible (see Risk 1).

### `results/run_metadata.json`

Frozen constants (basket, `AVWAP-FH`, cost table, WF schedule, `m` rule, conjunction), seeds, module hashes,
EXP-083 sha + EXP-085 cost assertion, hash-pin, reconciliation_ok, determinism_ok, `holdout_untouched: true`,
`counted_test_reads: 0`, `ledger_disclosure: [NZDUSD-4h, USDCAD-4h, USTEC-4h]` (tallies unchanged 0/2),
`candidate_slots: 0`, the portfolio verdict, and the `xen.wf.counted_reads` scenario table (context).

---

## Visualisations (≤ 4)

1. **WF-fold net trajectory** — per-fold net expectancy + CI vs zero across the 5 folds, with the
   **fresh-region marker at the 70% boundary** (so the [50–70%] selection-overlap folds vs the genuinely
   held-back [70–100%] folds are visually separated). *Answers: is the OOS edge in the fresh folds?*
2. **Pooled-basket net distribution** with the S2 tail boundary (`median − K_tail·MAD`) and `q05` /
   `q05_control` marked. *Answers: does the catastrophe tail clear S2 net?*
3. **Per-stratum net disclosure** — NZDUSD / USDCAD / USTEC net expectancy + CI vs the pooled basket.
   *Answers: is the basket carried by one instrument or broad?*
4. **Per-arm net disclosure** — the 11 exits' pooled-basket net expectancy + CI. *Answers: does the basket
   confirm robustly across exits, as EXP-085 suggested?*

All from the bounded result table (no heavy re-load for plotting).

---

## Interpretation Guide (pre-defined, before results)

- **`CONFIRM`** (all 4 binding legs pass with power): the AVWAP-4h capture geometry is **net-tradable
  out-of-sample as a portfolio** — the first programme-level positive confirmation in CF-CAPGEO-001. Read it as
  a **basket** claim (not per-instrument). Disclosed, 0 counted reads; does **not** by itself release the
  global holdout (a separate, governed event). Weight the per-fold disclosure (Risk 1): a CONFIRM driven only
  by the [50–70%] overlap folds is weaker than one carried by the fresh [70–100%] folds.
- **`NOT_CONFIRM`** (a binding leg fails with power): the net edge does not survive OOS as a portfolio →
  HYP-004 closes at G-018, basket disclosed, 0 counted reads. Record the failing leg (most likely: S2 — the
  catastrophe tail is now adjudicable and may FAIL — or the FPR-margin expectancy leg).
- **`INCONCLUSIVE_SPANS_ZERO`** (power-limited): honest, pre-registered, non-failure; closes HYP-004 at 0
  counted reads, non-upgradable. Expected if pooled TEST folds are subfloor-dominated.
- **No per-stratum / per-arm binding claim** is made (LESSON-001 + portfolio-aggregate rule). Those legs are
  disclosure; any cross-instrument heterogeneity they reveal is context for a future scope, not a verdict.

---

## Methodological risks / flags (for developer + governance)

1. **(HIGH) WF test region overlaps the screen's selection region.** The frozen §D5 schedule sets initial
   train = 0.50 of the analysis set, so the WF test folds span [50%–100%], while EXP-083/085 **selected** the
   candidate on [0%–70%]. Folds 1–2 (≈[50%–70%]) are therefore **not fresh** relative to selection; only folds
   covering [70%–100%] are genuinely held-back. **The frozen protocol is not altered** (it was validated
   EXP-077); instead the **per-fold trajectory is disclosed** and the interpreter must weight the fresh folds.
   Flag prominently for governance — this conditions how strong a `CONFIRM` is.
2. **(HIGH) Frozen-suite instantiation.** The binding suite is `xen.wf` + the FPR-calibrated margin (EXP-070/077),
   **not** the bps gate stack. If a leg cannot be applied faithfully to the pooled event series, route back —
   do not substitute. Document the mapping in `run_metadata.json`.
3. **(MED) S2 floor on the pooled TRAIN.** The key advance requires pooled initial-train n ≥ 120. Verify at
   run; if below, S2 reverts to deferred (advance lost) — disclose, do not fake adjudication.
4. **(MED) Pooled FX+index heterogeneity.** The basket mixes FX (NZDUSD/USDCAD) and an index (USTEC) ATR-unit
   events; the portfolio claim treats them as one basket (operator-ratified). Per-stratum disclosure exposes
   any one-instrument dominance; the verdict stays portfolio-level.
5. **(MED) Cost applied per-instrument before pooling** — each event carries its own instrument's `RT_i`/`F_i`;
   never apply one instrument's cost to another's events. Verify alignment of `instrument[]` to `basket_net[]`.
6. **(LOW) Temporal ordering across instruments** by event close-time only (never bar index); deterministic
   tie-break. Holdout never built/sliced/folded.

---

## Implementation safety constraints (for `experiment-developer`)

- TRAIN reconciliation on the first-70% sub-split; full **analysis set** (first 70% of file) for the WF series;
  **holdout never built or passed to `xen.wf`.** `CloseTime`-sorted before slicing.
- Reuse `xen.wf` (folds/aggregate/counted_reads), `xen.capgeo_screen` (one_sided_lo, two_sample_diff_lo,
  m_cell_margin, s2_tail_residual, resolve_fixed_horizon), `xen.capgeo_cost` (cost overlay + exit mirrors).
  ≤1 new module only if pooling/WF orchestration cannot be composed — and it must be pure (no I/O/RNG/selection).
- `kind="block"` in `aggregate_walk_forward` (real data). Fixed seeds; second pass byte-identical.
- Sequential causal scans (exit mirror) stay explicit; cost/pool arithmetic vectorized. No directory creation
  at import. `tqdm` over instruments/arms. Finite handling explicit; reconciliation failure HALTs (no silent drop).

---

## Complexity Check

- **Statistical-method families:** 3 / 3 — (1) `xen.wf` WF-EXPANDING aggregate + FPR-calibrated margin
  (reused); (2) net co-primary one-sided bootstrap (`one_sided_lo`); (3) separability S1/S2 + matched-random
  excess (`s2_tail_residual` / `two_sample_diff_lo`). No new test type.
- **Visualisations:** 4 / 4.
- **New code modules:** ≤ 1 (portfolio pooling + WF orchestration; only if not composable from existing
  kernels). Reuse-first.
