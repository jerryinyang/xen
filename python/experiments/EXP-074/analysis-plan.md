# Analysis Plan: Experiment EXP-074 — TRAIN-Only Loser-Tail Characterization (CF-HA-HARAMI-001 / HYP-027)

## Objective

On the **TRAIN** stratum, across the **full 99-cell MA-native harami substrate** (the EXP-068
grid), determine which causal entry-time features (if any) separate the large-loss tail of
`N-PARTIAL-V2A` per-event returns `r_e` from the rest of the distribution — leading with two
mechanism-grounded hypotheses (H1 exhaustion-magnitude bound, H2 harami-polarity agreement) and
screening the full 14-feature causal set as additional dimensions. This is **characterization**,
not selection: no filter is chosen, no parameter tuned. The **binding verdict object is the
substrate** (not any single cell): a feature is a *substrate separator* only if it is a cell-level
candidate separator in a material share of powered cells with a sign-consistent, material cross-cell
median effect. The output routes the CF-HA-HARAMI-001/CAND-001 decision and the EXP-075 exhaustion-cap
design (pursue a TRAIN-designed/holdout-confirmed tail filter vs close the family). GBPUSD-5m is
reported as a **named continuity cell** for comparison with EXP-071, not as the binding object.

This is a pure association/separation screen. All methods are **rank-based and non-parametric** —
appropriate because `r_e` is heavy-tailed (the whole motivation is a left tail that sinks the raw
mean while the median/winsorized mean are positive), so any mean/variance-based or normal-theory
method is disqualified.

---

## Methodology

### Step 0: Event resolution (TRAIN-only) and feature extraction

- **Method**: Reuse the frozen EXP-068/EXP-071 machinery via the `resolve_test_cell` resolution
  path, but **mirror the window mask to TRAIN**: qualifying `N-PARTIAL-V2A` entries are those with
  `entry_epoch ≤ train_end` (the exact complement of EXP-071's `entry_epoch > train_end`). MA /
  `/STRONG-STAT` / ATR / segment state is warmed by the bars preceding each entry, identically to
  EXP-071; only the *evaluation* window changes. Per qualifying entry, record realized `r_e`
  (binding arm `pv.r_e`) and the 14-feature causal vector (scope §"Causal entry-feature set").
- **Why**: byte-for-byte reuse of certified resolution guarantees the events and returns match the
  EXP-071/EXP-068 definitions; only the chronological window differs. No new return logic.
- **Simpler alternative considered**: recompute features from scratch — rejected; duplicates
  certified machinery and risks definitional drift.
- **Assumptions**: TRAIN slice `[0, train_cutoff)`; TEST never re-read; holdout never loaded.
  Temporal ordering by `CloseTime`/`entry_epoch`. All features causal (≤ entry timestamp) — verified
  per scope (binding pivot `ConfirmTime ≤ t_i`, trailing windows only, no ZigZag position-in-move).
- **Expected output**: per-cell tidy table `events_<cell>.parquet` with columns `[entry_epoch, r_e,
  f1..f14]`; an event-count + feature-coverage summary (NaN/undefined rates per feature).

### Step 1: Tail-target construction (all three framings)

For each cell, define three target views on `r_e` (scope §"Tail-target definitions"):

- **T-A (extreme + sign)** — two binary labels: `tailA_q05 = 1[r_e < q05(r_e)]` and
  `tailA_neg = 1[r_e < 0]`. `q05` is the empirical 5th percentile of the cell's TRAIN `r_e`
  (type-7 linear quantile, matching `xen`).
- **T-B (mean-below-median contributors)** — binary `tailB = 1[r_e < median(r_e)]`.
- **T-C (continuous)** — `r_e` itself (no cutoff), oriented so that *more negative = more
  loss*; association is signed toward the loss direction.

- **Method/Output**: deterministic labels appended to the event table; per-cell quantile table
  (`q05`, median, mean, winsorized mean for context).
- **Assumptions**: empirical quantiles on the in-sample TRAIN distribution; no model.

### Step 2: Per-feature separation / association

For each of the 14 features against each target framing:

| Feature type | Target | Estimator | Output |
| --- | --- | --- | --- |
| Continuous (f1,2,4,5,6,7,8,9,10,12) | binary T-A/T-B | **rank-biserial correlation** `r_rb = 2·AUC − 1` (Mann-Whitney U effect size: feature values in tail-group vs rest) | `r_rb ∈ [−1,1]`, AUC, group medians, n per group |
| Continuous | T-C continuous | **Spearman ρ**(feature, `r_e`) | ρ, n |
| Binary categorical (f3 polarity-agreement, f11 `rd`) | binary T-A/T-B | **difference in tail-rate** between groups + **phi** coefficient; equivalently rank-biserial of `r_e` across the binary feature | Δ tail-rate, phi, per-group n |
| Binary categorical | T-C | rank-biserial of `r_e` between the two feature groups (Mann-Whitney) | r_rb |
| Multi-level categorical (f13 session 4-level, f14 day-of-week 7-level) | T-C continuous | **Kruskal-Wallis H** across groups (omnibus) + per-group median `r_e` and tail-rate with CI | H, per-group stats |
| Multi-level categorical | binary T-A/T-B | per-group tail-rate with bootstrap CI; **Cramér's V** of (group × tail) contingency | V, per-group tail-rate |

- **Why rank-biserial / AUC for binary, Spearman for continuous**: both are rank-based, scale-free,
  monotone-only, and robust to the heavy left tail; AUC/rank-biserial is the natural "how well does
  this feature separate losers from the rest" measure and maps 1:1 to the Mann-Whitney U.
- **Simpler alternative considered**: group mean differences / point-biserial (Pearson) — rejected;
  mean-based statistics are exactly what the fat tail corrupts. Visual-only — insufficient to rank
  14 features.
- **Circularity note (f13/f14)**: hour-of-day is circular, so it is **not** treated as a linear
  feature — it is bucketed into the 4 session blocks (Asia / London / London-NY overlap / NY) and
  day-of-week into 7 categories, then handled by Kruskal-Wallis / contingency, which are invariant
  to category ordering. No linear/Spearman estimator is applied to circular time.
- **Assumptions**: independence across events is imperfect (events cluster in time) — addressed by
  the block bootstrap in Step 3, not by the point estimator.
- **Expected output**: a master ranking table — one row per (feature × framing) with the effect
  estimate, AUC/phi/V, direction, and per-group n.

### Step 3: Uncertainty on the leading features (block bootstrap)

- **Method**: For the features that reach the material bar on point estimate (and unconditionally
  for the two lead features f1, f3), compute a **moving-block bootstrap** CI on the effect estimate.
  Resample the *chronologically ordered event sequence* in blocks of length `b = round(n_events^(1/3))`
  (the EXP-068/EXP-071 convention), `N_BOOT = 10_000`, recomputing the effect each resample. Report
  the 1σ (68%) and 2σ (95%) percentile intervals.
- **Why block (not iid) bootstrap**: 5m harami entries cluster in time; an iid bootstrap would
  understate uncertainty. Block resampling preserves local serial dependence among adjacent events.
- **Simpler alternative considered**: iid bootstrap — rejected (ignores event clustering); analytic
  Mann-Whitney CI — rejected (assumes independence).
- **Assumptions**: approximate stationarity within the TRAIN window over block scale; acceptable for
  a descriptive CI.
- **Expected output**: effect estimate + [CI_lo_1s, CI_hi_1s, CI_lo_2s, CI_hi_2s] for each leading
  feature, each framing.

### Step 4: Cell-level candidacy → substrate-wide aggregation (the binding verdict)

- **Cell-level candidate separator** (per powered cell): a feature qualifies in a cell when (a) its
  effect is **directionally consistent across all three framings** (T-A both cutoffs, T-B, T-C),
  (b) its TA_q05 point `|effect| ≥ 0.15`, **and** (c) its 1σ block-bootstrap CI lies on the
  material side of 0.15. Consistency across pre-declared framings is the anti-p-hacking guard.
- **Per-domain aggregation (BINDING)**: group powered cells (n_q05 ≥ 30) **by domain**. For each
  domain report two metrics: (i) the **per-cell any-feature separability rate** (fraction of the
  domain's powered cells with a per-cell candidate separator on any feature); and (ii) for each
  feature the **single-lever breadth** = fraction of the domain's powered cells in which it is a
  cell-level candidate, with a within-domain bootstrap median-effect CI (resample the domain's
  powered cells). A domain has a **uniform lever** when some feature's breadth `≥ 0.50` and its
  within-domain median effect CI (1σ) is on the material side of 0.15 with a consistent sign.
  The pooled (all-domain) version is computed too but is **disclosed-only** — pooling masks the
  domain structure (5m noise + underpowered 2h/4h vs the 15m–1h core). GBPUSD-5m is a continuity
  cell only.
- **Multiplicity stance**: this is a **hypothesis-generating screen** over a wide surface (14
  features × ~4 framings × 99 cells). We **rank-and-report** with bootstrap CIs rather than apply a
  per-(cell×feature) family-wise correction, because (a) no confirmatory inference is drawn — any
  separator must be re-confirmed via EXP-075's TRAIN-design → sealed-holdout chain, (b) the two
  lead features (f1, f3) are **pre-registered**, and (c) **the verdict is itself a breadth
  statistic** (≥50% of powered cells + sign-consistent material cross-cell median): isolated
  cell-level hits cannot satisfy it, so the share rule *is* the multiplicity guard. The plan makes
  **no p-value-thresholded claim**; effect size, breadth, and CIs carry the interpretation.
- **Expected output**: `substrate_feature_share.csv` (per-feature share + cross-cell median CI),
  `substrate_verdict.json`, and the substrate separator shortlist; per-cell ranking retained in
  `feature_separation.csv`.

### Material-effect bar (confirmed)

**Retain the scope's |effect| ≥ 0.15** (rank-biserial / |Spearman ρ| / equivalent), with the
refinement that the **bootstrap 1σ CI must also lie on the material side of 0.15** for a feature to
be called a candidate separator (point estimate alone is insufficient). Rationale: rank-biserial
0.15 ↔ AUC ≈ 0.575 — a small but genuinely actionable separation; below this an entry filter cannot
meaningfully reshape the tail without gutting event count. The bar is deliberately modest because
this is an exploratory screen, not a confirmatory test; the CI condition prevents promoting noise.

---

## Power / Floor

- **Per-cell power floor**: a cell is **powered** only with **≥ 30 events in its `r_e < q05` tail
  cell**; unpowered cells are excluded from both metrics' denominators (still tabulated). Empirically
  every 2h/4h cell is unpowered (n_q05 ≤ 25 even at the largest, BTCUSD-2h) — expected, and correctly
  removed from the breadth statistic rather than diluting it.
- **Per-domain INCONCLUSIVE_POWER rule (binding)**: a domain with **< 5 powered cells** is
  **INCONCLUSIVE_POWER** (too thin to estimate a breadth/rate) — this is what rules out 2h and 4h
  (0 powered each). 5m/15m/30m/1h have 16–17 powered.
- **Pooled-substrate floor (disclosed-only)**: < 30 of 99 cells powered ⇒ pooled INCONCLUSIVE; the
  pooled line does not bind.
- **Reporting under-power**: any cell/feature/framing whose tail cell `< 30` or whose bootstrap CI
  spans the material bar in both directions is marked `low-power` and excluded from the
  candidate-separator determination (but still tabulated).

---

## Verdict mapping (to scope Success/Failure criteria)

Computed **per domain** over its powered cells (GBPUSD-5m reported as a continuity cell only); the
pooled-substrate verdict is disclosed-only. Four-tier per domain:

- **SEPARATOR_FOUND** → ≥1 feature has single-lever breadth ≥ 0.50 of the domain's powered cells
  (point |effect| ≥ 0.15 ∧ 1σ CI material-side ∧ all-framing consistency) **and** a sign-consistent
  within-domain median effect CI on the material side. ⇒ a uniform lever exists in this band;
  strongest motivation for an EXP-075 exhaustion-cap **restricted to that band**.
- **SEPARABLE_NO_UNIFORM_LEVER** → per-cell any-feature separability rate ≥ 0.50 but no feature
  reaches the breadth bar. ⇒ the tail separates via heterogeneous, cell-specific features; a single
  *global* cap is weakly supported — EXP-075, if opened, must be per-domain / feature-blended.
- **NO_SEPARATOR** → per-cell rate < 0.50 and no uniform lever. ⇒ tail not separable in this band.
- **INCONCLUSIVE_POWER** → < 5 powered cells in the domain. ⇒ no routing change for the band.

CAND-001 / EXP-075 routing reads the domain verdicts **jointly**: any band returning SEPARATOR_FOUND
or SEPARABLE_NO_UNIFORM_LEVER on H1 motivates a band-restricted EXP-075; all-NO_SEPARATOR /
all-INCONCLUSIVE supports closing the path without spending the holdout. The verdict is descriptive
routing — it does **not** itself select a filter or touch TEST/holdout.

---

## Visualisations (≤ 6)

1. **Cross-cell lead-feature distribution** (boxplot over powered cells): each lead feature's TA_q05
   effect across all powered cells, with the |effect| = 0.15 material line — the headline "how
   broadly does the separator hold".
2. **Per-domain single-lever breadth heatmap**: feature × domain candidate-cell share (0→1), with
   each domain's verdict and per-cell separability rate annotated — shows the 15m–1h sweet spot and
   the absence of any uniform lever at a glance.
3. **H1 conditional `r_e` distribution** (continuity cell): `r_e` by `m_sofar/atr_entry` bins
   (box) — does the loss tail concentrate at extreme magnitude.
4. **H2 polarity contingency** (continuity cell): tail-rate (`r_e<q05`, `r_e<0`) for polarity-agree
   vs polarity-disagree entries.
5. **Session / magnitude loss-rate heatmap** (continuity cell): tail-rate across session bucket ×
   `m_sofar/atr` tercile.
6. **Continuity-cell ranking** (bar): GBPUSD-5m feature separation (TA_q05) with the material line —
   continuity with the EXP-071 yellow-flag read.

---

## Interpretation Guide

- Read the domains **jointly**, never pooled. For each domain: the per-cell any-feature rate says
  whether the tail is separable at all; the per-feature breadth (esp. f1 `m_sofar/atr` exhaustion and
  f3 polarity) says whether one uniform lever exists.
- A domain with a feature at breadth **≥ 0.50** + material within-domain median CI → **SEPARATOR_FOUND**:
  a bounded entry filter on that feature is a credible lever **in that band** → route EXP-075 restricted
  to that band.
- A domain with per-cell rate ≥ 0.50 but no breadth-≥0.50 feature → **SEPARABLE_NO_UNIFORM_LEVER**: the
  tail is separable but heterogeneously; a single global cap is weakly supported — EXP-075, if opened,
  is per-domain/feature-blended, not one threshold. (This is the expected 15m–1h read.)
- A domain with per-cell rate < 0.50 and no lever → **NO_SEPARATOR** (expected at 5m: noise-dominated).
- A domain with < 5 powered cells → **INCONCLUSIVE_POWER** (expected at 2h/4h: underpowered).
- Routing: all-NO_SEPARATOR / all-INCONCLUSIVE across bands → close the path, do not spend the holdout.

---

## Complexity Check

- Statistical/association method families: **3** (rank-biserial/AUC + Mann-Whitney; Spearman;
  Kruskal-Wallis/contingency) + block-bootstrap CI — within the scope's 3-family budget (bootstrap
  is the uncertainty wrapper, not a separate inferential family).
- Visualisations: **6 / 6**.
- New modules: **1 / 1** (experiment-local; reuse frozen EXP-068/EXP-071 machinery by import).

---

## Data-View Comparison & Implementation Safety (for experiment-developer)

- **TRAIN-only fence**: slice `[0, train_cutoff)` with `train_cutoff = int(int(total × 0.7) × 0.7)`
  (frozen EXP-068/071 convention; `int` truncates downward → fence-conservative); never slice TEST
  or holdout in this script. Mirror EXP-071's mask as `entry_epoch ≤
  train_end` (the documented complement).
- **Temporal ordering** by `CloseTime`/`entry_epoch`; event clustering handled by the moving-block
  bootstrap (block `b = round(n_events^(1/3))`, `N_BOOT = 10_000`, seeded with the EXP-068 base-seed
  convention for determinism).
- **Real-price outcomes only**: `r_e` is the certified `N-PARTIAL-V2A` realized return on real prices;
  HA used only upstream for harami detection.
- **Zero-baseline / finite handling**: features with undefined values (e.g. `defined=False` strong-stat,
  `valid=False` state, NaN ATR) are dropped per-feature with an explicit coverage count, never imputed;
  ratio features guard zero denominators (report coverage, do not infinity-fill).
- **Determinism & progress**: deterministic outputs; `tqdm` over the 99-cell resolution loop and the
  bootstrap (per-event block bootstrap on leads + cell-level bootstrap on the cross-cell median);
  string-free integer seeds only (no `hash()` on labels); concise logging; no full-data pandas
  conversion for plots (reuse the analysis tables).
- **No deduplication / no membership-altering optimization**: event set defined solely by the frozen
  resolver + TRAIN mask.
