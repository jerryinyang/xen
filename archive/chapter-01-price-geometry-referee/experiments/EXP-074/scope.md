# Experiment: EXP-074 — TRAIN-Only Substrate-Wide Loser-Tail Characterization of the 99-Cell MA-Native Harami N-PARTIAL-V2A (CF-HA-HARAMI-001 / HYP-027)

## Hypothesis

**Exploratory (no candidate slot, no TEST/holdout read).** EXP-071 returned
`TEST_NOT_CONFIRMED` on the binding 6-cell `N-PARTIAL-V2A` family: 0/6 cells cleared the
composition conjunction, and GBPUSD-5m — the lone Holm-significant median+beats-RM survivor —
was **killed solely by the raw-mean leg** (`pv_mean_ci_low_1s < 0`), with the
`mean_recoverable=false` diagnostic showing the failure **survives removal of the adverse stop**,
i.e. the loss tail is *entry-structural*, not exit-induced. The binding family is too small (6
cells) to tell whether that entry-structural loss tail is a GBPUSD-5m idiosyncrasy or a property
of the MA-native harami **substrate**. This experiment therefore characterizes the loss tail
across the **entire 99-cell MA-substrate matrix**, not the hand-picked EXP-071 survivors.

**Primary exploratory question (substrate-wide):** On the **TRAIN** stratum, across the **full
99-cell MA(20,50)-native harami matrix**, which causal, entry-time features separate the
large-loss tail of `N-PARTIAL-V2A` per-event returns from the rest of the distribution — and do
any such separators replicate across a material share of the substrate (rather than holding in a
single cell)?

**Two pre-registered lead (mechanism-grounded) sub-hypotheses:**
- **H1 — exhaustion-magnitude bound.** The loss tail concentrates at *extreme* `m_sofar/atr_entry`
  (and/or large excess above the `/STRONG-STAT` p75 bar): reversals taken against a counter-move
  that has already run very far keep running. The current substrate gates a *lower* bound
  (`m_sofar ≥ p75`) but imposes **no upper bound / maturity cap**.
- **H2 — harami-polarity disagreement.** The loss tail concentrates where the harami's own
  HA polarity (`HA0Direction`/`HA1Direction`) **disagrees** with the MA-segment reversal
  direction `rd`. Polarity is computed by the detector but **currently unused** in conditioning.

All other causal features (below) enter as **additional characterizing dimensions** — exploratory,
ranked-and-reported, no threshold selected.

## Question

Before deciding whether an exhaustion-cap / tail filter is worth designing (EXP-075) and
eventually spending the sealed holdout on, what (if anything) causally distinguishes the entries
that produce the large losses dragging the `N-PARTIAL-V2A` raw mean below zero — **across the
whole MA-native substrate**, not just the EXP-071 survivors — and is any such separator a
substrate-wide property or cell-local noise?

## Scope Boundaries

- **Data Views**: 1-minute time bars → MA(20,50)-segment domain bars (per cell domain ∈
  {5m,15m,30m,1h,2h,4h}), Heiken Ashi candles for harami detection. **Real-price outcomes only**
  (`RealOpen/High/Low/Close`); HA prices used only for harami detection, never for returns.
- **Parameters**: All frozen from EXP-068/EXP-071 — MA(20,50); `/STRONG-STAT` trailing-20, p75;
  Wilder ATR(14); `N-PARTIAL-V2A` exit geometry; binding object `nat`. **No parameter is tuned
  in this experiment.**
- **Instruments / cells**: **the full 99-cell MA-substrate harami matrix** (the EXP-060B /
  EXP-068 grid — 17 instruments × 6 domains minus the structurally-excluded cells, 99 reportable).
  No cell is hand-picked or pre-excluded by prior outcome. GBPUSD-5m is reported as a **named
  continuity cell** for comparison with EXP-071/074-prior, but it is **not** the binding object —
  the verdict is **substrate-wide** (see Success/Failure). EURUSD cells are characterized like any
  other (this is TRAIN-only with 0 TEST reads, so the EURUSD instrument-wide TEST cap does not
  apply to a TRAIN diagnostic; EURUSD carries no special status here and is reported, not screened).
- **Time range**: **TRAIN slice only** — `[0, train_cutoff)` where `train_cutoff = int(0.7 ×
  analysis_cutoff)` and `analysis_cutoff = int(0.7 × total)`, per file (frozen EXP-068/071
  convention; `int` truncates downward → fence-conservative). The **next-21% TEST
  stratum is NOT read** (**0 counted TEST reads**). The **final-30% global holdout is never loaded**.
- **Global holdout**: final 30% of each file must not be loaded, inspected, or used.
- **Look-ahead prevention**: every feature uses only data available at or before the entry-bar
  `CloseTime` — binding pivot is the last move confirmed at `ConfirmTime ≤ t_i`; `m_sofar` uses
  the entry bar's own real close; the `/STRONG-STAT` window is trailing; ATR is trailing. The
  per-event return `r_e` is the realized `N-PARTIAL-V2A` outcome (already causal in EXP-068).
  **No ZigZag position-in-move feature** (EXP-050/HYP-003: requires the move's end pivot =
  future information; excluded by construction).
- **Real-price outcome discipline**: returns from `RealOpen/High/Low/Close` only.
- **Exclusions**: no TEST read, no holdout read, no parameter tuning, no filter committed (this
  experiment *characterizes*; any filter is a separate future experiment — EXP-075 — with its own
  D0), no new shared `python/src/xen/` module.

## Causal entry-feature set (characterizing dimensions)

All computable at entry from the frozen EXP-068 machinery (`_ma_context`, `live_in_progress_state`,
`live_strong_stat`, `benchmark_barriers`, ATR, the HA harami frame):

| # | Feature | Source | Lead? |
| --- | --- | --- | --- |
| 1 | `m_sofar / atr_entry` | state, atr | H1 |
| 2 | strong-stat excess: `m_sofar / p75_thr` (and `m_sofar − thr`) | live_strong_stat | H1 |
| 3 | harami-polarity agreement: `HA0Direction == rd` (and `HA1Direction == rd`) | detector, state | H2 |
| 4 | trailing move dispersion: `mad / median` of trailing-20 magnitudes | live_strong_stat window | — |
| 5 | `fav_dist / atr_entry` | benchmark_barriers, atr | — |
| 6 | move age in bars: `entry_idx − confirm_idx[k]` | seg | — |
| 7 | binding move count `k` | state | — |
| 8 | `atr_entry` trailing percentile | atr | — |
| 9 | harami inner-candle compression: inner body /(prior body), inner range / atr | detector | — |
| 10 | entry-bar real range / `atr_entry` | ohlc, atr | — |
| 11 | trade direction `rd` (long/short asymmetry) | state | — |
| 12 | MA(20,50) separation / slope at entry | seg / MA | — |
| 13 | hour-of-day / session bucket (Asia/London/overlap/NY) | entry_epoch | — |
| 14 | day-of-week | entry_epoch | — |

## Tail-target definitions (all three; exploratory, pre-registered)

Per the operator direction, characterize against **all three** target framings so the read is
robust to the tail definition. **All three are computed per cell** (each cell's own empirical
distribution):

- **T-A — extreme + sign (primary).** `r_e < q05` (extreme losers) and, co-primary, `r_e < 0`
  (all losers). Binary membership; feature separation reported for both cutoffs.
- **T-B — mean-below-median contributors.** Membership = `r_e < median(r_e)` (the left mass that
  produces the winsor⁺/mean⁻ gap).
- **T-C — continuous association.** Rank association of each feature with continuous `r_e`
  (no cutoff).

A feature is reported as a candidate separator **in a cell** only if its separation is
**directionally consistent across T-A/T-B/T-C** — this is the anti-p-hacking guard (consistency
across framings, not a tuned threshold).

## Success / Failure Criteria (per-domain, dual-metric — BINDING)

This is a **characterization** experiment; the verdict routes the family decision and EXP-075's
design, it does not itself select a filter. The binding object is **per domain** (5m / 15m / 30m /
1h / 2h / 4h), **not** a single pooled substrate number: pooling 5m noise and underpowered 2h/4h
against the 15m–1h core masks domain structure (the substrate-wide read is retained only as a
disclosed secondary line).

Two metrics are reported **per domain**, because they answer different questions:
- **Per-cell any-feature separability rate** — fraction of the domain's powered cells with a
  per-cell candidate separator on *any* feature (point `|effect| ≥ 0.15` ∧ cross-framing sign
  consistency). Answers *"is the loss tail separable at all here?"*
- **Per-feature single-lever breadth** — for each feature, the share of the domain's powered cells
  in which it is a **cell-level candidate separator** (point `|effect| ≥ 0.15` ∧ 1σ block-bootstrap
  CI on the material side of 0.15 ∧ cross-framing sign consistency), plus the within-domain median
  effect CI. Answers *"is there one uniform lever?"* — the question EXP-075's global cap needs.

A cell is **powered** when its `r_e < q05` tail cell has ≥ 30 events; below that it is excluded
from both metrics' denominators.

Four-tier **per-domain** verdict:
- **SEPARATOR_FOUND** (→ a uniform lever exists; strongest input to EXP-075): ≥1 feature has
  single-lever breadth `≥ 0.50` of the domain's powered cells **and** a sign-consistent within-domain
  median effect CI on the material side of 0.15. Preference (not requirement) to H1 (exhaustion
  magnitude) / H2 (polarity).
- **SEPARABLE_NO_UNIFORM_LEVER** (→ tail separable but via heterogeneous, cell-specific features;
  a *global* cap is weakly supported — a per-cell/per-domain or feature-blended design is the most
  EXP-075 can justify here): per-cell any-feature separability rate `≥ 0.50` but **no** feature
  reaches the single-lever breadth bar.
- **NO_SEPARATOR** (→ tail not separable in this domain on available entry information): per-cell
  rate `< 0.50` and no uniform lever.
- **INCONCLUSIVE_POWER** (→ no routing change for this domain): **< 5 powered cells** in the domain.

The CF-HA-HARAMI-001/CAND-001 and EXP-075 routing reads the **domain verdicts jointly**: a domain
returning SEPARATOR_FOUND or SEPARABLE_NO_UNIFORM_LEVER on H1 motivates an EXP-075 cap *restricted to
that domain band*; all-NO_SEPARATOR / all-INCONCLUSIVE supports closing the path without spending the
holdout.

## Complexity Budget

- Max statistical/association measures: **3 families** (rank-biserial/AUC for binary T-A/T-B;
  Spearman for T-C; bootstrap CI on the per-cell effects and on the cross-cell median) — applied
  across the feature set and the 99 cells.
- Max visualisations: **6** (cross-cell effect distribution per lead feature [forest/violin over
  cells]; substrate-wide separator-share bar by feature × framing; H1 conditional `r_e` by
  `m_sofar/atr` bin pooled-with-cell-facets; H2 polarity-agreement contingency pooled; session/
  `m_sofar`-bin loss-rate heatmap; GBPUSD-5m continuity-cell single-cell ranking for comparison
  with EXP-071).
- Max new code modules: **1** experiment-local module under `EXP-074/code/`; reuse frozen
  EXP-068 / EXP-071 machinery by import; **no** new or modified shared `xen/` module.

## Data Requirements

Reuse the EXP-068/EXP-071 TRAIN-side resolution path (TRAIN bars warm MA/STRONG-STAT/ATR/segment
state), but **evaluate entries in the TRAIN window only** (`entry_epoch ≤ train_end`) — the mirror
of EXP-071's TEST mask — applied to **all 99 cells**. Extract, per qualifying `N-PARTIAL-V2A`
entry in every cell: the realized `r_e` and the 14-feature causal vector above. No holdout, no
TEST. The 99-cell loop must use `tqdm` progress.

### Standard Loading Pattern (TRAIN-only)

```python
scan = pl.scan_parquet(path).sort("CloseTime")
total = int(scan.select(pl.len()).collect().item())
analysis_cutoff = int(total * 0.7)
train_cutoff    = int(analysis_cutoff * 0.7)
train_1m = scan.slice(0, train_cutoff).collect()   # TRAIN only; TEST + holdout never sliced here
```

## Registry / Governance

- **Multiplicity registry**: the **HYP-027 / EXP-074** row (Phase 016 diagnostic batch) is updated
  from "GBPUSD-5m primary + 5 disclosed family cells" to **the full 99-cell MA-substrate matrix**,
  TRAIN-only, **0 candidate slots, 0 counted TEST reads**. The expanded comparison surface (14
  features × 3 framings × 99 cells) is recorded; the anti-multiplicity stance is the substrate-wide
  share rule + cross-cell median CI + the two pre-registered leads (not a per-(cell×feature)
  family-wise correction). Analogous prior: EXP-050 (harami-in-context characterization), EXP-070
  (TRAIN-only calibration).
- **Candidate family**: CF-HA-HARAMI-001 stays `REGISTERED / OPEN`; CAND-001 disposition deferred
  to this experiment's outcome (SEPARATOR_FOUND → motivates EXP-075 exhaustion-cap design;
  NO_SEPARATOR → supports closing the path).
- **TEST-read ledger**: unchanged — EXP-074 spends **no** counted read (TRAIN-only).
- **Phase alignment**: the original EXP-074 authorization (`D0-amendment-005`) scoped the GBPUSD-5m
  + 5-cell family. The substrate-wide expansion to all 99 cells is authorized by a **new addendum,
  `D0-amendment-006-exp-074-substrate-wide-expansion.md`** (append-only; amendment-005 retained,
  not edited) — to be ratified at the pre-execution governance gate before any code runs.

## Suggested Direction

Resolve all 99 cells' TRAIN `N-PARTIAL-V2A` events with the frozen machinery; build the per-event
`(r_e, features)` table per cell; rank every feature by its separation of the three tail targets
within each cell; bootstrap CIs on the per-cell effects; aggregate to the cross-cell effect
distribution per feature and compute the substrate-wide separator-share. Lead the interpretation
with H1 (exhaustion-magnitude bound) and H2 (polarity agreement), since those are mechanism-grounded
and directly actionable as causal filters — and are the mechanism EXP-075 will design against.
Report GBPUSD-5m as a continuity cell alongside the substrate read.
