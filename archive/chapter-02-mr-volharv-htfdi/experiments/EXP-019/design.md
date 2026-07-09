# EXP-019 — CF-VOLHARV-001/HYP-001: seed/fill falsification of the random-timing harvest anomaly + swap-inclusive cost floor (price-primary, 4h)

**Stage:** 1 (quant-designer). **Status:** DESIGN — awaiting QA pre-exec (fresh context) →
operator execution gate. **Family:** CF-VOLHARV-001 (registered 2026-07-04, operator-directed;
`docs/signal-registry/candidate-families/cf-volharv-001.md`). **Checkpoint:**
`2026-07-04-007-cf-volharv-001-falsification-first-screen`. **Slots:** 0. **Counted reads:** 0
(TRAIN only). **Holdout:** sealed, untouched.

Operator-locked parameters (elicitation 2026-07-04): full 16-instrument universe (all minus
DE30); 25 seeds/instrument; hold grid {6,12,24,48} round-robin within one run; swap charged in
the analysis layer from a declared table.

---

## 1. Question + mechanism statement

**One falsifiable question.** Is the EXP-018 random-timing per-leg positive (NZDUSD rt
+31.5 bps/leg, CI_low +13.7, both directions positive) reproducible across independent seeded
schedules under a fully ex-ante causal construction — or is it a sampling/clustering artifact,
exactly as the symmetry null predicts?

```
MECHANISM: NONE CLAIMED — this is a falsification experiment with an ANALYTIC null.
  A fixed-unit, random-direction, random-timing, fixed-hold market-order leg has
  E[gross P&L] = 0 by construction: the seeded coin flip on direction annihilates drift,
  and with no conditioning, no price-dependent exit, and no rebalancing there is no channel
  from path structure (oscillation, vol clustering, reversion) into the per-leg MEAN.
  "Both directions positive in expectation" is impossible for this object. Any systematic
  nonzero across-seed mean is therefore an ARTIFACT (fill/spread asymmetry, schedule
  data-dependence, accounting) or an extraordinary process asymmetry requiring escalation.
  Horizon: 6–48 4h bars. Cadence: ~1 entry per 8 bars. P&L object: the individual timed leg,
  aggregated per (instrument × hold) stratum, inference at seed level.
DERIVED: estimand = per-leg net bps (xen.adjudication) per stratum, seed-level battery
         null     = ANALYTIC E[gross]=0 (strongest possible; empirically exercised by 25
                    disjoint seeds — no synthetic path null needed and none could be sharper)
         horizon  = the exogenous hold grid itself {6,12,24,48}
         test     = across-seed distribution of per-seed stratum means (sign, dispersion,
                    percentile of the EXP-018 observation) + within-seed time-block bootstrap
```

**Why run it at all (three deliverables regardless of outcome):**
1. **Kill or escalate the anomaly** — the only positive residue of the MR arc dies or becomes
   a fill-audit finding.
2. **Swap-inclusive carrying-cost floor** per instrument × hold — the binding input to any
   future HYP-002 harvest-structure design; never measured in this programme (L-04 gap).
3. **Substrate disclosure** — VR/oscillation profile at 6/12/24/48 bars per instrument from
   the same emitted bars (descriptive, licenses/kills HYP-002 cheaply).

## 2. Object identity declarations

```
OBJECT-IDENTITY:
  measurement object == trading object: YES — both are the individual scheduled leg
    (market entry at scheduled bar open, market exit at open of entry-bar + H). No ladder,
    no episode structure, fixed 1-unit size. Stratum aggregation is disclosure over
    identical objects, not a different object.                                   # B-8/L-16
  measured conditioning event == traded entry event: YES — there IS no conditioning event;
    entry commits at the open of the pre-scheduled bar unconditionally (inventory-cap skip
    is the only override, deterministic, declared §4).                           # B-4
  effect-splitting windows non-overlapping: N/A — no effect decomposition; hold strata are
    properties of disjoint leg populations (round-robin assignment), not windows.  # B-9
```

## 3. Estimand

- **Primary:** per-leg net bps = `xen.adjudication` per-leg realized P&L (open-to-open,
  engine m1 fills, spread paid by market orders) − analysis-layer swap charge (§6).
- Aggregations: per (instrument × hold) stratum: per-seed mean → across-seed distribution;
  direction-split (long/short) always disclosed alongside.
- Emission = standard StrategyHost per-leg + per-bar contract; `xen.estimand_validation`
  runnable unchanged (blocking gate before ANY read).
- No accounting primitives in this experiment dir (`check_no_local_accounting`).

## 4. Scope

| Item | Value |
|---|---|
| Instruments | 16 = full VAL-003 universe minus DE30 (truncated history) |
| Domain | 4h (anomaly's domain; single hypothesis — no 1h arm) |
| Band | TRAIN only = first 49% of rows per instrument (70%·70%); `AnalysisEndUtc` fence per instrument computed from the 1m base data by the developer, recorded in the conf |
| Runs | 16 instruments × 25 seeds = 400 engine backtests (m1 data, Mode=NativeOrders) |
| Schedule | pre-generated per (instrument, seed): entry bars ~1 per 8 4h-bars (seeded jitter, uniform over TRAIN, warmup excluded); direction = seeded coin flip; hold = round-robin {6,12,24,48} in schedule order |
| Sizing | fixed 1 unit per leg, never varied |
| Inventory cap | 6 concurrent legs; a scheduled entry landing at cap is SKIPPED (logged `cap_skip`), never deferred — deterministic |
| Exits | market at open of bar entry+H, nothing else: NO TP, NO SL, no refresh, no ladder adds |
| Model | new lean `RandomHoldModel` (C#) reusing EXP-018's schedule-consumption machinery (`CisSchedulePath` pattern: LoadSchedule / FireScheduledEntries / matched-hold market exits) — strip all CIS trigger/basket/z code paths |
| Generator | `tools/ctrader-cli/experiments/gen_exp019_schedules.py`; base seed 20260705, seed_i = base + i, i ∈ 1..25; consumes ONLY the bar calendar (timestamps), never prices — data-independence provable by construction |
| Exclusions | final-30% global holdout (never loaded); TEST band (rows 49–70%) never emitted; EXP-016 TEST rows excluded outright |
| Complexity budget | 2 stat reads (seed battery + direction split), 4 plots, 1 new C# model + 1 generator + 1 swap-table module addition to `xen.evaluation` |

**Causal-construction guarantees (the operator's binding constraint):** every schedule input
is fixed before the run from (seed, bar calendar) only — no live-arm templates, no realized
hold distributions, no price-derived placement. Deployable-live equivalence: the same CSV
could be handed to a live robot on day 1.

## 5. Controls

```
CONTROL seed-battery (primary):
  question answered: is the EXP-018 rt positive a property of the construction or of one draw?
  population: 25 disjoint seeded schedules per instrument; DISJOINT from the EXP-018 rt
    schedule (different generator, different seeds, no template reuse) — and from each other
    (entry-bar overlap between seeds is incidental, direction/hold assignments independent). # B-1
  bite/MDE: per instrument ~590 legs/seed (§8); per-seed stratum SE ≈ σ_leg/√(n_eff);
    across 25 seeds the SE of the battery mean ≈ per-seed SE/5 → MDE ≈ 4–8 bps/leg per
    stratum (instrument-dependent), 4–8× smaller than the +31.5 target effect. A planted
    +15 bps/leg synthetic offset (analysis-side, predeclared) must be flagged by the battery
    in ≥ 24/25 seeds — run before the real read.                                            # B-5
  non-vacuity: the battery directly resamples the statistic under test (the per-leg mean);
    the sufficient statistic moves with every independent draw.                             # B-6
  expected outcome if H_artifact true: across-seed means center on 0 gross (− costs net);
    the EXP-018 +31.5 sits in the tail of the seed distribution.
  expected outcome if H_asymmetry true: across-seed means systematically ≠ 0, same sign,
    direction-split coherent → escalate to fill audit (§9 band PROCESS_ASYMMETRY).
  disclosure: percentile of EXP-018's +31.5 within the NZDUSD seed distribution; collapse
    fraction (battery mean / +31.5) reported per stratum.                                   # B-2
CONTROL direction-split (drift attribution):
  question answered: is any nonzero stratum mean just window drift leaking through finite-n
    direction imbalance?
  population: long legs vs short legs within each stratum (seeded coin → ~50/50); DISJOINT
    subpopulations of the same run.                                                         # B-1
  bite/MDE: analytic drift benchmark E[leg|dir] = dir·μ̂_window·H is computed exactly from
    the emitted bars; deviation MDE same order as battery MDE.
  non-vacuity: drift enters the two splits with opposite sign — a drift artifact separates
    them symmetrically; a genuine asymmetry moves both the same way.                        # B-6
  expected if drift artifact: long−short gap ≈ 2·μ̂·H, battery mean ≈ direction-imbalance ×
    drift; expected if H_asymmetry: both splits displaced same direction (the impossible
    signature — triggers fill audit).
  disclosure: long/short split per stratum, always, plus μ̂_window per instrument.           # B-2
```

## 6. Swap/financing model (INFR prerequisite — build before analysis)

- New declared table in `xen.evaluation`: per instrument, per side, bps per held night;
  triple-swap day (Wed FX / broker calendar) honored; BTCUSD zero-swap noted; indices use
  broker financing rate. **Source:** current cTrader/IC Markets published swap points,
  snapshot-dated and version-pinned in the module docstring.
- **Declared limitation:** historical swap series unavailable; the table is a 2021-24
  anachronism. Mitigation: binding read at 1× AND a 2× stress column, both always shown.
- Charge: per leg, nights-held × per-night bps, added to cost in the NET estimand. Engine
  emission stays gross-of-swap (deterministic, auditable).

## 7. Leak tripwire + integrity gates (HARD)

```
TRIPWIRE (adapted — no conditioning exists to future-destroy; declared per QA requirement):
  1. Schedule data-independence proof: regenerate every CSV from (seed, bar calendar) in QA;
     byte-diff against the consumed CSV. Any diff = REJECT.       # provenance, not statistics
  2. Fill-causality audit: every fill timestamp == scheduled bar open (±broker tick);
     exit fill == open of bar entry+H. Any early/late systematic pattern = REJECT.
  3. Entry-delay +1 twin (1 instrument, NZDUSD, all 25 seeds re-run with all schedule bars
     shifted +1 bar): for a genuinely unconditioned strategy this is just another draw —
     battery mean must be statistically indistinguishable. A systematic shift = the schedule
     was data-dependent after all = REJECT.
  vacuity check: tripwires 1–2 are provenance gates (binary, not statistical); tripwire 3
     moves the entry-bar set wholesale, the only free input the strategy has.
HARD gates: tripwires above; holdout untouched; estimand_validation.json blocking_pass
  before any read; TEST band never emitted.
INFORMATIVE (operator judges): every effect size, seed-battery read, swap sensitivity,
  direction split, VR disclosure. No auto-verdict thresholds anywhere.
```

## 8. Power statement

```
POWER (per instrument): TRAIN ≈ 4,700–5,100 4h bars (FX; indices/crypto vary) → ~590
  scheduled entries/seed (1 per 8 bars, minus warmup and cap_skips ≈ 5–10%) →
  ~145 legs per hold stratum per seed; 25 seeds → ~3,600 legs per stratum per instrument.
  Per-leg σ (4h, hold H): ≈ σ_bar·√H ≈ 60–200 bps (FX low, BTCUSD high).
  Within-seed stratum SE (block bootstrap, overlap-adjusted): ≈ 8–25 bps.
  Across-seed battery SE: ≈ 2–6 bps/leg per stratum → MDE 4–12 bps/leg ≪ 31.5 target.
strata predeclared UNPOWERED: none expected at H∈{6,12,24}; H=48 on BTCUSD/XAUUSD may
  breach block-overlap limits — if effective n < 40 seed-stratum cells the stratum is
  labelled UNPOWERED and excluded from negatives (B-5). Cap_skip rate > 25% in any cell →
  that cell disclosed and its cadence noted as compressed.
```

## 9. Interpretation bands (per instrument × hold stratum — no binaries)

```
BANDS (per stratum, battery = across-seed read):
  ARTIFACT_CONFIRMED (expected): |battery mean gross| < battery MDE AND EXP-018's +31.5
    falls inside the seed distribution's central 95% or above its ceiling → anomaly is a
    draw, not a property. Reported as A≈0, not as "family refuted" (family decision is the
    checkpoint's).
  PROCESS_ASYMMETRY: battery mean gross ≥ MDE with ≥ 20/25 seeds same sign AND direction
    split displaced same direction AND tripwires clean → do NOT book as edge; escalate to
    a fill-forensics follow-up (new EXP) before any claim.
  COST_FLOOR (always booked, orthogonal): swap-inclusive net carrying cost per stratum at
    1× and 2×, the HYP-002 design input.
  WASH: anything between — report absolute sizes with CIs (L-11).
  UNPOWERED: per §8 — never read as negative.
POOLED: cross-instrument or cross-hold pools are disclosure-only unless homogeneity shown.
```

## 10. Golden-trace spec (QA computes, developer never generates)

```
GOLDEN-TRACE: 3 legs from the NZDUSD seed-1 schedule CSV (QA regenerates the CSV
independently from seed 20260706 + bar calendar first):
  T1: first scheduled entry — expected: market fill at that bar's RealOpen, direction as
      CSV dir column, size 1 unit.
  T2: a hold-6 leg mid-schedule — expected exit: market fill at RealOpen of entry_bar+6;
      P&L = dir·(exit_open − entry_open)·1e4/entry_open bps minus spread actually crossed.
  T3: a leg scheduled while 6 legs are open (construct by picking the densest cluster in
      the CSV) — expected: NO position opened, `cap_skip` logged with the scheduled bar time.
QA diffs all three against the emission before execution sign-off.
```

## 11. Execution plan + artifacts

1. INFR: swap table lands in `xen.evaluation` (version-pinned) — **before** analysis, not
   before execution (engine emits gross).
2. Developer: `RandomHoldModel` + `gen_exp019_schedules.py` + 16 conf files
   (`EXP-019-4h-<SYMBOL>.conf`, 25 seeds via schedule path array) + NZDUSD delay-twin confs.
3. QA (fresh context): declaration-block completeness, schedule regeneration byte-diff,
   golden trace, exit-set diff (exactly one exit: fixed-H market — L-14).
4. Operator execution gate → 400 + 25 runs.
5. Estimand gate: `python -m xen.estimand_validation` per family root — blocking.
6. data-analyst: seed battery, direction split, swap floor, VR profile disclosure,
   evidence FOR+AGAINST both bands → analysis.md.
7. Operator verdict → documenter (report.md, registry evidence row, INDEX).

## 12. Amendment 2026-07-04 (implementation-stage, operator-resolved before coding)

| # | Change | Resolution |
|---|---|---|
| A1 | §4 fence | TRAIN fence = EXP-013/018 per-instrument 49% cutoffs (2023-vintage base files, idx-1 CloseTime convention) — band identity with the EXP-018 anomaly. 5 instruments absent from EXP-013 computed under the same rule (XAUUSD 2024-08-26T09:56Z, BTCUSD 2024-10-31T14:05Z, EURJPY 2024-09-06T15:12Z, GBPJPY 2024-09-06T15:28Z, AUDJPY 2024-09-06T14:39Z). Note: engine backtests start 2021 — the emitted band is [2021, fence], matching §8's ~4,700–5,100-bar power figure. |
| A2 | §4 schedule tail | Generator DROPS entries whose hold cannot complete before the fence (entry_idx + hold > N−2) → zero censored legs, balanced strata. A non-empty censored flush on a clean run is itself a finding. |
| A3 | §4 warmup | Warmup = first 50 calendar 4h bars (data-stability margin only; no indicators exist). Inter-entry gap = seeded uniform integer in [4,12] (mean 8). |
| A4 | §4 calendar source | The engine 4h grid is broker-server-aligned (UTC+2/+3, DST-switching): a UTC clock calendar misaligns every row. The generator consumes the engine's own emitted per-bar timestamps (timestamps ONLY, never prices) from 16 calendar-emission pre-runs (`RandomHold` with empty schedule → no orders). Run count: 16 cal + 400 live + 25 twin = 441. |
| A5 | §6 costs | Operator directive: swap table SUPERSEDED. Cost basis = FTMO published commissions (+ live-page spread, pinned at analysis time), snapshot 2026-07-04 in `xen.evaluation` (`FTMO_COSTS`, `round_trip_cost_bps`; raw JSON in `code/ftmo_symbols_snapshot_20260704.json`). Deliverable 2 becomes the commission+spread cost floor at 1×/2×; VR/substrate disclosure unchanged. |
| A6 | §11 conf packaging | One multi-symbol conf per arm (`EXP-019.conf`, `EXP-019-delay1.conf`, `EXP-019-cal.conf`; seed via `EXP019_SEED`, driver `run-exp019-all.sh`) instead of 16 per-symbol confs — same cells, single family root per arm so one `estimand_validation` gate call covers each arm. |

**Predeclared honest prior:** ARTIFACT_CONFIRMED in all strata (the analytic null is strong).
The experiment's value is symmetric: it either retires the anomaly for ~zero cost (freeing
the family to test real harvest structures under HYP-002 on measured cost floors), or it
surfaces a fill/process asymmetry that would invalidate more than this family.
