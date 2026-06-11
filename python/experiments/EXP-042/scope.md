# EXP-042 — Track A0 Band-Selection Scan (TRAIN-Only, Descriptive)

**Phase:** 011 (`docs/experiments-docs/checkpoints/2026-06-11-011-per-instrument-foundation/design.md` §5.2)
**Candidate family:** `CF-AVWAP-001` (`/BAND` variant selection; 1 slot consumed at selection if band ≠ 1.0)
**Type:** Exploratory/descriptive (0 statistical tests; mechanical predeclared selection rule)
**Slots / TEST reads:** 0 candidate-screening slots beyond the registered `/BAND` activation; **0 TEST reads**
**Status:** Stage 1 scoped 2026-06-11. G0 PASS recorded (`D0-predeclarations.md`) — TRAIN contact authorized.

## Question (exploratory, no hypothesis)

Which global AVWAP band multiplier in {1.0, 1.5, 2.0, 2.5, 3.0} is selected
by the frozen design-§5.2 rank rule over the 51 TRAIN cells (17 instruments ×
{1h, 2h, 4h}), and what are the selected band's per-cell event rates (for the
new power statements)?

This is a **selection scan**, not an edge claim. The working candidate is
band = 2.0 (not a decision). The output band is frozen for Phase 011 and all
downstream phases; no per-instrument band tuning.

## Strategy / event definition (frozen, faithfulness constraint)

Identical to the EXP-020/028 substrate in every component except the swept
band multiplier and its role in arming: MA(20, 50) regime detector on domain
Close; typical-price AVWAP anchored at regime pivots with `TickVolume ** 0.75`
weights; MAD-band from the anchored typical-price series with multiplier
**b ∈ grid**; pyramid bounces included as independent events
(EXP-029-corrected semantics). No other parameter changes. Streaming/causal
semantics preserved (no look-ahead; event uses only data at or before its
trigger timestamp).

**Entry rule (operator-ratified 2026-06-11, pre-TRAIN-read):** in the frozen
baseline the band plays no role in entry (arm = close on the opposite side of
the AVWAP; trigger = close recrossing the AVWAP), so a naive multiplier sweep
would leave the event population unchanged at every b — the scan would be
vacuous. Phase 011 therefore uses the **arm-at-adverse-band** rule: bullish
arms when a completed close < `AVWAP − b×MADspread` (bearish mirrored:
close > `AVWAP + b×MADspread`); the **trigger is unchanged** (completed close
recrossing the AVWAP in the regime direction). Wider b ⇒ deeper required
pullback ⇒ fewer, stronger events.

**Population-continuity disclosure:** under this rule, b = 1.0 does **not**
reproduce the historical Phase 004–010 event population (which armed at the
AVWAP itself — effectively b = 0 in this parameterization; the design's
"band=1.0 events" phrasing referred to exit targets, not entry selection).
All 5 grid bands define new event populations; prior-result
non-comparability (design §7.5) applies to the whole grid, including 1.0.
Implemented as `xen.avwap.generate_avwap_events(band_multiplier=b,
arm_at_adverse_band=True)`; defaults preserve the frozen baseline exactly.

## Data views, instruments, time range

- **Base data:** 1-minute time bars, `data/timebars/timebars_<symbol>_*.parquet`
  (newest file per symbol), sorted by `CloseTime`.
- **Domains:** 1h (`period_minutes=60`), 2h (`period_minutes=120`), 4h
  (`period_minutes=240`), all via `xen.bar_aggregator.aggregate_ohlc` with
  `min_coverage=0.90` (P7; the frozen 1h/4h convention extended to 2h).
- **Instruments (17):** BTCUSD, EURUSD, USTEC, XAUUSD, GBPUSD, USDJPY,
  USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, US500, US2000,
  DE30, JP225. DE30 used as-is with the truncated-history disclosure (P8;
  history ends 2026-01-16) repeated in every result artifact.
- **Stratum:** **TRAIN only** — first 70% of the first-70% analysis slice,
  per-instrument, 1-minute-row timestamp boundary (R1.3 `train_end_ts`
  convention). TEST rows are never loaded past the boundary computation.

## Mandatory exclusions

- The **final 30% global holdout is excluded from all analysis** — never
  loaded, inspected, or used; lazy chronological slicing before any collect.
- The TEST stratum (last 30% of the analysis slice) is likewise not read.
- No cost overlay, no net figures, no CIs, no per-cell selection, no exit
  logic (forward returns at fixed horizons only).

## Measurements (per band × instrument × domain cell, TRAIN only)

1. **Event count** `n(b, cell)`.
2. **Mean gross forward return in bps** (relative, direction-signed log
   return on real domain Close) at fixed horizons **H ∈ {4, 8, 16} domain
   bars** after the event trigger bar (P3). Events with fewer than H
   remaining TRAIN bars are excluded from that horizon's mean (no spill past
   `train_end_ts`).

**Denominators / zero-baseline:** denominator at each horizon = number of
events with a full H-bar forward window inside TRAIN (duplicate-source
pyramid events each count once as independent events — same convention for
every band, so ranks are comparable). A cell×band with zero qualifying
events at the binding horizon fails the floor by definition (no division by
zero is ever taken; means are reported only when n ≥ 1, ranks only via the
floor rule).

## Selection rule (frozen — design §5.2 + P3; mechanical, no discretion)

1. Within each cell, rank the 5 bands by mean gross forward return at the
   **middle horizon (H = 8)**; rank 1 = best.
2. **Event-count floor:** a band with `n(b, cell) < 30` TRAIN events (at the
   binding horizon's denominator) is imputed that cell's **worst rank**.
3. Selected band = best **median rank across the 51 cells**.
4. Tie on median rank → the **wider band wins**.

## Outputs

- `results/band_scan.parquet` — one row per band × instrument × domain:
  event counts, per-horizon mean gross bps, per-horizon denominators.
- `results/rank_table.csv` — per-cell ranks at H=8, floor imputation flags,
  per-band median ranks, selected band.
- `results/power_statement.csv` — selected band's per-cell TRAIN event rates
  and projected TEST-stratum counts (rate × TEST/TRAIN row ratio; no TEST
  rows read) for the §7.4 power statements.
- `results/run_metadata.json` — boundaries (`train_end_ts` per instrument),
  parameters, determinism hash.

## Success / failure / inconclusive criteria

- **SUCCESS (BAND_SELECTED):** the rule yields a unique band (after
  tie-break); per-cell event rates for the selected band are reported and
  the power statement is produced.
- **DEGENERATE_FLOOR (amended pre-read, 2026-06-11 — F03):** if > 50% of
  cells hit the floor imputation at every band ≥ 1.5, the scan is
  floor-dominated. The rule's selection is still reported, but the **band
  freeze is withheld** pending operator adjudication (a floor-dominated
  selection can be driven by worst-rank ties plus the wider-band tie-break
  rather than by signal). The adjudication chooses between accepting the
  selection with the disclosure or closing the phase early
  (FOUNDATION_NON-TUNABLE path) — it may not re-rank, re-parameterize, or
  extend the grid.
- **INCONCLUSIVE is not an available verdict** — the rule always selects;
  there is no re-parameterization, re-ranking, or grid extension after the
  scan is seen.

## Complexity budget

- Statistical tests: **0**.
- Visualisations: ≤ 3 (rank heatmap across cells; event-count vs band; mean
  gross bps vs band by domain). Plot inputs returned from the analysis pass
  (bounded), no reloads.
- New code modules: ≤ 1 (a parameterized-band event generator entry point
  only if the existing substrate module cannot take the multiplier as an
  argument; otherwise 0).

## Disclosures carried

- Wider-band events are plausibly a near-subset of band=1.0 events on the
  same price data; this scan is TRAIN-only and creates no re-read license
  (ledger §7.1 governs all TEST contact).
- First analytical use of the 13 new-universe instruments (VAL-003 PASS).
- DE30 truncated history (P8). EURUSD TEST-cap/holdout-contamination notes
  do not bind here (no TEST/holdout contact).
- Prior band=1.0 power analyses (EXP-030/033/039) are not transferable; this
  scan's power statement replaces them for Phase 011.
- **Proxy-alignment limitation (F02, disclosed — rule unchanged):** the
  selection statistic is mean **gross** forward return at H=8 with no cost
  overlay and no exits, while the band is frozen for downstream **net**
  portfolio tradability under trained exits. The statistic was deliberately
  predeclared this way at G0 (scale-free, zero TEST cost, no vol estimator
  to predeclare); the risk that it optimizes short-horizon gross reaction
  rather than cost-bearing expectancy is accepted and carried as a
  disclosure into Track B and the Track C read. No post-G0 rule change is
  permitted.
