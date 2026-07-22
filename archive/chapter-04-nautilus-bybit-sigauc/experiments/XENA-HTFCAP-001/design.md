# XENA-HTFCAP-001 — CF-HTFCAP-001 XENA Universe (Bybit, interaction filters × capture scale)

**Lane:** XENA (default route) · **Family:** CF-HTFCAP-001 (REGISTERED 2026-07-16, ckpt-013)
**Status:** DESIGN — Stage 1 (quant-designer, 2026-07-18); QA + operator execution gate pending
**Binding inputs:** SPDR-004 WORTH_EXPLORING (2026-07-17) + SPDR-006 WORTH_EXPLORING (2026-07-17, §10 caveats)
**Active CAL pin:** `python/experiments/INFR-015/results/bybit_pc_frozen_registry.json`
sha256 `abbb184229236a75f624537ca605668a73f6f85138c150e14a3609c4191bf786` — class **CLS-FILTER**,
**LOW cadence only certified** (α̂ 0.045, cov 0.035; HIGH FAIL — blocked).
**Instrument scope (operator, 2026-07-18):** BTC+SOL binding, ETH disclosure-only —
SPDR-006 §10 caveat 2 supersedes the ckpt-013 §5 online-10 rule for this evidence-scoped
universe (rationale recorded below, §4.1).

---

## 1. Question + mechanism

**Falsifiable question.** Under the pinned cost-aware CLS-FILTER binder (stage-1 net search →
stage-2 gross leg-studentized LCB on an embargoed band), does a portfolio drawn from the
HTF-interaction-filter × hold-scale universe on BTC/SOL 4h/15m certify (stage-2 gross LCB > 0),
where the calibrated false-pass rate is α̂ ≈ 4.5% (LOW cadence)?

```
MECHANISM: Confirmed 4h HTF state — DI-direction continuation gated by high relative
  volatility (vol_ratio = ATR(14)[t−1]/median(ATR14, W=100 HTF bars) ≥ thr), optionally
  ADX-strength-gated — raises the conditional gross bps/trade of otherwise-unconditioned
  15m entries, with capture scaling in hold length (SPDR-004: SOL DI_ADX ladder 5.9→50.1
  bps monotone; SPDR-006: interaction amplifier +26.6/+28.5 bps med lift, 160/164 powered
  CI+ above direction-only). P&L-bearing object: the individual directional LEG
  (market-on-open entry at gate-ON, fixed hold H, market-on-open exit). Event cadence:
  4h-gate-driven, LOW class (holds 4–16h; tens-to-hundreds of legs per candidate on TRAIN).
DERIVED: estimand = per-leg open-to-open gross/net bps via xen.adjudication (shim on
    positions_ledger); portfolio functional = pinned g_gross_ratio / g_net
  null = pinned CLS-FILTER calibration battery (INFR-014, thinned-gate FILT-vs-BASE nulls)
    + in-design gate-schedule derangement destroy
  horizon = hold H ∈ {1×,2×,4×} HTF span = {16,32,64} 15m bars
  test = pinned two_stage_sample_split binder — this design NEVER re-derives thresholds
```

## 2. Object identity declarations

```
OBJECT-IDENTITY:
  measurement object == trading object: YES — both are the market-order leg
    (entry fill at next 15m RealOpen after confirmed gate-ON at t−1; exit fill at
    RealOpen of entry+H bars); adjudicated from positions_ledger via the shim. L-16/L-18.
  measured conditioning event == traded entry event: YES — the gate (DI sign, vol_ratio,
    ADX) is evaluated on CONFIRMED HTF bars ≤ t−1; the strategy commits capital at the
    immediately following 15m bar open; no limit entries anywhere (limit_entry_cells =
    false, matches pin; P-10/L-27 not in play). B-4.
  effect-splitting windows non-overlapping: YES — one open leg per (candidate) at a time;
    a new gate-ON while a leg is open is ignored (no pyramiding); greedy re-entry at the exit
    boundary is contiguous, never overlapping (`next entry ≥ prev entry + H`; engine OMS =
    HEDGING, D3 §4.3, so a coincident close+open does not net); direction and vol effects
    are not separately claimed (interaction-only scope, SPDR-006 caveat 1). B-9.
```

## 3. Estimand

- Canonical: `xen.nautilus.adjudication_shim` → `xen.adjudication` per-leg objects
  (`cis_trades`); open-to-open real prices only; no local accounting
  (`check_no_local_accounting` clean).
- Emission contract v1 per candidate under catalog fence (`fence_attestation.json`,
  non-STUB); **finite synthetic `SlPrice` on every leg** = EntryFill − side × 1.0 ×
  HTF ATR(14)[t−1] (sizing denominator only; no live stop order — clarified contract).
- Estimand gate v2 (`python -m xen.estimand_validation`) must pass on the universe emission
  before ANY analysis/certification read.
- L-29 anchor check in gate: `EntryFillPrice == next-15m-bar RealOpen ± 1 tick`.

## 4. Universe manifest (all cells enter — no per-cell quality gates)

### 4.1 Instruments

| Role | Symbols | Read |
|---|---|---|
| Binding | BTCUSDT-LINEAR.BYBIT, SOLUSDT-LINEAR.BYBIT | per-stratum, verdict-bearing |
| Disclosure | ETHUSDT-LINEAR.BYBIT | disclosure-only (SPDR-006 review: single seed-fragile cell) |

Deviation record: ckpt-013 §5 online top-10 selection is NOT used here. SPDR-006 §10
(operator-signed, later, design-specific) fixes the evidence scope to BTC+SOL exactly;
operator confirmed 2026-07-18. Anti-survivorship is moot on two fixed always-listed majors;
it re-binds on any future rule-selected HTFCAP universe. DIRECTION: NEUTRAL (scope
narrowing to evidence, predates measurement).

### 4.2 Candidate grid

| Axis | Values | n |
|---|---|---|
| Domain | 4h HTF / 15m LTF only (SPDR-006 caveat 3; 1h/5m excluded — P-14 short-grain sub-cost; 1d unpowered at SPDR) | 1 |
| LTF base | UNF (unconditioned; promote clusters were UNF-base) | 1 |
| Filter model | DI×VOL_HI (sign from ±DI, vol gates); DI_ADX×VOL_HI (adds ADX ≥ ADX_min) | 2 |
| vol_thr (vol_ratio ≥) | 1.10, 1.25 (screen value), 1.50 | 3 |
| ADX_min (DI_ADX only) | 20, 25 (screen value), 30 | 3 (DI: n/a) |
| Hold H (× 4h span) | 1× (16 bars), 2× (32), 4× (64) | 3 |
| Polarity | with-HTF only (against-HTF dead per SPDR; standalone VOL banned — caveat 1) | 1 |

Cells: DI×VOL_HI = 3 vol_thr × 3 holds × 3 symbols = 27; DI_ADX×VOL_HI = 3×3×3×3 = 81.
**Total 108 candidates** (72 binding-symbol, 36 ETH disclosure). Every cell enters the
oracle universe. h0.5 holds excluded (sub-floor at SPDR — caveat 3); W=100 and ATR(14)
frozen verbatim from `spdr006_screen.py` (no retune).

### 4.3 Feature definitions (verbatim from SPDR-006, causal ≤ t−1)

- `vol_ratio[t] = ATR(14)[t−1] / causal_rolling_median(ATR(14), W=100 HTF bars)[t−1]`
- DI sign: +DI > −DI ⇒ long, else short (Wilder, confirmed HTF bars only)
- ADX: Wilder ADX(14) on confirmed HTF bars
- Gate-ON at 15m bar t ⇔ all gate legs true on the last CONFIRMED 4h bar as of t−1.
  One leg at a time per candidate; re-entry allowed at first gate-ON after exit.
- **Re-entry object (AMENDMENT-1, operator-approved 2026-07-18).** The engine implements
  **greedy back-to-back** re-entry, matching SPDR-006's `greedy_entries`: at a 15m boundary T
  where a leg exits, the next leg may enter at the SAME open (coincident exit/entry price),
  subject to non-overlap `next entry ≥ prev entry + H`. Engine deviation **D3**: venue OMS =
  **HEDGING** (not NETTING) so a coincident close+open does not net to nothing; each leg stays
  a distinct FIFO-mapped position — no true concurrency. Non-overlap and no-pyramiding hold
  (BTC smoke ledger: 0 overlaps; 38/40 consecutive legs contiguous, 2 gate-gap re-entries;
  B-9 preserved). The certified object is the **greedy 41-leg** object = the SPDR evidence
  generator EXACTLY — SPDR-004/006 effect/power transfer is 1:1 with no leg-set seam.

### 4.4 Cadence certification constraint (binding)

Pin certifies CLS-FILTER **LOW only**. Grid cells hold 4–16h (16–64 LTF bars), gate duty
≈ 10–40% ⇒ expected leg density in the LOW class (analog: hold_bars 20 @ LOW spec).
**Attestation at candidate gate:** report per-candidate realized legs + mean hold; if the
certified top-1 candidate's stream is HIGH-shaped (mean hold < 2h or leg density in the
HIGH calibration class), certification is NOT covered by the pin → no gate spend; park +
operator escalation. This is an integrity (coverage) check, not a quality gate.

## 5. Temporal mapping + pinned binder (cited, never re-derived)

- TRAIN span: 2021-06-29T06:53Z → 2023-12-18T00:00Z (fence manifest, sha-pinned catalog
  `35d3375e…`, 894 ADMITTED). TEST: 2023-12-18 → 2025-01-08 (holdout_start). Holdout sealed.
- Stage bands from pin procedure: `search_frac 0.5, ranking_frac 0.25, embargo_frac 0.2`,
  computed by the frozen INFR-014/015 band code on the TRAIN calendar; resulting UTC
  boundaries are written into the universe manifest BEFORE any search and are immutable.
- Binder (pin, class CLS-FILTER): `two_stage_sample_split`; stage-1 search+certify top-1 on
  **g_net** (charge_costs=true, cost_stack `bybit_round_trip_cost_bps_v1`, funding included
  — family decision: funding BINDS at XENA); stage-2 `lcb_g_leg_studentized(g_gross) > 0`
  on the distant embargoed band; e2e pass event `stage2_gross_lcb_positive`; deployability
  (informational-binding per L-22) `stage2_net_lcb_positive`; n_boot 200, block_legs 1,
  alpha 0.05, one_subset, no shortlist.
- Search: `xen.xena.search.run_restart` ×10–15 (LAHC), TRAIN search band only.
- Certification: `xen.xena.certify.certify_and_rank` with `registry_path` = INFR-015 pin
  (hash-verified). Final gate: `run_final_gate`, TEST band, **counted, cap 2/universe**,
  operator-approved spend only; `new_data_attestation` operator-only.
- Multiplicity: `evaluation_count` + `distinct_subsets` travel with every number;
  XENA run registered in `docs/signal-registry/xena-runs.md` before search.
- S1 smoke result honored: multi_instrument_single_node admissible; runners obey L-30
  (`dispose_on_completion=False`) + L-31 (one node/process).
- **Topology deviation D3 (operator-signed 2026-07-18).** Venue OMS = **HEDGING** (not the
  NETTING validated at INFR-014 S1). Greedy contiguous legs (§4.3) put a leg's exit and the
  next leg's entry at the SAME 15m open; under NETTING that coincident close+open nets to
  nothing, destroying the object — HEDGING keeps each leg a distinct FIFO-mapped position.
  The operator's greedy-object approval (§4.3) entails this OMS. L-31 preserved: still one
  `BacktestNode` per `run_param_group`, one node/process (smoke ran 3-instrument HEDGING
  single-node cleanly). See amendment ledger §15.

## 6. Costs + pre-search floor

- Engine costless; costs analyst/oracle-injected via `xen.evaluation.bybit_round_trip_cost_bps`
  (taker fees + pseudo-quote spread + **funding**; per-symbol spread pin status disclosed).
- **Pre-search gross floor (XENA-003 lesson, disclosure + park rule):** before search,
  per-cell TRAIN median gross bps/trade vs the cell's measured breakeven
  (`bybit_round_trip_cost_bps` + GAP; SPDR-006 measured floors ≈ 13–15 bps taker+GAP on
  BTC/SOL 4h/15m). If the ENTIRE binding-cell mass is sub-breakeven → park before search
  (family kill row "entire mass sub-breakeven pre-search"). Individual sub-floor cells
  still enter (no per-cell gates); the floor table is disclosure.
- **Floor leg-set note (AMENDMENT-1).** The pre-search feature-replay floor is computed on the
  greedy leg set — the SAME object the engine certifies (§4.3), so there is no leg-set seam.
  Floor is disclosure only; on `--all` emission it switches to per-cell emission medians.

## 7. Controls

```
CONTROL RAND-SIGN-BATTERY (per certified finalist cell, analysis stage):
  question answered: is the finalist's g attributable to HTF direction content, or to
    gate-timing/vol-regime exposure alone?
  population: same entry timestamps (gate-ON schedule preserved), sign ~ Rademacher,
    25 seeds; DISJOINT: direction information destroyed while cadence/regime kept — it can
    show timing-only profit the signal series cannot disentangle (B-1 satisfied: the
    control population is the sign-scrambled ensemble, not the signal itself).
  bite/MDE: battery seed-percentile read (L-19); with n≥100 legs and SPDR-scale effect
    (~26 bps med lift) the true-signal cell must sit ≥P95 of the battery; MDE from battery
    spread reported per cell.
  non-vacuity: sign scramble moves the MEAN of g directly (mean-bearing statistic; B-6).
  expected outcome if H true: finalist ≥P95 battery; if H false: within battery IQR.
  disclosure: collapse fraction (battery-median / raw effect) per cell.
  destroy form: sign randomization, NOT a permutation — fixed-point rate ≈ 0.5 per leg by
    construction; bite preserved because the read is a 25-seed percentile, not a single
    twin (L-19); declared per L-28 escape clause.

CONTROL GATE-DERANGEMENT (destroy / tripwire, see §8): primary future-destroying control.
```

## 8. Leak tripwire

```
TRIPWIRE: gate-schedule block derangement (causal misalignment destroy)
  GRID (AMENDMENT-2 correction): operates on the 15m LTF open grid. Aggregate/snap marks
    to 15m; blocks are ≥ 64 LTF bars = ≥ max hold H (64×15m = 16h), NOT minute blocks; the
    deranged exit is offset by hold_bars in 15m steps (real 4–16h hold), NOT minute offsets.
  Construction: partition TRAIN into contiguous 15m blocks ≥ 64 bars (≥ max hold H);
  derange the gate-ON block assignments (zero fixed points, code-asserted) so entries fire
  with identical cadence/count but at HTF-unconditioned times. Re-run adjudication on the
  deranged schedule for every certified finalist.
  SEED BATTERY (AMENDMENT-2, operator 2026-07-18; L-19): the collapse read is a
    seed-battery percentile, NOT a single deranged twin. Draw ≥ 15 independent derangements
    (each zero-fixed-point, code-asserted); report the collapse-fraction distribution and read
    the HARD gate off a battery percentile (below), never off one seed.
  must collapse the edge; expected collapse fraction ≈ 0.8+ on BTC (SPDR-006 Control C
  0.79–0.92); SOL predeclared partial 0.55–0.78 (known incomplete destroy — caveat 4):
  SOL residual is reported and routed to operator scrutiny, not auto-passed.
  vacuity check: deranged entries sample unconditioned base drift — moves the mean of g
  (mean-bearing metric); block length ≥ H prevents within-leg leakage. B-6 clean.
  derangement=YES (zero fixed points; L-28); battery=YES (≥15 seeds; L-19).
  HARD: a finalist whose deranged edge survives (battery-MEDIAN collapse < 0.5 on BTC
  binding cells) is a leak → REJECT, no operator override. Percentile read, not one twin.
```

## 9. Interpretation bands (per stratum = symbol × filter-model; no binaries)

```
BANDS (per stratum, on stage-2 / gate reads; all informative except integrity):
  SUPPORTED:    stage2 gross LCB > 0 (pinned pass event) AND net read: g_net LCB > 0 with
                commission + 1× spread + funding binding (L-22) — SUPPORTED-GROSS reported
                separately as machinery verdict only
  WASH:         |median g| < battery noise scale (report A≈B; not refutation)
  CONTRADICTED: gross UCB < 0 on powered stratum
  UNPOWERED:    n_legs < MDE-consistent floor (F07: n at which MDE ≤ shrunk TRAIN effect,
                shrinkage from fold attenuation) — never read as negative
POOLED: disclosure-only. ETH strata: disclosure-only regardless of band.
Gross gate pass = selection-machinery verdict, never tradability (L-22 retained clause).
```

## 10. Power statement

```
POWER (TRAIN ≈ 2.47y; 4h bars ≈ 5400; gate duty: vol_thr 1.10 ≈ 35–45%, 1.25 ≈ 25–30%,
  1.50 ≈ 10–15%; DI splits direction; hold occupancy caps re-entry):
  expected legs/cell (order-of-magnitude, verified at candidate gate):
    H=16: ~200–500 · H=32: ~120–300 · H=64: ~60–150 (thr 1.10→1.25)
    vol_thr 1.50 × H=64 × ADX 30: ~20–60 → predeclared likely UNPOWERED
  (leg counts are the greedy engine object = SPDR order-of-magnitude directly, §4.3;
   verified against realized legs at candidate gate)
  MDE at n=150 legs, per-leg σ ≈ 120 bps (15m·16–64-bar crypto holds): ≈ 19 bps — below
    SPDR promote-cluster med lift (+26.6/+28.5) → binding cells powered at SPDR effect.
  strata predeclared UNPOWERED: all vol_thr=1.50×ADX_min=30 cells; any cell failing the
    F07 floor at candidate-gate time (reported, excluded from negatives).
```

## 11. Screen-effect conversion pin (L-21)

```
CONVERSION-PIN:
  divisor object: NONE on the promote facet — SPDR-004/006 primary unit is already
    "gross open-to-open bps/trade (no ATR divisor)" (SPDR-006 results/unit_pin.json,
    measured 2026-07-16; ATR is disclosure-only there).
  measured value: BTC 4h/15m TRAIN-median LTF ATR ≈ 26.55 bps (unit_pin.json) — disclosure.
  resulting effect: screen effects carried in native bps: +26.6 / +28.5 bps med lift
    (promote clusters); SPDR-004 SOL ladder 5.9→50.1 bps.
  cost floor: measured taker+GAP ≈ 13–15 bps (SPDR-006 money-floor table; re-pin if
    fee/spread map changes — caveat 4 of SPDR-006 §10). h1+ holds cleared it at screen;
    effects clear the floor → tradability framing permitted at XENA (net leg still binds).
```

## 12. T1 spread-scale routing

```
SPREAD-SCALE-ROUTING (per certified finalist cell, before any verdict-bearing read):
  estimated_rt_spread_bps: from per-symbol pseudo-quote series via
    xen.evaluation.t1_round_trip_spread_bps (BTC/SOL/ETH, cell's TRAIN window)
  gross_edge_bps: cell TRAIN gross median bps/trade
  t1_undecidable: via xen.evaluation.spread_scale_route (3× rule, not re-derived)
  if YES: disposition AWAITING_MBP or T2 confirm (BTC/ETH/SOL post-collection);
    pooled T1 reads disclosure-only; no tradability band on that cell
```

## 13. Golden-trace spec (QA derives; developer must not generate)

```
GOLDEN-TRACE (3 events, hand-derived from catalog + §4.3 definitions):
  G1: BTCUSDT, first DI×VOL_HI(thr=1.25) gate-ON after 2021-08-01T00:00Z — verify from raw
      4h bars: vol_ratio ≥ 1.25 and DI sign on the last confirmed bar; expected entry =
      RealOpen of the next 15m bar, side = DI sign; exit = RealOpen 16 bars later;
      SlPrice = entry − side × 1.0 × HTF ATR(14)[t−1] (finite).
  G2: SOLUSDT, first DI_ADX×VOL_HI(thr=1.25, ADX≥25) gate-ON after 2022-01-01T00:00Z —
      same checks + ADX leg; hold 64 bars (H=4×) variant; verify no second entry while open.
  G3: negative trace — a 15m bar where vol_ratio ≥ thr but DI gate flips on the FORMING 4h
      bar only: expected NO entry (confirmed-bar discipline; L-29 fill-ts anchor checked).
QA diffs all three against the emission before execution sign-off.
```

## 14. Integrity vs informative split

```
HARD (block): tripwire collapse (§8), holdout fence, causal provenance (≤ t−1 gates,
  fence attestation non-STUB), estimand reconciliation (gate v2), pin hash verification
  (abbb1842…), cadence coverage attestation (§4.4), SlPrice finiteness (candidate gate).
INFORMATIVE (operator judges): all effect sizes, LCB/UCB reads, battery percentiles,
  collapse fractions, cost/funding sensitivity, floor tables, ETH disclosure strata,
  net deployability. No auto-verdict thresholds anywhere. Final gate spend and final
  verdict are operator gates.
EXPLORATORY-RUN OVERRIDE (AMENDMENT-4/5, operator 2026-07-18): for THIS run only —
  (a) analysis window = TRAIN+TEST (no reserved OOS); (b) n_legs_floor(16) is INFORMATIVE,
  not a HARD/domain veto — sparse candidates are reported, not excluded; (c) NO pin-backed
  "certification" or deployability claim (α̂ guarantee void without the floor). Everything
  becomes informative evidence for the operator. **STILL HARD, non-overridable:** global
  HOLDOUT sealed (`≥ holdout_start`; fence refuses it), estimand reconciliation (gate v2),
  causal ≤ t−1 provenance, fence attestation non-STUB, §8 derangement leak tripwire.
```

## 15. Complexity budget + amendments

- Stat machinery: pinned binder + 2 controls (battery, derangement) — no new tests.
- New code: universe manifest builder + Nautilus batch runner cells (contract v1) +
  derangement/battery analysis scripts in `analysis_code/`. No new `xen` accounting.
- Visualisations: ≤5 (floor table, ladder, battery percentile, collapse, fold ranking).
- Amendment ledger (L-23):
  - AMENDMENT-0: instrument-scope deviation §4.1 (BTC+SOL binding, ETH disclosure) — DIRECTION: NEUTRAL
  - AMENDMENT-1: certified re-entry object = greedy back-to-back §4.3/§6/§10 (41 legs = SPDR evidence generator exactly; non-overlap `next entry ≥ prev entry + H` + no-pyramid preserved) — operator-signed 2026-07-18 — DIRECTION: NEUTRAL
  - AMENDMENT-2: §8 derangement tripwire → 15m-grid + seed-battery percentile collapse (L-19) — DIRECTION: TIGHTER
  - AMENDMENT-3: engine topology D3 = venue OMS **HEDGING** (not INFR-014 S1 NETTING) §5 — required by greedy coincident exit/entry (NETTING would net the object to nothing); L-31 one-node/process preserved (3-instrument HEDGING single-node smoke clean) — operator-signed 2026-07-18 — DIRECTION: NEUTRAL
  - AMENDMENT-4: **analysis window extended to TRAIN+TEST** — stage bands (search/ranking/gate) recomputed over the covered majors window **2022-07-14 → 2025-01-08 (`holdout_start`)** instead of TRAIN-only, via two sanctioned fenced reads (`band="TRAIN"` + `band="TEST"`). Rationale: majors' local history starts 2022-07-14 (trailing-4y cap); TRAIN-only (~1.4y) leaves LOW-cadence candidates below the n_legs floor (verified re-CAL probe 2026-07-18: 100% out-of-domain at the 1.4y scale, α̂ vacuous). TRAIN+TEST ≈ 2.46y ≈ calibrated scale. **CONSEQUENCE: no reserved out-of-sample band — this run is EXPLORATORY / in-sample, NOT a pin-backed certification and NOT a deployability claim.** Global HOLDOUT (`≥ 2025-01-08`) remains HARD-sealed (fence `band_bounds` refuses HOLDOUT; TEST caps at `holdout_start`). Operator-approved TEST spend, against the train/test-separation policy — operator's explicit call 2026-07-18 (records 1 gate slot in `xena-runs.md`). — DIRECTION: LOOSER
  - AMENDMENT-5: **n_legs_floor (16) demoted HARD-gate → INFORMATIVE for this experiment** — per-candidate trade counts + domain status are reported as evidence, not a blocking exclusion. Rationale: operator authorizes finishing the exploration despite thin per-candidate samples; sample sufficiency is an operator judgment here, not an auto-veto. The pinned α̂ 4.5% guarantee **does not hold** without the floor (un-floored α̂ ≈ 0.135, probe 2026-07-18) — so certification language is void; reads are informative only. Operator-signed 2026-07-18. — DIRECTION: LOOSER
  - running count: 2 L / 1 T / 3 N
  Two operator-authorized LOOSER amendments (A4/A5) land together, 2026-07-18; both are
  explicit against-policy operator calls, recorded not silent. No one-directional streak ≥ 3
  (N,N,T,N,L,L). **These convert HTFCAP from a pin-backed certification into an
  operator-directed EXPLORATORY characterization: no reserved OOS, floor informative, results
  evidence-only — operator decides follow-up.** HOLDOUT remains absolutely sealed.
  AMENDMENT-1/D3 approval is consistent across design (§4.3/§5/§15) and code.
- No scope expansion after QA APPROVE; new questions (e.g. 1h/5m grain, rule-selected
  universe, against-HTF) = new designs.

## 16. Kill / park rows honored (family card §8)

Entire binding mass sub-breakeven pre-search → park. Noise-like under binder / only
cadence-print artifacts → negative outcome row (operator-signed at checkpoint). Cannot emit
causally or pin costs → park, don't book.
