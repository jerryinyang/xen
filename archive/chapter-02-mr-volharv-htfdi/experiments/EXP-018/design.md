# EXP-018 — CF-MR-005 Disposition Probe: Deliberate Ladder Harvest (price-primary, 4h)

**Checkpoint:** `2026-07-04-006-cf-mr-005-disposition`. **Family:** CF-MR-005 (registered;
this is HYP-003 — evidence row appended at documentation, no status transition).
**Class:** price-primary, full engine runs, TRAIN band only. **Pipeline:** INFR-001
(this design → fresh-context QA → operator execution gate → estimand script gate →
data-analyst → operator verdict).

## 1. Question + mechanism

**Falsifiable question.** When the ladder scale-in harvest that survived VAL-006 as a residue
is specified *deliberately* (not as EXP-014b's accidental e0 arm) and emitted under the
correct accounting contract, does it show a dislocation-conditioned, exposure-honest,
regime-robust positive episode economics on TRAIN in the residue clusters (US2000
single-instrument; US500 both-leg) — and NOT in a predeclared negative-control cell?

```
MECHANISM: 4h index dislocations vs the S8 basket-relative anchor (z = deviation/σ of
log P − basket-implied value) overshoot and partially revert over multi-day horizons.
A resting ladder that adds one unit at each deepening threshold (z*∈{z1<z2<z3}) buys the
overshoot in tranches; each leg's reversion to the (moving) anchor mean is the P&L unit;
overlapping legs chain into multi-week EPISODES. The edge, if real, is conditional on the
dislocation (kill test: random-timing ladders with the same cadence earn less) and is paid
for by inventory risk during trend regimes (left tail carried, not hidden).
DERIVED: estimand = episode net (xen.adjudication.build_episodes) + per-leg net;
horizon = episode (bounded by flat); null = random-timing ladder, exposure-matched;
tests = block-bootstrap episode CIs + exposure-honest economics (xen.evaluation).
```

Prior context honestly stated: VAL-006 residue = 5 US2000 e0/e2 cells (leg CI_low>0; two
episode-CI-positive) + US500 both-leg positive in 4/4 variants; 2022-concentrated, 2023
negative; 8/207 cells overall (barely above multiplicity). This experiment exists to test
that residue as a deliberate thesis (controlled thesis-shopping, operator-sanctioned), not to
presume it.

## 2. Object identity declarations

```
OBJECT-IDENTITY:
  measurement object == trading object: YES — the strategy's P&L object is the multi-leg
    EPISODE (overlapping ladder legs to flat); primary estimand is episode net from
    xen.adjudication.build_episodes; per-leg net is secondary/decomposition. (L-16/L-18)
  measured conditioning event == traded entry event: YES — the conditioning event IS the
    resting-limit fill at exp(anchor ± z*σ) (m1-native). All conditioning stats (entry z,
    regime label) are computed at the fill from ≤ t-1 confirmed engine state and emitted
    per leg. No close-breach proxy anywhere. (B-4)
  effect-splitting windows non-overlapping: YES — regime labels (range/trend, vol tercile)
    are assigned at EPISODE START from trailing windows ending ≤ t-1; episode P&L accrues
    strictly after. Year splits by episode END. (B-9)
```

## 3. Estimand + emission contract

- Canonical only: per-leg `RealizedBps` (engine fills), episodes via
  `xen.adjudication.build_episodes`, exposure series via `assemble_multileg_bps`. No local
  accounting (`check_no_local_accounting` gates).
- Emission per cell: `positions.parquet` (incl. `OpenLegs`, provenance columns),
  `cis_trades.parquet` (fills, `RealizedBps`, `Censored`, `LadderLevel`, `LegSymbol`,
  entry-time conditioners incl. `EntryZ`, `EntrySigma`, `EntryTrendZ`, `EntryVolRegime`),
  `run_metadata.json` with `analysis_end_utc` = TRAIN fence.
- **Estimand gate is a hard block**: `python -m xen.estimand_validation` must pass
  (reconciliation/schema/fence/manifest) on the smoke cell before hand-off and on the full
  emission before any analysis or verdict.
- Costs: frozen per-instrument 4h round-trip map (`adaptive_cost_bps_for`), charged once per
  leg (L-02). Cost-sensitivity curve disclosed (§7).

## 4. Scope

| Item | Spec |
|---|---|
| Trigger | S8 basket-relative anchor (identical construction to EXP-014b: w_z=200, w_a=200, median_w=90, basket mates per instrument; frozen, not tuned) |
| Ladder | resting limits at exp(anchor ± zσ), z ∈ {1.5, 2.0, 2.5}; one unit per level; R-refresh per bar; reentry **extend** (primary) / **allow** (one contrast cell) |
| Exit arm A ("harvest") | per-leg TP limit at current anchor mean (moving — deliberate: the reversion target is the mean and the mean moves); episode ends flat; NO stop-loss; time-stop ⌈3·HL⌉ cap 48 bars per leg (bounds e1-style censoring) |
| Exit arm B ("braked") | per-leg TP frozen at entry-time anchor + outward SL at 1·D; time-stop as A |
| Cells (live) | US2000: A/extend/z-ladder, A/allow (contrast), B/extend — each at base ladder; US500: both-leg market (blmkt-style, mate legs at market) arm A; **NZDUSD: arm A (predeclared NEGATIVE CONTROL — VAL-006 confirmed loser; if it turns positive under this spec, the spec is suspect)** |
| Domain / band | 4h; TRAIN only — `AnalysisEndUtc` = the per-instrument 49% TRAIN fence (EXP-016 `TRAIN_FENCE` values); TEST/holdout never emitted |
| Time range | full TRAIN history per instrument (2020-11 → 2024-09 era) |
| Exclusions | final-30% holdout (never); TEST band (never); no other instruments |
| Complexity budget | 7 live cells + controls (§5): ≤ 21 engine runs; stat tests ≤ 4 families; plots ≤ 6; new C# = 1 model variant + conf set; new Python = 0 modules (xen.evaluation only) |

## 5. Controls (each with validity proof)

```
CONTROL random-timing-ladder (PRIMARY DESTROY — engine arm, per live cell):
  question answered: is the P&L conditioned on the dislocation, or is it exposure/regime
    carry any ladder would collect?
  population: same instrument, same TRAIN band, same ladder cadence — entries triggered at
    seeded random bars matched to the live arm's per-level entry-count and inter-add gap
    distribution (engine consumes a pre-generated seeded schedule). DISJOINT: entry bars are
    (almost surely) non-dislocation bars; the live arm fires only at z-threshold touches. (B-1)
  bite/MDE: detectable Δ = live episode-net mean − control episode-net mean; with n≈85-130
    episodes/cell and VAL-006 episode σ, the paired-cell MDE ≈ episode CI half-width √2
    (§8 table) — the residue effect sizes (US2000 z15 mean ≈ +575 bps/episode) exceed it.
  non-vacuity: different entry bars ⇒ different fills ⇒ different P&L mean — the destroy
    moves the mean statistic itself. NOT a permutation of realized outcomes. (B-6/EXP-012)
  expected if H true: control mean ≪ live mean (collapse fraction < ~0.4).
  expected if H false: control ≈ live (fraction ≈ 1) — the "edge" is carry.
  disclosure: collapse fraction per cell, continuous. (L-15)

CONTROL entry-delay +1 bar (CAUSAL-MISALIGNMENT TRIPWIRE — engine arm, per live cell):
  question answered: does the P&L depend on information genuinely available at t-1?
  population: identical spec, all arming decisions delayed one bar (t-2 conditioning).
  non-vacuity: shifts every fill; moves the mean.
  expected if causal edge: graceful degradation (fraction ~0.5-1.0 — reversion horizon is
    multi-day, one 4h bar should not kill it).
  expected if timing leak: discontinuous collapse or sign flip at +1 bar. Anomalous
    IMPROVEMENT also flags mis-specification. This is the future-destroy analog for an
    engine-side strategy (causality is structural in OnBar ≤ t-1; the residual leak channel
    is timing, and this arm stresses exactly that). (EXP-012 lesson: break alignment
    causally, don't permute outcomes.)

CONTROL basket phase-shift 60h (ATTRIBUTION DISCLOSURE ONLY — extend cells):
  question answered: how much of the edge needs the cross-instrument construction?
  Semantics on mixed own-price/construction P&L are uninterpretable as a binary (B-3);
  reported as collapse fraction, explicitly non-binding.

NEGATIVE-CONTROL CELL NZDUSD (design-level control): a confirmed per-leg loser under the
  same mechanism class. Expected: stays ≤ 0. A positive flip is evidence of spec-induced
  artifact and caps confidence in the US2000/US500 reads.
```

Integrity hard gates: estimand reconciliation (§3), holdout/fence, provenance trace (QA +
analyst), entry-delay tripwire anomaly (discontinuous behaviour ⇒ REJECT-class investigation).
Everything else informative.

## 6. Test selection (candidate-aware, composed from xen.evaluation)

Mechanism = episodic multi-leg mean-reversion harvest ⇒
- **Primary:** per-cell episode-net mean + moving-block bootstrap CI (block 5 over
  time-ordered episodes; the episode is the iid-violating unit, so blocks over episodes).
- **Paired destroy read:** live − random-timing episode-net mean, block bootstrap on the
  difference of cell aggregates (episodes not pairable one-to-one; bootstrap each series,
  difference of draws), + collapse fraction.
- **Exposure-honest economics:** `xen.evaluation.exposure_metrics` — occupancy, avg + peak
  deployed exposure, ann. return on unit/avg/peak, maxDD, B&H and exposure-time-matched B&H.
  No raw-B&H kill reads (operator rule 2026-07-04).
- **Regime robustness:** episode-net split by predeclared episode-start regime — trend
  |EMA20−EMA50|/σ tercile and vol tercile (trailing 500 bars, ≤ t-1) — via
  `xen.evaluation.split_by`; year split by episode end. Left-tail census: worst-episode MAE,
  net without top-3 winners (tail dependence).
- **Cost curve:** `cost_sensitivity` over {0.5×, 1×, 2×, 3×} frozen cost.
Shape note: episode nets are right-skew heavy (few big harvests) — medians disclosed beside
means; a mean-only read is not treated as the whole story (L-11).

## 7. Interpretation bands (per cell — informative; operator judges)

```
BANDS (per live cell, episode-net mean at frozen cost):
  SUPPORTED:    CI_low > 0 AND random-timing collapse fraction < 0.5 AND
                ann_return_on_avg_exposure ≥ bh_exposure_time_matched_return AND
                2023-only episode mean not CONTRADICTED (CI_high < 0 in 2023 disqualifies
                "regime-robust", downgrade to REGIME-BOUND)
  REGIME-BOUND: CI_low > 0 but 2023/trend-tercile contradicts — a real but regime-gated
                harvest; disposition = operator (deployability implications differ)
  WASH:         CI straddles 0 with |mean| < MDE — reported as A≈B, not refutation
  CONTRADICTED: CI_high < 0
  UNPOWERED:    n_episodes < 30 or MDE > 2× the VAL-006 residue effect for that cell —
                excluded from negatives
POOLED (across cells): disclosure only. NEGATIVE CONTROL (NZDUSD): expected ≤ 0; a
SUPPORTED-band read there flags the whole experiment for QA re-review, not a discovery.
```

## 8. Power statement

| Cell | Expected episodes (VAL-006 basis) | Est. MDE (episode-net bps) | Status |
|---|---|---|---|
| US2000 A/extend (≈e0/z-ladder) | ~110-130 | ~500-550 (CI half-width, census) | POWERED for the residue effect (~575) — marginal; medians co-read |
| US2000 A/allow | ~90-130 | ~600 | MARGINAL |
| US2000 B/extend | ~45-85 | ~900 | MARGINAL-to-UNPOWERED — predeclared: a negative here is weak evidence |
| US500 both-leg A | ~40-60 | ~150-200 (smaller episodes) | MARGINAL |
| NZDUSD A (neg-control) | ~100+ | n/a (expected negative) | control |

Predeclared UNPOWERED risk: US500 and B/extend cells. If realized n < 30 episodes, the cell
reports UNPOWERED, never negative. The experiment's decisive read is US2000 A/extend + the
random-timing destroy; everything else is characterisation.

## 9. Golden-trace spec (QA diff material — derived from THIS design, not from code)

Using the already-validated EXP-014b US2000 z15 emission's provenance columns (same anchor
construction, frozen):
1. Bar `2021-01-04 18:00` (US2000): with emitted `Anchor`/`Sigma` at t-1, resting buy levels
   must equal `exp(anchor − zσ)` for z=1.5/2.0/2.5 (hand-compute all three from the emitted
   columns); a fill occurs iff m1 low ≤ level within the bar; `EntryZ` recorded ≈ z of the
   touched level.
2. First leg of that episode, arm A: TP limit re-rests each bar at `exp(anchor_t-1)` (must
   move with the anchor); arm B: TP fixed at `exp(anchor_entry)` for the leg's life and an
   SL rests at `exp(entry_ref − 1·D)` (D = distance to anchor at entry). Same entry, two
   different exit paths — hand-derivable divergence bar.
3. Any leg reaching 48 bars or ⌈3·HL⌉ (emitted `Hl`) must exit at next bar open
   (`ExitReason=time_stop`) — pick one long leg and verify the bar arithmetic.
DEVELOPER MUST NOT generate these expected values; QA computes them from this section + the
emitted provenance columns.

## 10. Hard/informative split + governance

```
HARD (block): estimand reconciliation per cell; fence/holdout; provenance (QA trace +
  analyst Phase 0); entry-delay discontinuity anomaly; check_no_local_accounting.
INFORMATIVE (operator judges): all bands in §7, collapse fractions, exposure economics,
  regime/year splits, cost curve. No auto-verdicts anywhere.
GOVERNANCE: 0 counted TEST reads (TRAIN only); no candidate slot beyond the registered
  CF-MR-005 branch; registry gets an evidence row (HYP-003) at documentation, no status
  change; family disposition = checkpoint-006 retrospective, operator-signed.
```

## Amendment A1 (2026-07-04, operator-elicited pre-implementation — developer stage)

Four under-determined points raised by the developer BEFORE coding (silent-deviation rule);
operator resolutions, all binding:

1. **Random-timing destroy exits = matched-hold market exits.** Each control leg holds a
   seeded draw from the live arm's realized per-level `BarsHeld` distribution, then closes at
   market. NOT arm A's TP-at-anchor (near-anchor random entries would close instantly →
   trivial collapse → biased null, L-08). Implementation: live EPISODES are rigid templates
   (relative add offsets, levels, dirs, realized holds) placed at seeded random non-warmup
   TRAIN bars (`gen_exp018_schedules.py`, seed 20260704); engine consumes the CSV
   (`CisSchedulePath`), market-enters at next open, no TP/SL/form-1.
2. **US500 both-leg arm A = joint form-1 + group time-stop.** The spread-object analog of
   "TP at the moving mean" is the joint spread-reverts-through-mean exit (market, next open),
   plus a group ⌈3·HL_entry⌉ cap-48 time-stop. No per-leg price TPs.
3. **US500 both-leg keeps reentry=none** — faithful to the residue object (VAL-006 both-leg
   cluster was produced under none). No group ladder.
4. **NZDUSD negative control = arm A, reentry=extend, z-ladder** — mirrors the decisive
   US2000 primary. Cell count: **5 live cells** is authoritative (§4's "7" was a typo);
   run census = 5 live + 5 random-timing + 5 entry-delay + 3 phase-shift (extend cells) = 18
   engine runs ≤ 21 budget.

Developer notes (recorded, not deviations): entry-delay arm delays the full DECISION state
(bracket + logClose) for arming, exits, TP refresh, and leg provenance; conditioner columns
(trend/vol) are not decision inputs and stay at t-1. Phase-shift twin passes
`BasketPhaseShiftHours=60` (the EXP-014b/c "60h" convention, unchanged). Both-leg base band
uses z*=1.5 (the ladder base). Single-leg `cis_trades.LegSymbol` stays `""` (existing
convention: empty = traded instrument).

**Status: DESIGN COMPLETE + A1 — implementation done; awaiting fresh-context QA
(`qa-compliance`), then operator execution gate.**
