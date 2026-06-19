# Experiment: EXP-075 — TRAIN Design of an Exhaustion-Cap Entry Filter on the MA-Native N-PARTIAL-V2A Harami (CF-HA-HARAMI-001 / HYP-028)

## Hypothesis

**TRAIN-design-and-lock (0 TEST reads, holdout sealed). Authorized by `D0-amendment-007` (revised),
ratified by operator direction 2026-06-19.**

EXP-074 (CHARACTERISATION_DELIVERED, 2026-06-19) has **run**. Its binding per-domain verdict returned
**no location-monotone uniform lever** (5m NO_SEPARATOR; 15m/30m/1h SEPARABLE_NO_UNIFORM_LEVER; 2h/4h
INCONCLUSIVE_POWER), i.e. it did **not** return a formal `SEPARATOR_FOUND`. The motivating premise of
this experiment is therefore **not** "EXP-074 certified a separator." It is the **gate-masked but
substantively strong finding** EXP-074 delivered: the H1 exhaustion-magnitude lead
`msofar_atr = m_sofar / atr_entry` separates the **extreme q05 loss tail** near-universally
(rank-biserial 0.68–0.80, AUC ≈ 0.84–0.90, the 0.15 material bar cleared in 100% of powered cells in
every powered domain; median 0.70–0.79), while ~vanishing/sign-flipping on the location framings
(TA_neg/TB_median/TC). It registered as "no uniform lever" **only** because EXP-074's pre-registered
all-framing sign-consistency gate is structurally blind to tail-shape effects — the exact bimodality
(exhausted entries either work, median-positive, or go catastrophic, q05) that broke EXP-071's raw
mean while the median/winsorized mean passed. See `D0-amendment-007` §"Status post-EXP-074".

**Primary hypothesis (H-CAP).** An entry-time **upper cap on exhaustion magnitude** (`msofar_atr`)
removes enough of the q05 left tail to **lift the `N-PARTIAL-V2A` raw mean** — the single leg that
failed EXP-071's one-shot TEST — **without** breaking the median edge, the beats-matched-random
property, or the tradable event count, **and does so per domain in the separable band-core
(15m/30m/1h), not merely as a band-pooled average** (EXP-074 Lesson 1). The current substrate gates a
**lower** bound (`m_sofar ≥ /STRONG-STAT p75`) and imposes **no upper bound / maturity cap**; this
experiment designs the missing cap.

This experiment **designs and locks** the filter on TRAIN only. **No holdout/TEST is read.** A
separate future experiment performs the one-shot sealed-holdout confirmation of the *frozen* global
filter on fresh strata.

### Lessons from EXP-074 carried as binding design constraints

- **Lesson 1 — pooled/unstratified evaluation masks structure.** The binding read is **per domain**
  (15m/30m/1h band core; 5m disclosed; 2h/4h excluded — underpowered). The band-pooled number is
  **disclosed-only**. The masking risk recurs one level up: M-GLOBAL is a *pooled-quantile* threshold,
  so EXP-075 must report whether the single global cap helps **each band-core domain separately** — a
  global cap that helps 1h while hurting 15m must be caught, never averaged away.
- **Lesson 2 — a gate must not be so rigid it nullifies a worthwhile observation.** EXP-075 re-runs
  **no separation / framing-consistency gate.** The q05-tail finding is the **design rationale** only
  (it fixes that an *upper cap on `msofar_atr`* is the lever and its direction); the cap is judged
  **solely** by the direct economic endpoint on the strategy's own legs (Metrics). The legitimate
  anti-p-hacking role of EXP-074's gate is **replaced** by: a single pre-registered lead + a fixed
  threshold grid + M-GLOBAL-only deployability + non-confirmatory-until-separate-holdout.

## Question

On the TRAIN stratum, does an exhaustion-cap entry filter materially improve the `N-PARTIAL-V2A`
harami **per band-core domain** — lifting the raw mean while preserving median/beats-RM/event count —
and how much of any improvement is robust (captured by a single uniform global rule) versus overfit
(only reachable by per-cell tuning)?

## Scope Boundaries

- **Data Views**: 1-minute time bars → MA(20,50)-segment domain bars per cell; Heiken Ashi for harami
  detection only. **Real-price outcomes only** (`RealOpen/High/Low/Close`); HA never used for returns.
- **Parameters**: all frozen from EXP-068/074 — MA(20,50); `/STRONG-STAT` trailing-20 p75; Wilder
  ATR(14); `N-PARTIAL-V2A` exit geometry; binding object `nat`, binding arm `PARTIAL-V2A`. The
  **only** new free parameter is the exhaustion-cap threshold `U` (Filter Variants). No other
  parameter is searched or tuned.
- **Feature**: the cap acts on `msofar_atr` (F1) and `m_sofar / p75_thr` (F2 normalizer robustness).
  **`favdist_atr` is NOT used** (EXP-074 W1: `favdist_atr ≡ 0.5·msofar_atr` exactly — redundant).
  **H2 (polarity agreement) is NOT used** (EXP-074: refuted).
- **Cells**: resolve the **full 99-cell MA-substrate matrix** (EXP-060B grid) for disclosure, but the
  **binding evaluation is the band core — 15m/30m/1h** (EXP-074 per-cell separability 0.88/0.71/0.94).
  **5m is disclosed/secondary** (100% q05 H1 breadth but noisier under the full gate, rate 0.35);
  **2h/4h excluded from binding** (0 powered cells — INCONCLUSIVE_POWER). GBPUSD-5m reported as the
  continuity cell.
- **Time range**: **TRAIN slice only** — `[0, train_cutoff)`, `train_cutoff = int(int(total·0.7)·0.7)`
  (frozen EXP-074 convention). The next-21% TEST stratum and the final-30% global holdout are
  **never sliced, inspected, or used**. Forward resolution clips at the TRAIN edge (boundary entries
  censor; counted).
- **Look-ahead prevention**: `msofar_atr` is causal (entry bar's own real close vs the binding pivot
  confirmed at `ConfirmTime ≤ t_i`; trailing ATR). The cap is an entry-time gate — it only removes
  entries, never reaches forward.
- **Exclusions**: no TEST read, no holdout read, no candidate slot consumed, **no per-cell threshold
  promoted to a deployable filter** (M-PERCELL is diagnostic only), no parameter tuned beyond `U`, no
  new shared `python/src/xen/` module.

## Filter variants (2 forms × 2 selection methods = 4 arms)

Applied as an additional entry gate on the EXP-074 `cond` mask: `cond ∧ (exhaustion within bound)`.

**Forms**
- **F1 — single upper cap.** Keep entries with `msofar_atr ≤ U`. The existing `/STRONG-STAT` p75
  lower gate stays; F1 adds only the upper bound.
- **F2 — strong-stat-excess cap (normalizer robustness).** Keep entries with `m_sofar / p75_thr ≤ U'`.
  Tests whether the result is robust to expressing exhaustion relative to the per-entry strong-stat
  threshold rather than ATR.

**Selection methods (the integrity axis)**
- **M-GLOBAL — single pre-registered uniform rule (the only deployable arm).** One threshold rule,
  identical across cells, defined as a **fixed pooled-TRAIN quantile** of `msofar_atr` (resp.
  `m_sofar/p75_thr`). Candidate grid **pre-declared: U ∈ {p85, p90, p95}** of the band-core pooled
  TRAIN distribution. **Locked-U selection rule (pre-registered, mechanical):** lock `U` at the single
  grid percentile that **maximizes the number of band-core domains that are "improved"** (per the
  per-domain criterion below) under M-GLOBAL; ties broken toward the **least restrictive** percentile
  (highest retention). Threshold selection on TRAIN is the explicit purpose of a TRAIN-design
  experiment; it is never selected on TEST/holdout. This is the **only** arm eligible to be frozen.
- **M-PERCELL — per-cell tuned threshold (diagnostic ceiling; NEVER deployed).** Best `U` per cell on
  TRAIN. Reported solely as the **overfit ceiling**; never carried to the holdout, never described as
  deployable performance.

## Metrics & per-cell "improved" definition (TRAIN, real prices)

For each arm vs the unfiltered `N-PARTIAL-V2A` baseline, on the retained events per cell:
- **raw mean** `r_e` and its 1σ block-bootstrap CI low (the EXP-071 failing leg — the leg to FIX);
- **median** `r_e` and 1σ CI low (the leg EXP-071 passed — to PRESERVE);
- **beats-RM-native** 1σ CI low (the EXP-060B substrate property — to PRESERVE);
- **retained event count** and **retention fraction** vs baseline.

**Per-cell "improved" (pre-registered, the joint economic criterion — EXP-074 Lesson 2's correct
instrument):** a cell is improved under an arm iff **all** hold simultaneously on retained events:
1. raw-mean 1σ-CI-low **> 0** (fixes the failing leg), **and**
2. median 1σ-CI-low **> 0** (median edge preserved), **and**
3. beats-RM-native 1σ-CI-low **> 0** (substrate property preserved), **and**
4. retention **≥ 70%** of the cell's baseline events **and** ≥ 30 retained events absolute.

A filter that lifts the mean only by gutting the sample, or by breaking the median/beats-RM legs,
does **not** count as improved. The joint requirement is deliberate: because high exhaustion both
creates the q05 tail and *raises* the median, the cap necessarily trades tail-suppression against
median-erosion, and is credited only when the net is positive on every leg.

## Per-domain binding metric & verdict (EXP-074 Lesson 1 — per domain, never pooled)

A cell is **powered** when its baseline `r_e < q05` tail cell has ≥ 30 events (EXP-074 convention).
For each band-core domain (15m/30m/1h), over its powered cells, report under each arm:
- **improved-cell share** = fraction of the domain's powered cells that are "improved";
- **baseline improved-cell share** (same criterion on the unfiltered arm);
- **uplift** Δ = (capped share − baseline share) — the cap must **add** improved cells, not inherit them.

A domain is **"improved by the cap" (M-GLOBAL)** iff its uplift Δ **≥ +0.15** with capped share ≥ 0.50
and **no retention violation** at the locked `U`. A domain is **"hurt"** iff Δ ≤ **−0.10** (a global
cap that breaks a domain). The band-pooled improved-share is computed too but is **disclosed-only**.

**Overfit premium (headline diagnostic):** per band-core domain, `premium = (M-PERCELL improved share
− M-GLOBAL improved share)`; reported per domain and averaged over the band core.

## Success / Failure / Inconclusive (routing — pre-stated, concrete thresholds pinned)

This is a **TRAIN-design** experiment; it routes whether a one-shot holdout-confirm is worth the look.
Read the **per-domain** improvement vector jointly; **never** a band-pooled average.

- **FILTER_PROMISING** → under **M-GLOBAL** (deployable): **≥ 2 of 3** band-core domains "improved"
  (Δ ≥ +0.15, share ≥ 0.50, retention OK), **no** band-core domain "hurt" (Δ ≤ −0.10), **and** the
  band-core mean **overfit premium ≤ 0.20** (M-GLOBAL captures most of the M-PERCELL ceiling). ⇒
  freeze the global filter (band-restricted to the domains where it holds) and route to a **separate**
  one-shot sealed-holdout-confirm experiment (its own EXP-ID / D0; fresh strata only — never the
  EXP-071-consumed TEST strata).
- **FILTER_OVERFIT** → M-PERCELL shows domain uplift but **M-GLOBAL improves < 2 band-core domains**,
  OR the overfit premium **> 0.20**, OR M-GLOBAL **hurts** any band-core domain. ⇒ the edge is mostly
  mined / not uniformly deployable; **do not** spend the holdout; routes toward closing CAND-001 or a
  band-restricted re-scope.
- **FILTER_INEFFECTIVE** → even **M-PERCELL** fails to reach Δ ≥ +0.15 in **any** band-core domain. ⇒
  the exhaustion cap is not a lever; supports closing CAND-001 cleanly.
- **INCONCLUSIVE_POWER** → fewer than 2 band-core domains have ≥ 5 powered cells. ⇒ no routing change.

## Complexity Budget

- Statistical/association measures: **≤ 3 families** (paired baseline-vs-filtered raw-mean/median
  effect; beats-RM contrast; block-bootstrap CI as the uncertainty wrapper) across the 4 arms.
- Visualisations: **≤ 6** (per-domain improved-share baseline-vs-capped by arm; raw-mean shift global
  vs per-cell; overfit-premium by domain; retention-vs-mean-gain trade-off; U-sensitivity
  (p85/p90/p95) curve per band-core domain; continuity-cell GBPUSD-5m before/after).
- New modules: **1** experiment-local module under `EXP-075/code/`; reuse frozen EXP-068/074 machinery
  by import; **no** new/modified shared `xen/` module.

## Data Requirements

Reuse the EXP-074 TRAIN resolution path per cell; add the exhaustion-cap gate to `cond`; recompute the
metric vector on retained events per cell × arm. Resolve all 99 cells for disclosure; bind on the
band-core domains. `tqdm` over the cell loop. **No holdout, no TEST.**

## Registry / Governance (preconditions)

- **Candidate family**: CF-HA-HARAMI-001 stays `REGISTERED / OPEN`; CAND-001 disposition deferred to
  this design + its later holdout confirm. EXP-075 registers **no** new candidate branch (it designs
  a prospective filter; registration occurs only if confirmed on the holdout).
- **Multiplicity registry**: **HYP-028 / EXP-075** is registered (Phase 016 batch) — object =
  MA-native harami events under an exhaustion-cap gate, TRAIN-only, **0 candidate slots, 0 counted
  TEST reads**, 4 design arms (F1/F2 × M-GLOBAL/M-PERCELL), pre-declared U-grid {p85,p90,p95}. The
  conditional row is **ACTIVATED** by EXP-074's q05-tail finding (framing-resolved; not a formal
  SEPARATOR_FOUND — see Hypothesis).
- **TEST-read ledger**: unchanged — EXP-075 spends **no** counted read (TRAIN-only); holdout sealed.
- **Phase alignment**: authorized by **`D0-amendment-007-exp-075-train-design-followup.md`** (revised
  2026-06-19), which records (a) the proceed is on the framing-resolved q05-tail evidence with the
  tail framing pre-registered a priori (EXP-074's gate is **not** retro-edited), (b) M-PERCELL is
  diagnostic-only and never deployed, (c) per-domain (not pooled) evaluation is binding, and (d) the
  holdout confirm is a separate future experiment on fresh strata.

## Suggested Direction

Resolve all 99 cells' TRAIN `N-PARTIAL-V2A` events with frozen machinery; apply F1/F2 × M-GLOBAL /
M-PERCELL exhaustion caps; compute the metric vector + retention per cell × arm; aggregate to the
**per-band-core-domain** improved-share, uplift, hurt-check, and overfit premium; lock M-GLOBAL `U` by
the pre-registered rule; route per the pinned thresholds. Lead with M-GLOBAL (deployable); use
M-PERCELL strictly as the overfit ceiling. Report GBPUSD-5m as the continuity cell and the band-pooled
number as disclosure only.
