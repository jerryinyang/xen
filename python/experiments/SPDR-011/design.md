# SPDR-011 — Volatility-to-Direction Characterisation

- **Family:** `CF-VOLCONV-001`
- **Checkpoint:** `2026-07-22-016-volatility-direction-conversion`
- **Status:** `DESIGN COMPLETE — IMPLEMENTATION COMPLETE / PRE-EXECUTION QA PENDING`
- **Vehicle:** one TRAIN-only SPDR emission; five ordered report layers
- **Execution authority:** none; operator approval required after fresh-context QA
- **TEST / holdout:** prohibited; zero reads

## 1. One question and mechanism

> Does a causally known HIGH daily-volatility state leave enough signed movement after a
> completed four-hour break of the prior UTC-day range to support one fixed four-hour episode
> under partial fee/funding/allowance accounting?

```text
MECHANISM:
  Daily volatility clusters into the next session and predicts movement magnitude, not sign.
  A completed four-hour close beyond the prior confirmed UTC-day range supplies sign. Capital
  is committed at that boundary for one non-overlapping four-hour episode. The mechanism exists
  only if HIGH-state signed residue exceeds identical MID/LOW breakout residue and survives the
  available fee, discrete-funding and execution-allowance accounting. Spread is unavailable.
DERIVED: estimand=one fixed four-hour episode
         null=matched non-breakout timing plus identical MID/LOW breakout episodes
         horizon=4 wall-clock hours
         test=date-blocked partial-cost residue and HIGH-minus-MID/LOW increments
```

This is a conversion test. The breakout earns no independent information claim; its identical
unconditional population owns the generic breakout/drift explanation.

## 2. Object identity

```text
OBJECT-IDENTITY:
  measurement object == trading object: YES — one next-boundary-open to open exactly 4h later episode
  measured conditioning event == traded entry event: YES — completed 4h range break, action at boundary
  effect-splitting windows non-overlapping: YES — [entry, entry+4h); later triggers inside it are ignored
```

The trigger bar's move is never credited. No pyramid, refresh, reversal, stop or target exists.

## 3. Pre-outcome census and feasibility

### 3.1 Frozen artifacts

| Artifact | SHA-256 | Contents |
|---|---|---|
| `results/census.json` | `5474955afc85b9e76b409d960dff2af74a8e47538c6dfcab624cba0bbed2b9db` | counts, coverage, assumed-sigma MDE curves, data status |
| `results/census_event_keys.parquet` | `d1299a08c98461468447289622ac979a6450fc04171c1547ccf950af850c7dfd` | causal timestamps/state/ranks only; no prices or outcomes |
| `design_derivations/census.py` | `9fae1731a3afe39a64abb7cbda58b870932b9ea52ae6c83a38ccb470ee802bdc` | fenced locator and isolation assertions |
| `results/signed_train_attestation.json` | `bdfe839c4f6ae61b75a3ec2bca270cd9ba23a1bdff90bcbb8351970d9b180d29` | five-symbol TRAIN ingest, mapping and fence proof |

The census queried `TRAIN` through `fenced_bar_query`; maximum query end equals the pinned
`2023-12-18T00:00Z` TRAIN fence. It emitted no execution price, future path, return, excursion,
cost or P&L field and applied no post-event path-completeness filter. The catalog reader does
materialise TRAIN OHLCV; isolation is therefore proven by the code/data contract and emitted
schema, not by physically withholding later bars from the census process.

### 3.2 Coverage and counts

Native core data start: SOL `2022-07-14`; the other four `2022-07-15`. The registered DESIGN
window remains unchanged, but its effective five-name eligible interval begins
`2022-09-14T00:00Z` after the 60-return warm-up.

| Band | Located events | HIGH | MID | LOW | Unique dates | TOP2 |
|---|---:|---:|---:|---:|---:|---:|
| DESIGN | 1,390 | 394 | 390 | 606 | 148 | 551 |
| CONFIRM | 2,216 | 490 | 704 | 1,022 | 255 | 894 |

DESIGN HIGH event/date counts: BTC 54/19, ETH 54/14, SOL 115/42, DOGE 71/20, XRP
100/33. Same-boundary clustering is material: 351 DESIGN timestamps contain multiple symbols;
maximum cluster size is five. Episode rows are not independent observations.

### 3.3 Prospective power — count-only

Independent unit is conservatively one UTC date. Values below are 5% two-sided / 80%-power
normal approximations using assumed date-level sigma; no outcome variance was inspected.

| DESIGN object | MDE at σ=50 bps | σ=100 bps | σ=200 bps |
|---|---:|---:|---:|
| HIGH pooled disclosure, one-sample | 16.3 | 32.5 | 65.1 |
| HIGH vs MID/LOW pooled disclosure | 20.6 | 41.3 | 82.5 |
| Per-symbol HIGH, best→worst | 21.6→37.4 | 43.2→74.8 | 86.4→149.7 |

CONFIRM pooled HIGH one-sample MDE at σ=100 bps is 27.6 bps; HIGH-vs-MID/LOW is 33.1
bps. Per-symbol small effects are expected to be UNPOWERED. The run can resolve only large
per-symbol effects; pooled figures remain disclosure-only unless homogeneity is demonstrated.

### 3.4 Signed data readiness — cleared

The raw signed source is currently readable and the full TRAIN signed catalog is verified at
`data/catalog_sigbar/train`: 3,731,908 rows across five symbols and 90 parquet files, catalog-tree
SHA-256 `d4b7bbed7e0c039cc8c74a05e0f8747796c75016957d1e7c5f7c2feb20f7d2b9`.
The attestation records source hashes, first/last timestamps, zero
`BuyVolume + SellVolume == Volume` violations, zero `delta == Buy-Sell` violations, accepted
INFR-017 config hash, TRAIN fence, and zero TEST/holdout rows. `data/catalog/` remains unchanged
and OHLCV-only. This is an engine-readable restoration of already collected primary data, not a
secondary-data branch. Data readiness does not authorise outcome execution.

## 4. Fixed scope

| Item | Frozen decision |
|---|---|
| Core | BTCUSDT, ETHUSDT, SOLUSDT, DOGEUSDT, XRPUSDT |
| DESIGN | `[2021-06-29T06:53Z, 2023-03-01T00:00Z)`; effective eligibility starts 2022-09-14 |
| CONFIRM | `[2023-03-01T00:00Z, 2023-12-18T00:00Z)`; one frozen-rule read |
| TEST | `[2023-12-18T00:00Z, 2025-01-08T00:00Z)` — never queried |
| Holdout | `>=2025-01-08T00:00Z` — never queried |
| Detection | completed 4h close strictly beyond prior confirmed UTC-day high/low |
| Entry / exit | boundary's first 1m `RealOpen`; `RealOpen` exactly 4h later |
| Overlap | one open episode per symbol; `[entry, exit)` blocks later triggers |
| Base | HIGH state, all core symbols |
| Modifier 1 | fixed TOP2; TOP1/TOP3 distribution-only |
| Modifier 2 | fixed upper-tercile aligned flow |
| Costs | taker fees + discrete funding + 0/2/5-bps allowance; spread null/unavailable |
| Complexity | one emission, five layers, four controls, three golden traces, no search grid |

No broad-catalog result can select a rule or enter the strategy package.

## 5. Causal feature contract

### 5.1 Daily state

For confirmed UTC day `d`:

```text
r[d]       = log(daily_close[d] / daily_close[d-1])
rv20[d]    = sqrt(mean(r[d-19:d]^2))
vol_pct[d] = (count(prior_rv20 < rv20[d]) + 0.5*count(equal)) / n_prior
```

- prior history: at most 252 `rv20` values, current excluded;
- minimum 60 confirmed daily returns;
- state fixed at `d+1 00:00Z` and used only during `d+1`;
- HIGH `>=2/3`; MID `[1/3,2/3)`; LOW `<1/3`;
- `drift20 = sum(r[d-19:d])`;
- `beta60 = cov(symbol,BTC)/var(BTC)` on the 60 returns ending `d`; BTC=1.

Admission-ledger no-trade minutes do not make a day incomplete: all five have zero collection
gap, zero outage and zero unresolved-error days. Located events remain in the population even
if a later entry/exit mark is unavailable; outcome columns become null with an explicit reason.

### 5.2 Trigger and rank

- Aggregate UTC slots `[00,04)`, `[04,08)`, … from real 1m prints.
- At slot end `t`, compare completed close with day `d-1` high/low.
- Long if `close > high`; short if `close < low`; equality is no event.
- Entry timestamp is `t`; exit timestamp is `t+4h`.
- Daily `vol_pct` ranks descending across five eligible symbols; lexical tie-break.
- TOP2 means rank 1 or 2 only. TOP1/TOP3 cannot become executable.

### 5.3 Signed flow

```text
imbalance    = (BuyVolume - SellVolume) / (BuyVolume + SellVolume)
aligned_flow = direction * imbalance
flow_pct      = midrank percentile against prior 60 completed same-UTC-slot 4h bars
```

Zero-volume trigger bars are flow-ineligible but remain in base. Executable flow condition is
`flow_pct >= 2/3`; continuous percentile and reversed-sign mirror co-report.

## 6. One emission and located-population rule

One row per **located** breakout. Required groups:

1. identity/timestamps/direction;
2. `rv20`, `vol_pct`, tercile, drift20, beta60, rank, flow fields;
3. feature source/known timestamps;
4. prior range and breakout distance;
5. outcome availability flags and reasons;
6. 1h/2h/4h open-to-open signed/absolute outcomes where available;
7. fee, funding stamps, allowance, partial reported net, spread-null disclosure.

Missing future marks never delete the event. Report `located`, `1h_available`, `2h_available`,
`4h_available` and covariate differences between available/missing rows. Only 4h defines the
executable object; 1h/2h are timing descriptions and cannot select another exit.

## 7. Estimands and ordered layers

SPDR outputs are characterisation estimands, not a deployability verdict. Run 2 later reproduces
the frozen episode through canonical `xen.adjudication`.

| Layer | Primary estimand | Secondary reads | Operator choice |
|---|---|---|---|
| L1 partial economics | HIGH 4h signed gross minus fees/funding/2-bps allowance | 0/5 allowance; mean/median/trimmed mean; concentration | ADVANCE or STOP |
| L2 volatility bite | HIGH minus MID/LOW 4h absolute open-to-open move | continuous `vol_pct` dose response; 1h/2h timing | ADVANCE or STOP |
| L3 conversion residue | HIGH minus MID/LOW signed 4h partial residue | unconditional breakout and direction-deranged distributions | ADVANCE or STOP |
| L4 selection | fixed TOP2 minus occupancy/beta-matched random top-2 | TOP1/TOP2/TOP3 distribution; all-core reference | ADD TOP2 or KEEP BASE |
| L5 flow | upper-tercile aligned flow minus remainder on same selected events | continuous dose response; reversed-sign mirror | ADD FLOW or DROP FLOW |

All columns and arms freeze before emission. Layers are revealed in order from one immutable
artifact. Nothing is dropped by code; every operator decision is recorded before the next layer.

## 8. Controls and validity proofs

```text
CONTROL MATCHED-RANDOM-TIMING:
  question answered: does breakout timing add value beyond equal directional exposure?
  population: non-breakout 4h boundaries outside signal [entry,exit) windows; DISJOINT by construction
  bite/MDE: >=2000 seeds; 0.5x/1x/2x plants tied to 10/15/20-bps layer effects and realised MDE
  non-vacuity: changes entry date/path while preserving symbol, side, slot, tercile, third and occupancy
  expected outcome if H true: live residue exceeds seed distribution; if false: live lies within it
  disclosure: live percentile, effect, CI, seed range and control/raw collapse fraction
  destroy form: DERANGEMENT — zero event keeps its original matched date
```

```text
CONTROL UNCONDITIONAL-BREAKOUT:
  question answered: does HIGH volatility add value beyond generic breakout continuation?
  population: MID/LOW breakout episodes; DISJOINT from HIGH by frozen tercile
  bite/MDE: count-derived date MDE plus 0.5x/1x/2x plants around 20-bps absolute and 15-bps signed effects
  non-vacuity: changes volatility state while trigger, execution and hold remain identical
  expected outcome if H true: HIGH absolute/signed distributions shift right; if false: no increment
  disclosure: raw arms, difference, CI, MDE, thirds and collapse fraction
  destroy form: not a permutation
```

```text
CONTROL DIRECTION-DERANGEMENT:
  question answered: is magnitude converted into the registered sign?
  population: zero-fixed reassignment of event directions; control mappings are DISJOINT from true mapping
  bite/MDE: >=2000 seeds and +/-10/15/30-bps planted signed residues
  non-vacuity: moves the signed-return sufficient statistic while preserving absolute paths/times
  expected outcome if H true: true sign exceeds deranged distribution; if false: centred within it
  disclosure: effect, one-sided p, CI, seed range and retained fraction
  destroy form: DERANGEMENT — zero fixed directions/event assignments
```

```text
CONTROL FUTURE-DESTROY:
  question answered: does any reported edge survive after own future is destroyed?
  population: within-symbol/calendar-third reassignment to another event path; DISJOINT own futures
  bite/MDE: every eligible row moved; planted +50-bps future-label sentinel must be detected
  non-vacuity: changes the event-to-own-path pairing used by all return statistics
  expected outcome if H true or false: genuine event alignment collapses; sentinel is detected
  disclosure: fixed-point rate, raw/control effects and collapse fraction
  destroy form: DERANGEMENT — zero fixed points
```

Future-destroy is a hard integrity tripwire. The first three are attribution/report layers.
Drift-only direction and exposure-matched BTC are benchmarks, never vetoes.

### 8.1 Frozen control construction

- **Matched random timing:** candidate units are completed non-breakout four-hour boundaries whose
  `[entry,exit)` interval overlaps no located signal episode. Preserve the live event's symbol,
  assigned side, UTC slot, volatility tercile, effective calendar third and one-episode occupancy;
  exclude the live UTC date. Within that exact cell, form the five nearest candidates by absolute
  `beta60` distance, then sample one uniformly without replacement within each seed. Use seeds
  `41000..42999`. If fewer than five exist, use all available; if none remain, retain the event with
  a null match reason. Report match attrition and beta-distance distribution.
- **L4 random top-2:** the sampling unit is the UTC-date symbol cluster, not an individual episode.
  For each date and seed, consider every two-symbol pair from the five-name eligible cross-section.
  Exclude the realised TOP2 pair before matching. Retain only remaining pairs whose located-episode
  count equals the realised TOP2 episode count on that date;
  among them minimise absolute difference in signed beta exposure
  `sum(direction * beta60)` and sample uniformly across tied minima. Use seeds `51000..52999`.
  Dates with no exact-occupancy pair stay visible with a null-match reason. Report date/episode
  attrition and beta-distance distribution; do not backfill from another date.
- **Direction derangement:** zero-fixed event-assignment derangement within
  `(symbol, effective_calendar_third)` using seeds `31000..32999`. This preserves each stratum's
  direction frequency and every path/time/magnitude. Report the fraction whose assigned sign value
  actually changes; constant-sign or otherwise non-moving strata are uninformative, never dropped
  silently or re-stratified after outcomes.
- **Future-path derangement:** use the same `(symbol, effective_calendar_third)` strata and seeds
  `31000..32999`; the dedicated audit seed is `33000` after the 2,000-seed envelope.

```text
TRIPWIRE: FUTURE-PATH-DERANGEMENT
  metric: HIGH-minus-MID/LOW signed four-hour residue plus a dedicated +50-bps synthetic sentinel
  must collapse: zero-fixed path mapping; raw sentinel recovery 50 +/- 0.5 bps; after derangement the sentinel effect lies inside the frozen 99% synthetic-null envelope; disclose the actual destroyed effect and collapse distribution
  expected-collapse rule: generate at least 2,000 zero-fixed derangements on census keys and synthetic labels before any real outcome column is opened, then freeze the 99% envelope; any fixed point, failed raw sentinel recovery, or post-destroy sentinel outside that envelope invalidates the emission
  vacuity check: the control moves event-to-path pairing, which is the sufficient statistic for signed and absolute outcome contrasts
  sentinel acceptance rule: raw sentinel recovery 50 +/- 0.5 bps and post-destroy result inside the frozen 99% synthetic-null envelope
  derangement=YES (zero fixed points)
```

The **real-edge survival rule** is binding only if the raw L3 effect reaches its frozen SUPPORTED
band (`raw >= +15 bps` and the five-seed 95% date-block CI lower bound is above zero). In that case,
the raw effect must exceed the 99th percentile of the 2,000 future-path-deranged effects
(`empirical one-sided p <= 0.01`) and the absolute destroyed median must be no more than 25% of the
absolute raw effect. Failure invalidates the emission. If raw L3 is not SUPPORTED, this real-edge
rule is `NOT_APPLICABLE` because no positive edge is being authenticated; the synthetic sentinel,
zero-fixed-point and catalog/provenance checks remain binding regardless.

## 9. Inference, dependence and concentration

- Primary resampling: UTC-date blocks retaining every symbol/event on sampled dates.
- Bootstrap: 10,000 circular resamples for each of seeds `101,211,307,401,503`; construct the
  chronological unique-UTC-date sequence, sample 1/3/7 consecutive-date blocks with wraparound,
  and retain every symbol/event attached to each sampled date.
- Statistics: mean, median, 20% trimmed mean; seed-bound ranges.
- Per-symbol before pooled disclosure; pooled requires homogeneity to support a common claim.
- Report unique dates/weeks, same-timestamp clusters and overlap exclusions.
- Report top day/week/symbol/top-decile contribution, leave-one-symbol-out and
  leave-one-effective-third-out.
- Effective DESIGN thirds: `[2022-09-14, 2022-11-09)`, `[2022-11-09, 2023-01-04)`,
  `[2023-01-04, 2023-03-01)`.
- CONFIRM thirds divide its registered interval into equal elapsed-time thirds.
- CONFIRM opens only where prospective MDE <= chronologically shrunk DESIGN effect.

## 10. Interpretation bands — informative only

Per-symbol first; pooled disclosure-only absent homogeneity.

| Layer | SUPPORTED label | WASH label | CONTRADICTED label | UNPOWERED |
|---|---|---|---|---|
| L1 partial net | mean >= +10 bps and CI low > 0 | absolute mean < 10 bps | mean <= -10 and CI high < 0 | MDE > 20 bps |
| L2 absolute bite | increment >= +20 and CI low > 0 | absolute increment < 10 | increment <= -20 and CI high < 0 | MDE > 20 bps |
| L3 signed increment | increment >= +15 and CI low > 0 | absolute increment < 7.5 | increment <= -15 and CI high < 0 | MDE > 15 bps |
| L4/L5 modifier | increment >= +10 and CI low > 0 | absolute increment < 5 | increment <= -10 and CI high < 0 | MDE > 10 bps |

These labels never decide progression. “CI excludes zero” is evidence wording, not a pass.
Expected pre-run state: every per-symbol small-effect stratum is UNPOWERED; only a large effect
can be resolved. The operator may stop rather than pay for an under-informative run.

```text
POWER: expected DESIGN events/dates per HIGH stratum:
  BTC=54/19 ETH=54/14 SOL=115/42 DOGE=71/20 XRP=100/33 pooled=394/74
  MDE at sigma=100 bps: per-symbol one-sample 43.2..74.8 bps; pooled 32.5 bps
  strata predeclared UNPOWERED: every per-symbol effect <=40 bps; all modifier effects <=10 bps
```

## 11. Costs and claim boundary

- Entry/exit taker fee: 11.0 bps round trip.
- Funding: count 00:00/08:00/16:00 UTC stamps in `(entry,exit]`; adverse 1.0 bps each.
- Allowance: 2.0 bps governing; 0/2/5 bps reported.
- Apply `xen.evaluation.bybit_round_trip_cost_bps` with no `spread_bps`.

```text
SPREAD-COST-DISCLOSURE:
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: reported cost understates total cost; reported net performance is overstated
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

Raw `SpreadBps`, `MeanPriceSkewBps`, flip pairs and former proxy pins are prohibited inputs.

## 12. Golden traces — independently specified fixtures

Synthetic prices prevent outcome contact while fixing event/fill semantics.

| ID | Known at trigger | Expected action | Entry / exit fixture | Expected 4h gross |
|---|---|---|---|---:|
| GT-1 LONG | 2022-10-01 04:00; prior H/L 105/95; completed close 106; HIGH | long at 04:00 | RealOpen 107; 08:00 RealOpen 104 | `(+1)*(104/107-1)*1e4 = -280.374 bps` |
| GT-2 SHORT | 2022-10-02 20:00; prior H/L 110/90; completed close 89; MID | short at 20:00 | RealOpen 88; 00:00 RealOpen 84 | `(-1)*(84/88-1)*1e4 = +454.545 bps` |
| GT-3 EQUALITY | 2022-10-03 08:00; prior H/L 120/100; completed close 120 | no event | no order, no episode | N/A |

Actual no-price membership anchors from the census: BTC `2022-09-17T16:00Z` long, DOGE
`2022-10-27T04:00Z` long, ETH `2022-09-25T20:00Z` short. QA may verify causal inputs, but
must not open their entry/exit prices before execution approval.

## 13. Integrity, implementation and run contract

```text
HARD (block): TRAIN/TEST/holdout fence, source hashes, causal provenance <=t,
  no post-event eligibility conditioning, signed-lane attestation, future-destroy collapse,
  sentinel detection, deterministic emission, no local accounting.
INFORMATIVE (operator judges): all effects, MDEs, bands, p/CI reads, costs,
  concentration, attribution collapse, modifier comparisons and CONFIRM retention.
```

Implementation must:

1. assert census/result hashes and reproduce all 3,606 event IDs before outcomes;
2. bulk-ingest and attest signed TRAIN data before adding flow columns;
3. emit one immutable TRAIN artifact with DESIGN and sealed CONFIRM columns;
4. keep CONFIRM unread until one rule/config hash is frozen;
5. run >=2,000-seed controls and the hard tripwire only after schema/fence checks;
6. write no `pass`, auto-verdict or candidate-drop field;
7. use shared `xen.evaluation`; no experiment-local P&L/accounting primitive;
8. emit source-known timestamps and assert `known_ts <= trigger_ts` row by row.
9. re-hash the live signed-catalog tree immediately before the engine read and require exact equality
   with the attested catalog-tree hash;
10. issue one explicit tagged ENTRY and one explicit tagged EXIT market order per event, including
    contiguous same-direction episodes, then reconcile each complete event to Nautilus fills:
    exactly one fill per action, correct side, fill source timestamp at `entry_ts+1m` / `exit_ts+1m`,
    and fill price equal to the corresponding first-minute `RealOpen` within relative `1e-9`.
    An unavailable event must carry its frozen reason and cannot masquerade as a complete fill pair.

The immutable emission is one artifact **bundle** with a manifest hash over two parquet members:
`design.parquet` and `confirm.parquet`. The analysis entry point may read `design.parquet`
immediately. It must reject `confirm.parquet` unless a separate append-only unlock record supplies
the exact pre-frozen rule/config hash and explicit operator CONFIRM authority. Direct filesystem
readability is not claimed as cryptographic secrecy; the seal is a deterministic access-control and
audit contract. Any direct CONFIRM read outside that entry point is a governance breach recorded in
the test-read ledger.

No execution command is supplied until fresh QA approves and the operator separately authorises
the run.

## 14. Amendment-direction ledger

```text
AMENDMENT-A1: remove all fixed spread proxies; disclose null/unavailable spread
  DIRECTION: LOOSER — running count: 1 looser / 0 tighter / 0 neutral
AMENDMENT-A2: define stability/matching thirds over effective eligible DESIGN coverage
  DIRECTION: NEUTRAL — running count: 1 looser / 0 tighter / 1 neutral
AMENDMENT-A3: retain every located event; later path absence is null attrition, not eligibility
  DIRECTION: NEUTRAL — running count: 1 looser / 0 tighter / 2 neutral
AMENDMENT-A4: freeze control seeds, match units/strata and logical CONFIRM bundle seal
  DIRECTION: NEUTRAL — running count: 1 looser / 0 tighter / 3 neutral
AMENDMENT-A5: exclude the realised TOP2 pair from the L4 random-pair null
  DIRECTION: TIGHTER — running count: 1 looser / 1 tighter / 3 neutral
AMENDMENT-A6: bind live catalog re-hash, supported-edge destroy survival and event-to-fill reconciliation
  DIRECTION: TIGHTER — running count: 1 looser / 2 tighter / 3 neutral
```

There is no qualification gate, so a global-null false-qualifier count is inapplicable. All
predeclared arms remain visible; no arm is selected by performance.

## 15. Execution gate

SPDR-011 remains blocked until all are true:

- five signed TRAIN histories bulk-ingested with the §3.4 attestation — **SATISFIED**;
- implementation reproduces census membership and synthetic golden traces;
- fresh-context `qa-compliance` review records `APPROVE` in append-only `qa-review.md`;
- operator separately authorises outcome emission.

QA approval will not itself authorise execution. TEST, holdout and any deployment claim remain
outside this design.
