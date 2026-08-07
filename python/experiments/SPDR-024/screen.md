# SPDR-024 — Screen record

- **Experiment:** `SPDR-024` — breakout baseline characterisation on estimands that can see the effect
- **Family / registration:** `CF-VOLDIR-001` — checkpoint-018 item 7b / Step 3b
- **Checkpoint:** `2026-07-25-018-trade-opportunity-capture-geometry`
- **Band:** TRAIN. TEST and the global 30% holdout were never loaded.
- **Vehicle:** NautilusTrader `BacktestNode`, realistic fills, no vectorisation (D10)
- **Cells:** 4 — 2 signal domains (H1, H4) × 2 universes (cTrader, crypto), run and reported independently, never pooled (OD-2)
- **Date of this record:** 2026-08-07

**NO disposition is taken here.** This document is a neutral record of what ran and what exists. It
contains no interpretation, no effect values, no counts of results, and no verdict. The interpretive
read is `analysis.md`; the interpretation is the operator's.

**Status.** This file replaces two earlier versions. The first carried effect values, result-band
counts and causal claims, which is outside a screen record's boundary in this programme; the second
was rewritten after a review found the analysis layer was labelling rows by their power. The
emissions were not affected by either correction and were not re-run; the analysis artifacts were
regenerated. Both corrections are itemised in `implementation-notes.md` §6.

---

## Spread limitation

Reproduced from each run's own disclosure (`config.json`, `run_summary.json`, all four cells,
identical):

```text
SPREAD-COST-DISCLOSURE
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: reported cost understates total cost; reported net performance is overstated
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

Plainly: **no cost of any kind is charged in this run** (OD-4 / D9). Spread is not charged at all,
and the declared fees/funding scope is itself zero here. Every figure in every artifact is gross, no
output may be read as net, and no output uses the words fully-net, cost-complete, tradable or
deployable. In place of charging cost, every effect emits `breakeven_spread_rt_bps` at that arm's
own round-trip count, labelled `NON_EMITTED_SCENARIO` (M7).

---

## 1. What ran

38 arms per cell: 24 selection arms plus the fixed native comparator (DIRECT only, `REVERSE` dropped
per OD-16), and 12 management arms plus the fixed unit-size comparator and the uncapped arm (SIZE
only, per OD-11 / OD-15).

Each cell is four engine passes: the full arm grid, the arm A / arm B hold phase, a future-shifted
twin for the leak tripwire, and an independent single-worker replay for the determinism check.

| Cell | catalog | episode rows | closed episodes | distinct origins | censored |
|---|---|---:|---:|---:|---:|
| cTrader H1 | `data/catalog_ctrader` | 762,318 | 59,168 | 20,061 | 1 |
| cTrader H4 | `data/catalog_ctrader` | 207,290 | 17,429 | 5,455 | 1 |
| crypto H1 | `data/catalog` | 3,882,080 | 273,650 | 102,160 | 49 |
| crypto H4 | `data/catalog` | 1,033,372 | 63,553 | 27,194 | 22 |

**Rows are not trades.** The episode table carries one row per arm per origin. Every sample-size
statement in `analysis.md` uses a separately named population, never a row count.

Positions still open at the TRAIN fence are reported `CENSORED` and excluded from paired reads. None
was closed at a fence price.

---

## 2. Emission requirements, and where each one landed

The design's actual deliverable (§5). Each is a column or table that exists, or does not.

| # | Requirement | Status |
|---|---|---|
| E1 | Realised regime label per origin and per episode, causal at `<= t-1` | present — `regime_state`, `regime_episode_id` |
| E2 | Counterfactual outcome for declined origins | present — `counterfactual_outcome_bps`, `counterfactual_source` |
| E3 | A TARGET metric not monotone in target distance | emitted `NOT_APPLICABLE_NO_TARGET_ARM`; no TARGET arm exists in this run |
| E4 | `exit_reason` and `entry_ts` plumbed through | present |
| E5 | Realised hold duration in domain bars + cap-bind flag | present; `hold_cap_bars` is null — see §4 |
| E6 | Capital-normalised outcome alongside per-notional bps | present — `capital_normalised_return_bps` |

**Admission is the stop fill** (design §2 OBJECT-IDENTITY). `order_created` is emitted beside
`admitted` so the two events stay separable, and `rejection_class` distinguishes an origin that
never triggered from one whose order was created and expired unfilled.

**The separately named populations** are emitted on every estimate row: `eligible_origin_n`,
`entry_fill_n`, `close_n`, `common_fill_n`, `common_close_n`, `effective_origin_blocks`,
`effective_trade_blocks`. A count is null where its population does not apply to that channel, and
is never filled in from another population.

**No result label is emitted anywhere.** Every row carries estimate, uncertainty, population count,
effective count and MDE, and nothing else.

---

## 3. Integrity — every cell, every gate

Regenerated 2026-08-07 from freshly re-run shift and replay emissions. All four cells:

| Gate | cTrader H1 | cTrader H4 | crypto H1 | crypto H4 |
|---|---|---|---|---|
| Estimand validation `blocking_pass` | true | true | true | true |
| Self-check HARD checks (declared / run / failed) | 17 / 17 / 0 | 17 / 17 / 0 | 17 / 17 / 0 | 17 / 17 / 0 |
| Determinism — artifacts compared / differing | 41 / 0 | 41 / 0 | 217 / 0 | 217 / 0 |
| Leak tripwire — arms compared | 34 | 34 | 34 | 34 |
| Leak tripwire — arms whose shifted edge survives | 0 | 0 | 0 | 0 |
| Leak tripwire — admission rows changed by the shift | 3,156 | 871 | 12,664 | 3,568 |
| Leak tripwire — committed-capital rows changed | 51,468 | 14,668 | 246,756 | 68,286 |
| E2 — declined origins carrying a counterfactual | 13,487 | 3,933 | 80,390 | 20,735 |

**Why these were regenerated.** The self-check previously on record was produced before the
admission-at-fill correction, so it attested to an emission that no longer matched the one it
guards: it counted 9,003 declined-with-counterfactual origins on cTrader H1 against the current
13,487, the difference being the `EVALUATED_DECLINED_ORDER_EXPIRED` population that
admission-at-fill makes visible. The self-check reads `results/runs/*/shift` and
`results/runs/*/replay`, both deleted on 2026-08-06 with no `determinism_reference.json` persisted
in their place, so neither HARD check could be re-run from what remained. Both passes were
re-created and all four self-checks re-run.

**Lesson, recorded rather than left implicit.** The 2026-08-06 pruning decision reasoned that the
deleted passes reproduce exactly, which is true, and concluded they were therefore safe to remove,
which did not follow: it left two HARD checks un-rerunnable without an hour of engine time.
`run_cell.py --prune` is off by default and says why. A persisted `determinism_reference.json` would
have preserved one of the two at negligible cost, and the SPDR-021/022/023 handoff raised exactly
this caution — "The old claim that two analysis passes were hash-identical is not independently
auditable because no persistent second-pass manifest was saved."

The HARD-check count is asserted and reconciled against the design's list by name (L-52 / P-23).
Every check reads an emitted artifact, so a missing or empty one fails rather than passing silently.
Columns are tested finite, not merely non-null.

Determinism compares a three-worker run against an independent one-worker replay. Two fields are
normalised before hashing — a wall-clock stamp and the declared worker count — by name, with the
normalisation recorded in the artifact.

**Two recorded limits on the tripwire, and one on re-running it.** The statistic is scale-invariant
in the delta series, so a strictly proportional leak would not trip it. The artifact also records
how many arms carried a causal effect above their own detection floor, because an arm with no edge
has nothing to collapse. And the tripwire and determinism verdicts on record were produced before
the 2026-08-07 correction: both read `results/runs/*/shift` and `results/runs/*/replay`, which were
deleted on 2026-08-06, so re-verifying either requires regenerating them (roughly 40 minutes;
determinism is what makes that reproduce exactly).

---

## 4. The hold cap was not set — the rule returned NOT_APPLICABLE in all four cells

Arm B removes the holding cap. With the four capture devices excluded (OD-11 / OD-15), the strategy
has no exit of its own, so the safety ceiling becomes arm B's only exit: every closed arm-B position
sits at exactly 120 domain bars and the ceiling binds 100%, against its declared 2% tolerance.

No value on the declared grid `{2, 4, 8, 12, 24, 48}` binds 5% or less, so **no cap was set**. The
rule was applied mechanically and reported as it fell out; the comparison arms keep the declared
one-bar hold, and the ceiling bind rate is flagged to the operator rather than reinterpreted.

Two consequences, recorded rather than worked around. **M4's shared cap is untested apparatus here**
— there is no absorbing device for it to fix. And the decay curve (H3) is a single point, so it
cannot calibrate a successor's horizon; doing that needs per-bar mark-to-market on arm B, which is a
new measurement and therefore a successor item.

---

## 5. Preflight items, computed not recalled

- **P-2, H4 origin counts, measured:** H4 supplies 24% (crypto) and 29% (cTrader) of H1's origins,
  against the design's assumed ~1/4.
- **P-3, conversion pin, computed from TRAIN data:** ATR(20) on the signal-domain bar lagged `[t-1]`,
  TRAIN median in bps, per instrument and per domain — EURUSD 12.83 (H1) / 25.90 (H4), XAUUSD 22.96
  / 45.32, USTEC 34.50 / 69.79.
- **P-5, dependence, both axes measured:** cross-symbol contemporaneous correlation averages +0.38
  in crypto (max 0.84) and +0.31 in cTrader, which no time-blocking treatment addresses — hence
  symbol-clustered intervals under all three treatments. The paired-difference dependence is emitted
  per arm per symbol and was computed before any effect was read. `analysis_summary.json` carries a
  `dependence_premise_check` verdict, including where design §10's premise does **not** hold.
- **P-1, per-cell MDE:** recomputed from realised counts under all three variance treatments and
  emitted on every row.

---

## 6. Artifacts

Per cell, under `results/analysis/<cell>/`:

```
episodes.parquet                     one row per arm per origin
baseline_characterisation.parquet    arm A alone, per symbol and pooled (OD-3)
paired_difference_dependence.json    P-5, computed before any effect
scale_channel_estimates.parquet      SIZE arms, three variance treatments, three regime strata
selection_channel_estimates.parquet  admission rules against the E2 counterfactuals
pool_filter_ladder.parquet           OD-9 concentration ladder, both channels, all three steps
analysis_summary.json                cell identity, populations, disclosures
inherited/                           the SPDR-021/022/023 risk-shape tables, retained (OD-6)
```

Plus `results/preflight/`, `results/selfcheck/`, `results/performance/`,
`results/golden_traces.json`, `results/*_cap_rule.json`, `results/estimand_validation_*.json`.

---

## 7. What this record does not do

No verdict, no disposition, no arm ranking, no family action, no tradability claim, no TEST or
holdout read, and no effect values. The per-stratum quantification, the observations stated
symmetrically, and the three variance treatments side by side are in **`analysis.md`**.
