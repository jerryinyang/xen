# EXP-094 — Scope: 4h Readiness + Falsification Re-Screen (RSI-2 fade / EXIT-RCT)

**Phase 021 (CF-MR-001 batch 2) · `CF-MR-001/HYP-002` · governed by `D0-amendment-004` (FROZEN 2026-06-24).**
TRAIN-only · 0 candidate slots · 0 counted TEST reads · holdout sealed.

## Signal-registry precondition (checked)

- **Family:** `CF-MR-001` — `ADMITTED (BINDING)` (G-020). Lever = bare RSI-2 fade (CORE) + EXIT-RCT capture
  geometry. First (and only) candidate slot consumed at G-020.
- **Countable item:** EXP-094 is **registered** in the Phase-021 multiplicity batch (`multiplicity-registry.md`)
  as the 4h readiness + falsification re-screen; **0 new candidate slots** (4h is a domain expansion of the
  admitted lever, `D0-amendment-004` §3.2). The new §4(c) paired-Δ shuffled-entry statistic is a **falsification
  null** → must be **bite-checked GREEN** at D0 before any result-producing run.
- **TEST-read ledger:** EXP-094 reads the **TRAIN sub-split only** → **no counted TEST read**; all 4h strata stay
  0/2 open (TRAIN-only disclosure convention, as EXP-089/090/091). The final-30% global holdout is never sliced.

## Question (one falsifiable leg, three measurement components)

**Does the bare RSI-2 fade's net-of-cost EXIT-RCT edge on 4h reflect the fade *entry signal* — beating a
matched-random/shuffled entry — or is it generic ATR-normalized oscillation harvesting that EXP-089's
dead-by-absence finding (4h 1/14) correctly flagged?**

The archived hunch `TEMP-091` showed EXIT-RCT net-clears 12/12 instruments on 4h (mean & median positive). But
on 4h only the proactive small resting-limit (RCT) is positive while the reactive same-signal analog
(RSI-revert-on-close) and every other arm are net-negative — consistent with capturing noise reversion, not the
fade. This experiment runs the falsification the hunch lacked.

## Hypothesis

- **H₀ (null, the worry):** on 4h, EXIT-RCT applied to **random/shuffled entries** (matched count and
  long/short mix) nets ≈ the same as applied to the **real fade entries** — the edge is exit geometry, not the
  signal. (4h stays closed, EXP-089 reaffirmed.)
- **H₁:** the real fade entry's net-of-cost EXIT-RCT expectancy **materially exceeds** the matched-random
  baseline (paired Δ lower bound > 0) in a quorum of 4h cells — EXP-089's ~3-bar MFE_med availability metric
  missed a real, RCT-capturable 4h geometry. (4h admitted as a domain expansion.)

## Data, instruments, features, parameters (all frozen — inherited, NO tuning)

- **Data view / domain:** 4h (240-minute) domain bars, holdout-fenced `build_domain_bars`, built from VAL-005
  5-year 1-minute base bars. 1-minute base series is the intrabar fill source. Real OHLC throughout
  (`RealOpen/High/Low/Close`); no HA/Renko prices in any metric.
- **Instruments:** the 13 `D0-amendment-003` cost-table instruments (EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD,
  NZDUSD, EURJPY, GBPJPY, AUDJPY, XAUUSD, USTEC, US2000, JP225). 4h member set is **defined by the readiness
  leg (a)** — JP225-4h flagged a priori (failed to build in TEMP-091; US500-4h/JP225-4h were `COVERAGE_EXCLUDED`
  on 4h at EXP-080); expected ≈12 member cells.
- **Entry (frozen, inherited byte-for-byte):** `RSI(2)` Wilder on domain Close; long `RSI₂<10`, short
  `RSI₂>90`. No re-tuning.
- **Exit slate (frozen, the full EXP-091 D2 slate — for the file drawer):** EXIT-RCT (primary, the binding arm),
  EXIT-ERT, ATR triple-barrier, RSI-revert-on-close, fixed-bar, favourable partial/trail. Single frozen
  parameter point each. Adverse side identical across arms: `2.0×ATR(14)` stop + EXP-089 MR-tempo cap.
- **Intrabar fill:** `xen.intrabar_fill` engine, timestamp-aligned domain→1m, causal order-of-touch
  (conservative adverse-first tie-break), real touched fill prices; 1m slice clipped by **timestamp** at the
  TRAIN edge.
- **Cost (frozen):** `D0-amendment-003` Phase-021-local conservative round-trip `RT_i` + financing `F_i=0`
  (domain-invariant in bps; covers all 13 instruments). Net = gross − cost in ATR(14) units. Shared
  `xen.capgeo_cost.COST_CONSTANTS` not mutated.
- **Matched-random / shuffled-entry baseline (the new §4(c) component):** for each 4h cell, draw entries at
  **matched per-cell count and matched long/short direction mix** at random eligible TRAIN bars (the EXP-089
  `SUB-RANDOM` direction-matched construction reused), resolved through the **identical** EXIT-RCT target +
  adverse side + 1m fill + cost — exit geometry held fixed so the contrast isolates the entry signal. Seeds
  fixed and recorded; exact resampling/pairing mechanics finalized in the analysis plan (Stage 2).
- **Master seed:** `20260623` (shared with the phase).

## Mandatory exclusion

The **final 30% global holdout is excluded from all analysis.** Within the analysis set, the **TRAIN sub-split
`[0, int(analysis_rows·0.7))` only** is read; the analysis-TEST stratum is **not** sliced (that is EXP-093, if
4h is admitted). The 1m holdout bars are never loaded.

## Measurable criteria (binding outcome rule, from `D0-amendment-004` §4)

Per 4h cell, all TRAIN-only:

- **(a) Readiness:** ≥15 RSI-MR events, deterministic substrate, **finite per-cell EXIT-RCT MDE** under the
  frozen referee. A cell failing → `COVERAGE_EXCLUDED` (retained, with record). Defines the member set.
- **(b) Net exit screen:** a cell net-clears iff net `ci_low_1s` (moving-block bootstrap, Z=1.645) > 0; EXIT-RCT
  passes iff it net-clears in **≥5 cells / ≥3 instruments**.
- **(c) Falsification (binding for admission; null corrected by `D0-amendment-005`):** the binding random arm is
  the **matched favourable-target-distance oscillation null** — a static favourable limit at a distance resampled
  from the real cell's RCT target multiples `{μ_k}`, fired at random times/directions, same adverse/cap/fill/cost
  (favourable by construction). Real-entry EXIT-RCT beats it in a cell iff the paired Δ (real net − random net)
  one-sided lower bound > 0; the real entry **passes** iff this holds in **≥5 cells / ≥3 instruments**. *(The
  original SUB-RANDOM-entry RCT null was found biased toward admission and is retained as a non-binding
  companion — see `D0-amendment-005`.)*

| Outcome | Rule | Disposition |
| --- | --- | --- |
| **ADMIT_4H** | (b) passes **AND** (c) passes | 4h admitted (domain expansion, 0 new slots); real-beats-random 4h RCT cells eligible for EXP-092/093, smallest-defensible. EXP-089 4h dead-by-absence overturned as a metric-specific false negative. |
| **4H_CLOSED_OSCILLATION** | (b) passes **BUT** (c) fails | 4h stays closed, retained. The 4h net-clear is exit-geometry/oscillation harvesting, not the fade — EXP-089 reaffirmed, mechanistically explained. No 4h cell to TEST. (Also flags a mechanism question for the 1h pass.) |
| **4H_EMPTY** | (b) fails | 4h not carried (empty 4h net screen); retained. |
| **INCONCLUSIVE** | positive control fails (test (c) underpowered) **or** < quorum-capable member cells after (a) | Disclosed; neither admit nor refute. |

**Positive control (disclosed companion, required for power assurance, non-binding):** run the same
real-vs-random EXIT-RCT contrast on the **EXP-091 1h clearing cells** (EURUSD/GBPUSD/NZDUSD/US2000/USTEC-1h),
where EXP-089 *did* find availability (1h 11/16). Real is expected to beat random there; if it does **not**, (c)
lacks power → EXP-094 reads INCONCLUSIVE rather than refuting 4h.

## Metric denominators / zero-baseline

- Net per-event expectancy denominators are **resolved events** (finite gross, valid ATR>0, valid holding) per
  (cell × arm × entry-population) — same `keep` mask as EXP-091. Report `n_events`/`n_resolved`/`resolved_frac`.
- The §4(c) contrast is a **difference of two net expectancies (ATR units), not a ratio** — no percentage
  against a zero baseline; the binding figure is the paired Δ one-sided lower bound (ATR), compared to the
  absolute floor 0, exactly as the net screen compares net `ci_low_1s` to 0.
- Matched-random baseline counts are matched to each cell's real resolved counts and directions; report the
  realized random `n` and any shortfall.

## Complexity budget

| Item | Budget |
| --- | --- |
| Binding statistical tests | ≤ 3 (net-screen bootstrap (b); paired-Δ bootstrap (c); 1h positive-control contrast) |
| Visualisations | ≤ 4 (4h net ci_low heatmap; real-vs-random paired Δ per cell; quorum bar; cost decomposition / mechanism) |
| New code modules | **Target 0–1.** Reuse the EXP-090 substrate (`build_cell_context`/`resolve_arm`), `xen.intrabar_fill`, `xen.capgeo_cost`, `xen.ass` bootstrap, and the EXP-089 `SUB-RANDOM` direction-matched generator. At most one small shuffled-entry helper if the EXP-089 generator cannot be reused verbatim. |

## Out of scope (do not expand after approval)

No re-tuning of any frozen constant (entry, RCT/ERT geometry, adverse side, MR-tempo cap, cost table, gate
thresholds). No 15m/1h re-screen (1h enters only as the positive control). No other deferred lever (vol-regime,
contrarian, 25/75, cross-cuts, parameter tuning). No TEST-stratum or holdout read. Follow-up questions get a new
EXP-ID.
