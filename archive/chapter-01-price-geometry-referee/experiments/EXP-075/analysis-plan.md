# Analysis Plan: Experiment EXP-075 — TRAIN Design of an Exhaustion-Cap Entry Filter (CF-HA-HARAMI-001 / HYP-028)

## Objective

On the **TRAIN** stratum, determine whether an entry-time **upper cap on exhaustion magnitude**
(`msofar_atr`, with `m_sofar/p75_thr` as a normalizer-robustness form) **materially improves** the
MA-native `N-PARTIAL-V2A` harami — **lifting the raw-mean leg that failed EXP-071's TEST while
preserving the median, beats-matched-random, and tradable event count** — and how much of any
improvement is captured by a **single uniform deployable rule (M-GLOBAL)** versus only by **per-cell
tuning (M-PERCELL, the overfit ceiling)**. This is a **TRAIN-design-and-lock** experiment: it freezes
one global rule on TRAIN and routes whether a separate one-shot sealed-holdout confirmation is
warranted. **0 TEST reads; holdout never loaded.**

**Two binding lessons from EXP-074 are carried as design invariants (not advisory):**
- **Lesson 1 (no pooling):** every binding metric is computed **per band-core domain (15m/30m/1h)**;
  the band-pooled number is disclosed-only. The masking risk recurs because M-GLOBAL is a
  pooled-quantile threshold — so the single global cap's effect is reported **per domain**, and a cap
  that helps one domain while hurting another is caught, never averaged away.
- **Lesson 2 (no rigid separation gate):** the endpoint is the **strategy's own legs** (raw-mean /
  median / beats-RM / retention), **not** a feature-separation screen. **No framing-consistency gate
  is re-run.** The EXP-074 q05-tail finding is the design rationale only (it fixes that an *upper cap
  on `msofar_atr`* is the lever and its direction); the threshold is then chosen mechanically and the
  cap judged solely by the economic legs.

All methods are **rank-based / bootstrap / descriptive** — `r_e` is heavy-tailed (the whole point is
a left tail that sinks the raw mean while the median passes), so mean/normal-theory inference is
disqualified except as the explicit raw-mean *point* being bootstrapped.

---

## Methodology

### Step 0 — Event resolution + exhaustion-cap gate (frozen machinery, cap added to `cond`)

- **Method.** Import the frozen EXP-068 machinery (via the EXP-074 TRAIN resolver path) unchanged in
  semantics. For each of the 99 cells, resolve the TRAIN `N-PARTIAL-V2A` events **once** to obtain
  the full `cond`-qualifying population: per-event `entry_idx` (entry order), `msofar_atr`,
  `m_sofar/p75_thr`, and the realized `r_e` (certified arm). The exhaustion cap is an **entry-time
  boolean mask** applied to `cond`:
  - **F1:** `cond ∧ (msofar_atr ≤ U)`,
  - **F2:** `cond ∧ (m_sofar/p75_thr ≤ U')`.
  The cap **only removes entries** — it never reaches forward, never alters any retained event's
  resolution, and is fully causal (`msofar_atr` uses the entry bar's own real close vs the pivot
  confirmed at `ConfirmTime ≤ t_i`; trailing ATR). Because only the cap mask changes across
  thresholds, the **signal side is resolved once per cell** and each threshold is a boolean subset of
  the same resolved events (no re-resolution per threshold).
- **Reconciliation (binding integrity check).** The **uncapped** arm (U = +∞) must reproduce the
  EXP-068/074 `N-PARTIAL-V2A` per-event `r_e` exactly — assert `max|Δr_e| = 0` at 1e-9 against the
  EXP-074 `events_<cell>.parquet`. A non-zero diff hard-fails the run.
- **Why.** Byte-for-byte reuse of certified resolution guarantees the cap is the *only* change; the
  loss-tail and returns keep their EXP-068/074 definitions.
- **Simpler alternative considered.** Reuse only the EXP-074 `events_*.parquet` for the signal side
  and skip re-resolution — accepted for the signal legs (with the reconciliation assert), but the
  matched-random null (Step 2) is **not** in those parquets and must be resolved, so the resolver is
  imported regardless.
- **Assumptions.** TRAIN slice `[0, train_cutoff)`, `train_cutoff = int(int(total·0.7)·0.7)`; TEST and
  holdout never sliced. Temporal order by `CloseTime`/`entry_epoch`.
- **Output.** Per cell: the resolved event table `(entry_order, msofar_atr, ss_excess, r_e)` plus the
  threshold-indexed retained masks.

### Step 1 — Threshold grids: M-GLOBAL (pooled) vs M-PERCELL (per-cell)

- **Method.** Two notions of the cap threshold, both drawn from the **same pre-declared percentile
  grid `{p85, p90, p95}`** (upper-tail caps; no finer search, no interpolation):
  - **U_global(p)** = percentile `p` of the **band-core pooled** TRAIN `msofar_atr` (resp.
    `m_sofar/p75_thr` for F2) — **one scalar per p**, applied identically to every cell (the deployable
    rule). "Band-core pooled" = all powered 15m/30m/1h cells' values pooled (5m/2h/4h excluded from the
    pool that sets the deployable threshold; 5m still *evaluated* under it, disclosed).
  - **U_cell(p)** = percentile `p` of **that cell's own** TRAIN `msofar_atr` — the per-cell threshold.
- **Why.** A deployable filter must be one rule (pooled threshold); the per-cell threshold is the
  overfit ceiling that bounds how much a uniform rule leaves on the table.
- **Assumptions.** Percentiles are empirical (type-7), in-sample on TRAIN — legitimate for a
  TRAIN-design lock (selection on TRAIN is the purpose; never on TEST/holdout).
- **Output.** 3 pooled thresholds + 3 per-cell thresholds per form; the retained subset for each.

### Step 2 — Per-cell metric vector on retained events (frozen bootstrap; matched-random re-drawn)

For each cell × form × threshold (and the uncapped baseline), on the **retained** events:

| Leg | Estimator | Source |
| --- | --- | --- |
| **raw mean** `r_e` + 1σ CI low | `bootstrap_stat_distribution(..., "mean")`, 16th pct | EXP-068 (the EXP-071 *failing* leg — to FIX) |
| **median** `r_e` + 1σ CI low | `bootstrap_median_distribution`, 16th pct | EXP-068 (the leg EXP-071 *passed* — to PRESERVE) |
| **beats-RM-native** + 1σ CI low | `contrast(signal, matched_random)` median contrast, 16th pct | EXP-068/060B (substrate property — to PRESERVE) |
| **retention** | retained_n / baseline_n; retained_n absolute | descriptive |

- **Matched-random under the cap (key methodological point).** `beats-RM-native` is the signal-minus-
  own-matched-random median contrast. When the cap removes entries, the matched-random null is
  **re-drawn at the retained count** within the same MA regime via the frozen `matched_random_arm`
  (count-matched, regime-matched — exactly EXP-068's null, just at the capped count). This keeps the
  contrast apples-to-apples: "does the *capped* signal still beat count-matched random in its regime?"
  - **Simpler alternative considered.** Keep the baseline null fixed and compare the capped signal
    median to it — **rejected**: not count-matched, inflates/deflates the contrast by the retention
    ratio. Exhaustion-matching the null (drawing random entries with the retained exhaustion
    distribution) is **out of scope** — the preservation question is whether the capped signal beats
    *regime* random, the EXP-060B/068 definition.
- **Bootstrap.** Frozen moving-block bootstrap, block `b = round(n^(1/3))`, `N_BOOT = 10_000`,
  `BOOT_BATCH = 2_000`, **integer-list seeds** `[BASE_SEED, cell_index, purpose, form_idx, thr_idx]`
  (no `hash()` on labels). 1σ CI = 16th/84th percentile (EXP-068/074 convention).
- **Power floor.** Bootstrap legs return NaN below `POWER_FLOOR = 30` retained events.
- **Why.** Rank/bootstrap is robust to the heavy left tail; reusing the certified estimators keeps the
  legs identically defined to EXP-068/071, so "lift the raw mean" is measured on the same object that
  failed EXP-071.
- **Output.** Per cell × form × threshold: `{mean, mean_ci_low_1s, median, median_ci_low_1s,
  rm_contrast, rm_ci_low_1s, retained_n, retention}`.

### Step 3 — Per-cell "improved" joint criterion (the economic instrument)

- **Method.** A cell is **improved** under an arm (form × threshold) iff **all** hold simultaneously
  on retained events:
  1. `mean_ci_low_1s > 0` (raw-mean leg fixed), **and**
  2. `median_ci_low_1s > 0` (median edge preserved), **and**
  3. `rm_ci_low_1s > 0` (beats-RM-native preserved), **and**
  4. `retention ≥ 0.70` **and** `retained_n ≥ 30`.
- **Why this joint form (EXP-074 Lesson 2's correct instrument).** Because high exhaustion both
  *creates* the q05 tail and *raises* the median, a cap necessarily trades tail-suppression against
  median-erosion and event loss. Requiring all four legs simultaneously credits the cap only when the
  net is positive on every leg — the economically correct test the consistency gate could never
  express. A cap that lifts the mean only by gutting the sample, or by breaking the median/beats-RM,
  is **not** improved.
- **Powered cell (pinned denominator — no membership drift).** A cell is **powered** iff its
  **baseline** (uncapped) `r_e < q05` tail cell has ≥ 30 events (EXP-074 convention). Powered status is
  fixed pre-cap so the cap never moves its own denominator (audit-relevant: no membership-altering
  optimization).
- **Output.** Per cell × arm: boolean `improved` + the failing leg(s) when not.

### Step 4 — Per-domain binding metric (per band-core domain; never pooled)

- **Method.** For each band-core domain D ∈ {15m, 30m, 1h}, over its **powered** cells, per arm:
  - **improved-cell share** `s_D(arm)` = fraction of D's powered cells that are `improved`;
  - **baseline improved share** `s_D(baseline)` (same criterion, uncapped arm);
  - **uplift** `Δ_D = s_D(capped) − s_D(baseline)` — the cap must **add** improved cells;
  - **hurt flag** = `Δ_D ≤ −0.10`;
  - **overfit premium** `prem_D = s_D(M-PERCELL) − s_D(M-GLOBAL)` (both at their locked thresholds).
  5m is computed identically but **disclosed-only**; 2h/4h are excluded (0 powered — INCONCLUSIVE).
  The **band-pooled** share is computed for disclosure and **does not bind**.
- **Domain "improved by the cap" (M-GLOBAL)** iff `Δ_D ≥ +0.15` **and** `s_D(capped) ≥ 0.50` **and**
  no retention violation at the locked U.
- **Why.** This is EXP-074's per-domain breadth methodology applied to the economic `improved` unit —
  it answers "does the single global cap help this domain" without pooling heterogeneous domains.
- **Output.** Per-domain table `{s_baseline, s_global, s_percell, Δ_global, hurt, premium}` for F1/F2.

### Step 5 — M-GLOBAL locked-U selection (pre-registered mechanical rule) and M-PERCELL ceiling

- **M-GLOBAL lock (deployable).** Lock `U` at the **single grid percentile** `p ∈ {p85,p90,p95}` that
  **maximizes the count of band-core domains "improved"** (Step 4) under M-GLOBAL; **ties broken
  toward the least restrictive percentile** (highest p ⇒ highest retention). Done **per form** (F1,
  F2); F1 is the lead, F2 the normalizer-robustness disclosure. The locked `(form, p, U)` is the
  frozen object, hash-pinned. Selection is on **TRAIN only** — the explicit purpose of a TRAIN-design
  experiment; never on TEST/holdout.
- **M-PERCELL ceiling (diagnostic only).** Per cell, pick the grid threshold maximizing that cell's
  improvement (improved if reachable; else max `mean_ci_low_1s` subject to retention ≥ 0.70). Reported
  **only** as the overfit ceiling; **never** frozen, deployed, or carried to any holdout.
- **Why.** Separates "is there a deployable uniform cap" from "is there only an overfit cap."
- **Output.** Locked global filter spec (JSON, hash-pinned) + the per-domain overfit premium.

### Step 6 — Routing verdict (pinned thresholds; per-domain vector read jointly)

Read the **per-domain** improvement vector — never a band-pooled average:

- **FILTER_PROMISING** → under M-GLOBAL: **≥ 2 of 3** band-core domains improved (`Δ_D ≥ +0.15`,
  `s_D ≥ 0.50`, retention OK), **no** band-core domain hurt (`Δ_D ≤ −0.10`), **and** band-core mean
  **overfit premium ≤ 0.20**. ⇒ freeze the global filter (band-restricted to the domains where it
  holds); route to a **separate** one-shot sealed-holdout-confirm experiment (own EXP-ID/D0; fresh
  strata only — never the EXP-071-consumed TEST strata).
- **FILTER_OVERFIT** → M-PERCELL shows domain uplift but M-GLOBAL improves **< 2** band-core domains,
  OR overfit premium **> 0.20**, OR M-GLOBAL **hurts** any band-core domain. ⇒ do not spend the
  holdout; route toward closing CAND-001 or a band-restricted re-scope.
- **FILTER_INEFFECTIVE** → even **M-PERCELL** fails `Δ_D ≥ +0.15` in **any** band-core domain. ⇒ the
  exhaustion cap is not a lever; supports closing CAND-001 cleanly.
- **INCONCLUSIVE_POWER** → fewer than 2 band-core domains have ≥ 5 powered cells. ⇒ no routing change.

### Pinned threshold rationale (pre-registered; not tunable post-hoc)

| Bar | Value | Rationale |
| --- | --- | --- |
| retention floor | **≥ 0.70** (and ≥ 30 abs) | a deployable cap that discards > 30% of in-band events is not a "filter" but a different strategy; pinned in `D0-amendment-007`. |
| uplift `Δ_D` | **≥ +0.15** | a *modest but material* per-domain breadth gain — ≥ 15 percentage points more of the domain's powered cells meeting the **full four-leg economic** criterion. Conceptual ancestor is EXP-074's 0.15 material bar (rank-biserial 0.15 ↔ AUC ≈ 0.575); here the quantity is an **improved-cell share delta**, not an AUC — the 0.15 is reused as a deliberately modest exploratory TRAIN-design bar, **not** inherited as an effect-size identity. |
| hurt `Δ_D` | **≤ −0.10** | **asymmetric** (more sensitive to harm than to gain): a single global rule that *breaks* a domain disqualifies deployability even if it helps elsewhere — the asymmetry encodes "first, do no harm" for a uniform filter. |
| overfit premium | **≤ 0.20** | M-GLOBAL must capture all but ≤ 20 share-points of the M-PERCELL ceiling for the uniform rule to count as the real lever; a larger gap means the edge is per-cell-mined, not deployable. |

These four bars are **frozen here, before any code runs**, and are the complete set of free decision
thresholds in EXP-075 (the only other free parameter is `U`, selected by the Step-5 mechanical rule).

---

## Visualisations (≤ 6)

1. **Per-domain improved-share, baseline vs M-GLOBAL-capped** (grouped bars, domain × form) with the
   `Δ ≥ 0.15` uplift line — the headline "does the uniform cap add improved cells per domain".
2. **Raw-mean shift (capped − baseline) across band-core cells**, M-GLOBAL vs M-PERCELL (paired
   strip/box) — does the cap lift the failing leg, and how much more per-cell tuning would.
3. **Overfit premium by domain** (M-PERCELL share − M-GLOBAL share) with the 0.20 bar.
4. **Retention vs raw-mean-gain trade-off** (scatter over band-core cells; the 0.70 retention line) —
   exposes caps that "lift the mean by gutting the sample".
5. **U-sensitivity curve** (p85/p90/p95): count of improved band-core domains vs percentile, per form
   — shows the locked-U choice and its stability.
6. **Continuity cell GBPUSD-5m** `r_e` distribution before/after the locked cap (disclosed; 5m
   non-binding) — continuity with EXP-071/074.

## Interpretation Guide

- **≥2/3 band-core domains improved, none hurt, premium ≤0.20** → **FILTER_PROMISING**: a uniform
  exhaustion cap is a credible deployable lever; freeze it and route to a separate holdout confirm.
- **M-PERCELL improves but M-GLOBAL <2 domains / premium >0.20 / any domain hurt** → **FILTER_OVERFIT**:
  the cap works only per-cell; not deployable; do not spend the holdout.
- **Even M-PERCELL fails Δ≥0.15 anywhere** → **FILTER_INEFFECTIVE**: exhaustion cap is not the lever;
  supports closing CAND-001.
- **<2 band-core domains with ≥5 powered cells** → **INCONCLUSIVE_POWER**.
- Read 5m and the band-pooled line as **disclosure only**; never let them flip the per-domain verdict.
- A cap that lifts the band-pooled mean but improves **no** individual band-core domain is the EXP-074
  masking trap inverted — it is **not** FILTER_PROMISING.
- **Retention attribution (binding disclosure).** The retention denominator `n_base` is the full
  uncapped qual count, which includes events whose exhaustion feature is undefined (NaN); `cap_keep`
  drops those, so events the cap *structurally cannot retain* still count against retention. Report
  the per-cell `undef_share_{F1,F2}` (recorded in `cell_metrics.csv`) alongside retention, and when a
  cell/domain fails the 0.70 retention floor, state how much of the loss is feature-undefinedness vs
  exhaustion removal. A retention failure dominated by undefined features is **not** evidence the cap
  is too aggressive.

## Implementation-safety constraints (for `experiment-developer`)

- **TRAIN-only fence:** slice `[0, train_cutoff)`, `train_cutoff = int(int(total·0.7)·0.7)`; never
  slice/collect TEST or holdout. Forward resolution clips at the TRAIN edge (boundary entries censor).
- **Real-price only:** `r_e` is the certified `N-PARTIAL-V2A` real-price arm; HA used solely for
  harami detection. No HA-price returns.
- **Causal cap:** the cap is an entry-time boolean on `cond`; it only removes entries, never reaches
  forward, never alters a retained event's resolution. `msofar_atr` causal (entry close vs confirmed
  pivot; trailing ATR).
- **Pinned denominator:** `powered` = baseline q05 tail ≥ 30, fixed pre-cap; the cap must not change
  powered membership. No `.unique()`/dedup on the event set.
- **Matched-random re-drawn at retained count** per (cell × form × threshold) via frozen
  `matched_random_arm`; integer-list seeds only, no `hash()`.
- **Determinism:** integer-list bootstrap seeds `[BASE_SEED, cell_index, purpose, form_idx, thr_idx]`;
  `N_BOOT=10_000`, `BOOT_BATCH=2_000`.
- **No pooled binding metric:** binding aggregation is **per band-core domain**; band-pooled and 5m are
  disclosed-only and must be written to separate, clearly-labelled fields.
- **Finite/zero handling:** retention denominator = baseline_n (guard 0 → cell excluded with count);
  beats-RM contrast NaN when either side < POWER_FLOOR; never infinity-fill; below-floor legs → NaN and
  excluded from shares (counted).
- **Performance/progress:** resolve each cell's signal **once**; iterate thresholds as boolean subsets;
  `tqdm` over the 99-cell loop and the bootstrap; no data reload for plots (reuse in-memory tables);
  bounded pandas conversion only for plotting aggregates.
- **Reconciliation assert:** uncapped baseline `r_e` vs EXP-074 `events_<cell>.parquet`, `max|Δ| = 0`
  at 1e-9 — hard-fail on mismatch.
- **Organization:** imports → path → constants → types → I/O → pure compute → plotting → orchestration
  → `main`; `Agg` backend; output dirs created in orchestration; one experiment-local module.

## Complexity Check

- **Statistical/association families: 3 / 3** — (1) moving-block bootstrap CIs (median/mean), (2) the
  matched-random median contrast (beats-RM), (3) descriptive per-domain improved-share/Δ aggregation.
  (The bootstrap is the uncertainty wrapper, not a separate inferential family.)
- **Visualisations: 6 / 6.**
- **New modules: 1 / 1** (experiment-local; reuse frozen EXP-068/074 machinery by import; no shared
  `xen/` change).
