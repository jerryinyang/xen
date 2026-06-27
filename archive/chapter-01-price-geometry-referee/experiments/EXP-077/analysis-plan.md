# Analysis Plan: Experiment EXP-077 — Dogfood + Calibration under `WF-EXPANDING` (`ASS/VAL-002`)

## Objective

Validate the **error-control + protocol** legs of G-017: under the frozen `WF-EXPANDING`
expanding-window walk-forward protocol (D0 §D4), does the `ASS` qualifier (a) control false-positive
edge calls (FPR ≤ 0.05) under a synthetic-null-calibrated margin, (b) deliver a **finite/non-degenerate
MDE** for every `n ≥ 30`, (c) produce **reliable `P(return>X)`** on held-out folds, (d) carry a
**counted-read accounting rule that demonstrably honors the 2-lifetime-counted-reads cap**, and (e) run
end-to-end on **real bars** in a current-data **TRAIN-only** dogfood without touching any TEST stratum
or the holdout — all **deterministically** (byte-identical second pass)?

This experiment changes no market verdict. It decides whether the FPR/MDE/reliability/accounting legs
of `ASS_VALIDATED` hold. Every numeric result is reported **per stratum** (LESSON-001 binding; D0 §8).

**Inherited frozen objects (no re-derivation, no tuning):** the D1 synthetic generators + type
registry and the `xen.ass` qualifier core are reused **unchanged** from EXP-076. New this experiment:
the `xen.wf` protocol module and a **moving-block** bootstrap variant added to `xen.ass` (the `ass.py`
docstring already reserves "the real-data moving-block variant is EXP-077, not here").

---

## Key construction: `WF-EXPANDING` applied to a synthetic stratum

The D4 schedule is expressed in **fractions of an ordered event series**. A *stratum* here is one
`(type, N)` cell: a synthetic return series of total length `N` (from the D1 n-grid), treated as a
chronologically ordered population. `WF-EXPANDING` partitions it (D4):

| Fold | Train | Test |
| --- | --- | --- |
| 1 | [0.00, 0.50] | (0.50, 0.60] |
| 2 | [0.00, 0.60] | (0.60, 0.70] |
| 3 | [0.00, 0.70] | (0.70, 0.80] |
| 4 | [0.00, 0.80] | (0.80, 0.90] |
| 5 | [0.00, 0.90] | (0.90, 1.00] |

- Each **test fold** holds `≈ 0.10·N` events; **min fold size ≥ 30** (D4). Below-floor folds are
  **disclosed, never silently dropped** (a stratum whose folds are all sub-floor is reported as a
  power-limited / small-`n` disclosure, not a clean pass/fail).
- The **stratum verdict** is a single aggregate over the 5 test folds via a **fold-clustered
  bootstrap** (cluster = fold; D4): pool the test-fold returns, point-estimate the shrinkage-weighted
  expectancy/median, and form the 90% CI by resampling **whole folds as clusters** (preserving the
  fold structure, and — for the real dogfood — within-fold serial dependence via moving blocks). This
  yields exactly **one** `(expectancy, expectancy_CI, median, …)` per stratum — the binding unit.
- One full frozen WF run on a stratum = **exactly one** counted read (D4.1); the 5 folds are
  in-protocol disclosures, not separate reads.

This makes the **protocol itself the object under validation**: FPR/MDE/reliability are properties of
the WF-aggregated stratum verdict, not of a single-sample CI.

---

## Methodology

### Step 1 — Synthetic substrate (reuse EXP-076 D1; frozen)

- **Method**: reuse `build_type_registry()` and the `gen_unimodal/gen_skewnormal/gen_bimodal`
  samplers from EXP-076 (lifted or imported), with closed-form moments and MC ground truth.
  **Null types** for FPR: `U0` (μ=0; expectancy & median null) and `B_zero` (mean ≈ −0.015 ≈ 0,
  median +0.15 — used as the **expectancy/mean null** per its leg, per D2.2). **Effect types** for
  MDE: the `U`-location family `{U0,U1,U2,U3}` = μ ∈ {0, 0.05, 0.10, 0.20} gives a clean monotone
  effect ladder; the MDE curve interpolates/extrapolates the smallest μ reaching TPR ≥ 0.80.
- **Why sufficient**: ground truth is known/closed-form, so FPR and TPR are measured against truth
  with no modelling assumption. Non-parametric throughout (bootstrap CIs, empirical rates).
- **Simpler alternative considered**: a single Gaussian null. Rejected — the binding null must include
  the bimodal mean-null (`B_zero`) because the programme's failures were bimodal (retrospective §4.2);
  a Gaussian-only null would not stress the percentile bootstrap the way Phase 018 data will.
- **Assumptions**: synthetic iid draws within a series; the WF chronological partition is applied to an
  exchangeable population (no real autocorrelation) — acceptable because the synthetic leg validates
  the *protocol arithmetic and the estimator's error control*, while the **real-data dogfood** (Step 6)
  exercises genuine serial dependence via the moving-block bootstrap.
- **Expected output**: per-`(type, N)` drawn replicate series; ground-truth table persisted to
  `results/ground_truth.csv` (re-derivable by audit).

### Step 2 — Margin calibration on nulls (resolves the FPR↔MDE circularity)

- **Method** (the `m_cell` analog, D2.2; programme lineage EXP-008/EXP-070/EXP-032): the binding FPR
  rule is `expectancy CI_low_1s > m(N)`. For each null type and `N`, draw `R_REP` **calibration**
  null series (a dedicated RNG stream `TAG_CAL`), run `WF-EXPANDING`, collect the WF-aggregated
  one-sided lower bound `ci_low_1s` under the null, and set
  **`m(N) = max(0, Q95( ci_low_1s | null ))`** — the smallest margin driving the calibration-null
  edge-call rate to ≤ 0.05 at the realized fold-cluster structure.
- **Circularity break (explicit)**:
  1. **`m` is calibrated on NULL types only** (`U0`, `B_zero`) — it never sees any effect type, so it
     cannot be tuned to manufacture power.
  2. **Calibration and validation draws are disjoint.** `m(N)` is fixed on the `TAG_CAL` calibration
     nulls; the **FPR (Step 3) is then measured on an independent `TAG_VAL` null draw** with `m`
     **frozen**. A margin that controls FPR only on its own calibration draw (overfit) is caught here.
  3. **MDE (Step 4) uses the predeclared raw rule `CI_low > 0`, not the margin rule** (D2.3) — a
     deliberately different, simpler detection rule whose gate is *finiteness*, not magnitude. The two
     legs therefore use two predeclared, non-interacting decision rules; `m` is computed once, on
     nulls, before any effect type is scored, and is reported as a result (not a hand-set constant).
- **Assumptions**: the null `ci_low_1s` distribution is stable between the calibration and validation
  draws (tested directly by the independent-draw FPR). No distributional assumption on its shape
  (empirical Q95).
- **Expected output**: `results/margin.csv` — `m(N)` per null type and `N`, with the calibration-null
  edge-rate it achieves.

### Step 3 — FPR under `WF-EXPANDING` (D2.2) — BINDING, per stratum

- **Method**: on the independent `TAG_VAL` null draw, for each null stratum `(type, N)` run
  `WF-EXPANDING` on `R_REP = 2000` series; an "edge call" = WF-aggregated `ci_low_1s > m(N)`.
  **FPR = (# edge calls)/R_REP**; attach a **Wilson 95% upper bound**. PASS iff **FPR ≤ 0.05 and
  Wilson-hi ≤ 0.075** (D2.2).
- **Small-`n` FPR stratum (EXP-076 disposition (b) — mandatory)**: EXP-076 found the percentile
  bootstrap **under-covers the expectancy at `n < 30`**. EXP-077 must show whether that translates to
  FPR inflation. Two sub-reads, reported per `N ∈ {15, 30}`:
  - **(i) single-window** (no folds; direct `ASS` CI on the whole `N`-series) — the direct test of the
    EXP-076 under-coverage → FPR-inflation question;
  - **(ii) under-WF** where the 0.10·N folds are sub-floor and disclosed.
  Outcome is a **per-stratum disclosure to G-017**: either the margin rule still holds FPR ≤ 0.05 at
  `n < 30` (the n<30 guard can relax), or it does not (the EXP-076 "defer to median / no expectancy
  edge-calls at effective n<30" guard stands). Do **not** prejudge — report the rate per `N`.
- **Why sufficient**: FPR is the directly observed false-positive rate against a known null; Wilson
  bounds the Monte-Carlo uncertainty at `R_REP=2000`. No parametric test needed.
- **Simpler alternative considered**: a bare `CI_low > 0` rule (no margin). Rejected at D0 — the bite
  check measured 0.053 (Wilson-hi 0.069) for the bare rule; the margin is the programme's standard
  correction for the percentile bootstrap's mild one-sided inflation.
- **Assumptions**: independent replicate series; null ground truth exact.
- **Expected output**: `results/fpr.csv` — per `(null type, N, sub-read)`: FPR, Wilson-hi, `m(N)`,
  edge-count, `pass`.

### Step 4 — MDE finiteness under `WF-EXPANDING` (D2.3) — BINDING, per stratum (`n ≥ 30`)

- **Method**: for the `U`-location effect ladder, at each `N` measure
  **`TPR(μ, N) = P( WF-aggregated CI_low > 0 )`** over `R_REP` effect-series replicates (raw rule, D2.3).
  `MDE(N)` = smallest μ with `TPR ≥ 0.80`, obtained by monotone interpolation across the μ-ladder
  (and, if the ladder's top μ=0.20 does not reach 0.80, extend the ladder upward by a predeclared
  mechanical step until it does **or** declare the curve degenerate). **PASS iff `MDE(N)` is finite /
  non-degenerate for every `N ≥ 30`** — the gate is finiteness (a never-detecting / degenerate CI is
  the screened failure), not the magnitude. The full `MDE(N)` curve is reported.
- **Why sufficient**: TPR against known effect sizes is the direct power measurement; finiteness is a
  structural property (does the CI ever exclude 0 with ≥80% probability), read straight off the curve.
- **Simpler alternative considered**: an analytic power formula. Rejected — it would assume normality
  of the WF-aggregated estimator, which the bimodal types violate; the empirical TPR is assumption-free.
- **Assumptions**: monotone TPR in μ at fixed `N` (verified empirically; non-monotonicity is flagged,
  not smoothed over).
- **Expected output**: `results/mde.csv` — per `(N, μ)`: TPR; and per `N (≥30)`: `MDE`, `finite` flag.

### Step 5 — `P(return>X)` reliability on held-out folds (D2.4) — BINDING

- **Method**: for `X ∈ {0, 0.05, 1.0, 2.0}`, within each WF fold the **train** portion yields the
  `ASS` shrinkage-weighted **predicted** `P(return>X)`; the **test** fold yields the **realized**
  frequency `mean(test_returns > X)`. Pool `(predicted, realized)` pairs across folds × strata ×
  replicates, **bucket by predicted value into deciles**, and per decile compute mean predicted vs mean
  realized. **PASS iff max |predicted − realized| ≤ 0.10 across deciles AND the calibration-line slope
  ∈ [0.85, 1.15]** (OLS of realized-decile-mean on predicted-decile-mean — a robust diagnostic line,
  not an inferential model; D2.4).
- **Why sufficient**: a reliability diagram is the standard, assumption-free calibration check; the
  slope + max-gap are the two predeclared D2.4 statistics.
- **Simpler alternative considered**: a single Brier score. Rejected — it collapses calibration and
  resolution into one number and hides *where* on the probability axis the qualifier is mis-calibrated
  (the D2.4 deciles localize it).
- **Assumptions**: deciles are populated across the probability range — guaranteed because the type
  span (`U0..U3`, skew, bimodal) and the four `X` thresholds spread predicted `P(>X)` across [0,1];
  thin deciles are disclosed (per-decile `n` reported).
- **Expected output**: `results/reliability.csv` — per `(X, decile)`: predicted, realized, `n`; and
  per `X`: max-gap, slope, `pass`. Reported per `X` (a stratum), not collapsed across `X`.

### Step 6 — Counted-read accounting demonstration (D4.1) — BINDING, per scenario

- **Method**: implement the D4.1 rule as a **pure, unit-tested function** in `xen.wf`
  (`counted_reads(run_spec, ledger_state)`), then drive it through a predeclared scenario table and
  assert expected == actual:
  | Scenario | Expected |
  | --- | --- |
  | Conforming frozen WF run on an open stratum (all D4.1 conds hold) | **+1** counted read; folds = disclosures |
  | WF run with **between-fold human selection** (D4.1 cond 2 violated) | each fold reverts to **+1** (e.g. 5 folds → +5) |
  | Second conforming WF run on a 1/2 stratum | **+1** → at-cap; flagged **weakened-evidence** |
  | Any WF run on an **at-cap (2/2)** stratum | **rejected** — no further stratum-specific claim |
  | **Holdout used as a fold** (D4.1 cond 4 violated) | **rejected / error** |
  | Rolling 1y/2y/3y comparison on already-read folds | **+0** |
  | Non-frozen / not-hash-pinned schedule (cond 1 violated) | folds revert to separate reads |
- **Why sufficient**: the accounting is a deterministic rule, so correctness is a logic/arithmetic
  proof over the exhaustive condition table — the right tool is an assertion suite, not a statistic.
- **Demonstrably honors the 2-read cap**: a simulated multi-run ledger shows a stratum cannot exceed 2
  counted reads and that an at-cap stratum is permanently blocked from stratum-specific confirmation.
- **Expected output**: `results/counted_read_accounting.csv` — per scenario: expected, actual, `pass`.

### Step 7 — Current-data TRAIN-only dogfood (D4.2) — pipeline smoke, **0 counted reads**

- **Method**: load **current** 1-minute bars for the 4-instrument core (EURUSD, XAUUSD, BTCUSD, USTEC),
  lazily slice to the **first-49% TRAIN region** (`train_cutoff = int(int(total*0.7)*0.7)`), build
  **15m/1h/4h** domains via `xen.bar_aggregator` (`min_coverage=0.90`). Construct a **developer-defined
  causal real-price return series** (no market-edge claim): per-bar **forward `H`-bar log return in ATR
  units** on real `Close` (ATR(14) causal denominator), with the final `H` bars dropped (no look-ahead).
  Run `WF-EXPANDING` + `ASS` per `(instrument, domain)` cell with the **moving-block** bootstrap
  (`b = round(fold_len^(1/3))`, D3) within-fold and fold-clustered aggregation.
- **Pass = pipeline integrity, not a numeric edge**: every cell completes; each fold produces finite
  `ASS` scores (expectancy/median/`P(>X)`/CI); the realized fold schedule + per-fold event counts are
  emitted; **0 counted reads** (TRAIN-only); the **first-49% cutoff is asserted in code** (max read
  `CloseTime` < the cutoff timestamp; the next-21% TEST stratum and final-30% holdout are never
  sliced). Sub-floor folds disclosed.
- **Why sufficient**: the dogfood's job is to prove the machinery runs on real bars and respects the
  fence — a procedural integrity check, deliberately carrying no edge claim that could leak selection.
- **Real-price discipline**: returns on real `Close` only; ATR-normalised; **no HA / Renko brick
  prices**. Temporal order by `CloseTime`; no bar-index alignment.
- **Expected output**: `results/dogfood.csv` — per `(instrument, domain)`: n_events (first-49%),
  realized fold sizes, per-fold finite-score flags, ATR/return summary, cutoff-assertion evidence,
  counted_reads = 0.

### Step 8 — Determinism (D6) + integrity anchor

- **Method**: every draw seeded by `SeedSequence([MASTER_SEED, tag, type_id, N, replicate, fold])`
  with disjoint stream tags (EXP-076 pattern). Recompute the cheap point-estimate tables a second time
  and **hash-compare** (sha256 of canonical CSV); the dogfood is re-run and hash-compared too.
  **Integrity anchor (R-anchor)**: on one shared `(type, N)` cell, reconcile the production `ASS`
  expectancy against `numpy.mean` (≤ 1e-12) and against the EXP-076 estimator on the identical seed —
  confirming `xen.ass` is byte-consistent across experiments.
- **Expected output**: `results/integrity.json` — determinism hash matches, anchor diffs, config block.

---

## Visualisations (5 / budget 5)

1. **FPR vs `N` per null type** — `U0`, `B_zero`, with the 0.05 reference line, Wilson-hi whiskers, and
   the calibrated margin `m(N)`; small-`n` (single-window vs WF) sub-reads marked. *Sub-question: is
   FPR controlled at every `N`, including `n < 30`?*
2. **`MDE(N)` curve per type** — MDE vs `N` (log-`N`), finite cells solid / degenerate cells flagged.
   *Sub-question: is MDE finite for every `N ≥ 30`?*
3. **`P(>X)` reliability diagram** — realized vs predicted decile means per `X`, with the y=x line,
   the ±0.10 band, and the fitted slope. *Sub-question: is the qualifier calibrated across the
   probability range?*
4. **`WF-EXPANDING` fold schedule + event counts** — the 5 expanding train/test folds and realized
   per-fold sizes (synthetic representative `N` + dogfood cells), sub-floor folds highlighted.
   *Sub-question: does the protocol realize the predeclared schedule and where do folds fall below
   the ≥30 floor?*
5. **Dogfood pipeline diagnostic** — per `(instrument, domain)` first-49% event count, fold
   completion, and the cutoff-assertion bar (read range vs TRAIN cutoff vs TEST/holdout fence).
   *Sub-question: did the pipeline run on real bars within the fence?*

---

## Interpretation Guide (predeclared — before results)

- **FPR (per null stratum)**: if margin-calibrated FPR ≤ 0.05 with Wilson-hi ≤ 0.075 on `U0`, `B_zero`,
  **and** the small-`n` stratum → error control **holds** for that stratum. If any stratum exceeds it →
  that stratum **fails** (feeds `DISCOVERY_ONLY`); if only the `n < 30` stratum exceeds it → the
  EXP-076 "no expectancy edge-calls at effective n<30 / defer to median" guard **stands** (a bounded,
  per-stratum disclosure, not a whole-qualifier failure).
- **MDE (per `N ≥ 30`)**: if `MDE(N)` is finite for every `N ≥ 30` → detection is non-degenerate
  (PASS). A degenerate/never-detecting CI at any `N ≥ 30` → FAIL (the screened failure mode).
- **Reliability (per `X`)**: if max-gap ≤ 0.10 and slope ∈ [0.85, 1.15] → `P(>X)` is reliable for that
  `X`. Outside the band on any `X` → that `X` is mis-calibrated (disclosed; feeds `DISCOVERY_ONLY` for
  the `P(>X)` leg).
- **Counted-read accounting**: if all scenarios match expected and the cap arithmetic blocks a third
  read → the rule **honors the cap** (PASS). Any mismatch → **`PROTOCOL_DEFECT`** (fix + re-run).
- **Dogfood**: if every cell completes with finite scores, 0 counted reads, and the cutoff assertion
  holds → pipeline runs on real bars (smoke PASS). A crash, non-finite score, or fence breach →
  integrity failure (block).
- **Determinism**: byte-identical second pass → D6 PASS. Any hash mismatch → **`PROTOCOL_DEFECT`**.
- **Overall**: the experiment **feeds** G-017 (it does not adjudicate it). It reports, **per stratum**,
  which `ASS_VALIDATED` legs hold. No single collapsed PASS/FAIL is binding (LESSON-001).

---

## Implementation Safety Constraints (for `experiment-developer`)

- **Determinism (D6)**: seed every draw via `SeedSequence([MASTER_SEED, *key])` with **disjoint stream
  tags** for sample / calibration-null / validation-null / effect / bootstrap / fold / dogfood. Do
  **not** vectorize across replicates in a way that changes the exact RNG draw sequence (would break
  the byte-identical guarantee — keep the per-replicate loop explicit, EXP-076 §RUNTIME NOTE).
  Process-pool parallelism must be **order-preserving and seed-independent** (each cell seeded by its
  key) so the hash is identical at any worker count.
- **Margin discipline**: calibrate `m(N)` on the **`TAG_CAL` nulls only**, freeze it, then measure FPR
  on the **independent `TAG_VAL` nulls** and MDE on the effect types with `m` untouched. MDE uses
  `CI_low > 0`; FPR uses `CI_low > m`. Never let effect data influence `m`.
- **Holdout / TEST fence (dogfood)**: the lazy scan must stop at `train_cutoff = int(int(total*0.7)*0.7)`.
  **Assert** that the maximum `CloseTime` actually read is strictly below the cutoff row's timestamp;
  never collect, materialize, or even count the next-21% TEST stratum or the final-30% holdout. No
  full-data load before slicing.
- **Real-price discipline**: dogfood returns on real `Close`/`RealClose` only; ATR(14) causal; **no
  HA/Renko brick prices**. Drop the trailing `H` bars (no forward look-ahead). Order by `CloseTime`.
- **WF causality**: build folds by ordered index; a completed test fold rolls into the next train
  (historical at the next train time — not leakage). Within-fold real-data resampling is **moving-block**
  (`b = round(fold_len^(1/3))`, floor 1); synthetic within-fold is simple iid; cross-fold aggregation
  is **fold-clustered** (cluster = fold) in both. No bar-index alignment anywhere.
- **Denominators / zero-baseline**: FPR and coverage are rates over `R_REP` with explicit integer
  denominators; use the **Wilson** interval (not normal-approx) for FPR uncertainty; guard empty/thin
  deciles (report per-decile `n`, never divide by zero). Below-floor folds are **disclosed**, never
  dropped silently.
- **Bounded iteration / progress**: `tqdm` over the `(type, N, replicate)` grid, the μ-ladder, and the
  dogfood `(instrument, domain)` cells; bound bootstrap memory by a batch parameter (EXP-076 pattern).
- **Verdict representation (LESSON-001 / EXP-076 audit C1)**: `results/verdict.json` is **per stratum**
  (FPR per `(type,N)`; MDE per `N`; reliability per `X`; dogfood per cell; accounting per scenario).
  Coverage-type checks resolved **per `N`**, never AND-ed across `N`. Any collapsed flag is named and
  **captioned NON-BINDING**. Provide a `--rebuild-verdict` path (regenerate `verdict.json` from
  existing tables, no recompute) as EXP-076 did.
- **Module boundaries**: `xen.wf` = protocol (fold schedule, fold-clustered aggregation, D4.1
  accounting) — pure, reusable, no experiment-specific I/O. `xen.ass` gains only the moving-block
  bootstrap (in-family core extension). Generators + harness + plotting + orchestration stay in
  `code/run_experiment.py`, cleanly sectioned (imports → constants → DGPs → pure computation →
  plotting → orchestration → `main()`).

---

## Complexity Check

- **Statistical / validation checks: 4 / 4** — (1) margin-calibrated FPR, (2) MDE finiteness,
  (3) `P(>X)` reliability, (4) counted-read accounting. (Dogfood + determinism are procedural integrity
  checks, not hypothesis tests.)
- **Visualisations: 5 / 5** — FPR-vs-N, MDE(N), reliability diagram, WF fold schedule, dogfood
  diagnostic.
- **New modules: 1 / 1** — `xen.wf` (protocol + accounting); `xen.ass` reused unchanged + a small
  in-family moving-block bootstrap extension (not a new module).

## Data-View / Alignment Notes

- Synthetic legs touch no market data; the dogfood is confined to the first-49% TRAIN region of the
  **current** dataset. Different domains (15m/1h/4h) yield different event counts for the same window —
  reported per cell; never compared by bar index. The 2-read-cap accounting is **validated** here as a
  function, **not exercised** against the live ledger (Phase 018, post-INFR-003 5-year strata).
