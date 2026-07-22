# Checkpoint 016 — Volatility-to-Direction Conversion

- **Opened:** 2026-07-22
- **Status:** `OPEN — FAMILY REGISTERED / RUN-1 DESIGN PENDING`
- **Family:** `CF-VOLCONV-001` (`REGISTERED`)
- **Container:** `SPDR-011` count-only census + TRAIN characterisation; conditional `EXP-099`
  Nautilus replay
- **Authority:** checkpoint opening and family registration approved; no execution or outcome read
  approved

## Why this checkpoint exists

The programme repeatedly found material drift, beta and volatility clustering but did not convert
directionless volatility information into a deployable directional object. This checkpoint tests one
bounded conversion: lagged daily volatility forecasts movement magnitude; a completed four-hour break
of the prior UTC-day range supplies direction; one fixed four-hour episode tests whether useful residue
remains. It does not reopen multi-day trend, P-01 geometry, or the closed signed-auction family.

## 1. Governing sources and precedence

1. `docs/references/chapter-05-governance.md` — live gate and permission boundary.
2. `.ignore/what-next/alts/intraday-way-forward-plan.md` — complete approved route.
3. `docs/signal-registry/candidate-families/cf-volconv-001.md` — registered family contract.
4. This checkpoint — sequence, ownership and stop conditions.

The operator's no-spread amendment governs conflicts: no stored spread, flip-pair proxy or fixed pin
enters Chapter-05 cost accounting.

## 2. Preconditions — verified before opening

| Requirement | State |
|---|---|
| Chapter-04 rollover | Complete: commit `839b443`, tag `chapter-04-close` |
| Cost/data preflight | Complete: no-spread amendment QA run 10 APPROVE |
| Stored spread field | Quarantined as `MeanPriceSkewBps / UNUSABLE_AS_SPREAD`; never a cost input |
| Cost accounting | Fees + discrete funding; spread `null`; mandatory partial-cost caveat |
| Historical TEST | Sealed for this family; prior related contact makes it ineligible as confirmation |
| Global holdout | Sealed; no exception |
| Family registration | `CF-VOLCONV-001` registered by this checkpoint opening |
| Run execution | Not authorised |

## 3. Fixed question and mechanism

> Does a causally known high-volatility state leave enough signed movement after a completed
> four-hour breakout to support one four-hour market-entry episode under the available fee,
> funding and execution-allowance accounting, with spread explicitly unavailable?

```text
MECHANISM:
  Volatility clusters across adjacent sessions. HIGH lagged daily volatility predicts greater
  near-future absolute movement but not sign. A completed four-hour break of the prior confirmed
  UTC-day range supplies a causal sign. P&L belongs to one non-overlapping four-hour episode.
DERIVED:
  estimand=one signed four-hour episode
  null=matched non-event timing and identical MID/LOW breakouts
  horizon=4 wall-clock hours
  test=partial-cost residue plus incremental volatility-state contrasts
```

```text
OBJECT-IDENTITY:
  measurement object == trading object: YES — next-boundary open to open exactly 4h later
  measured conditioning event == traded entry event: YES — completed 4h range break
  effect-splitting windows non-overlapping: YES — later triggers ignored until exit
```

## 4. Frozen scope

| Item | Decision |
|---|---|
| Core | BTCUSDT, ETHUSDT, SOLUSDT, DOGEUSDT, XRPUSDT |
| Detection | completed 4h close strictly beyond prior confirmed UTC-day high/low |
| Entry/exit | next 4h boundary's first 1m `RealOpen`; exit `RealOpen` exactly 4h later |
| Volatility | causal daily `rv20`; percentile against prior ≤252 observations; 60-day warm-up; HIGH ≥2/3 |
| Cross-section | TOP2 is sole executable candidate; TOP1/TOP3 distribution only |
| Signed flow | direction-aligned exact aggressor imbalance; causal same-slot 60-bar percentile; upper tercile candidate |
| Controls | drift20 and beta60 as matching/benchmark columns only |
| Costs | taker fees + discrete funding + 0/2/5 bps allowance; spread unavailable/not charged |
| DESIGN | 2021-06-29T06:53Z → 2023-03-01T00:00Z |
| CONFIRM | 2023-03-01T00:00Z → 2023-12-18T00:00Z, one frozen-rule read |
| TEST / holdout | never loaded |

No threshold, symbol, direction, horizon or exit may be selected by outcome performance.

## 5. Research items and sequence

| Order | Item | Purpose | Start gate | Status |
|---:|---|---|---|---|
| 1 | `SPDR-011` census | Count eligible events and dependence clusters without opening outcomes; derive prospective MDE and 2–3 golden events | family registered; outcome isolation proven | **NEXT — not run** |
| 2 | `SPDR-011` design | Freeze schema, controls, plausible effect/MDE bands, golden traces and layer protocol | census artifact only | pending |
| 3 | `SPDR-011` QA | Fresh-context design/code review | completed design | pending |
| 4 | `SPDR-011` execution | Emit one TRAIN-only event artifact | QA APPROVE + separate operator approval | unauthorised |
| 5 | DESIGN layers | L1→L5 sequential operator reads; stop/drop/advance recorded after each | valid frozen artifact | unauthorised |
| 6 | CONFIRM | One read of one frozen rule; no replacement | rule hash + prospective power | unauthorised |
| 7 | `EXP-099` | Nautilus reproduction, canonical accounting and physicality | Run-1 rule/evidence accepted + new design/QA/operator approval | reserved only |
| 8 | Retrospective/shadow | Family disposition or frozen forward observation | operator verdict | pending |

The `SPDR → EXP` path is the operator-approved exception. XENA is prohibited because there is no
candidate grid or portfolio search.

## 6. Run-1 report layers

All layers come from one frozen event artifact. Nothing is re-mined between layers.

| Layer | Registered question | Candidate consequence only |
|---|---|---|
| L1 partial economics | Does HIGH-vol residue survive fees, discrete funding and allowance, with spread missing? | Powered wash/negative supports STOP recommendation |
| L2 volatility bite | Does HIGH predict more post-entry absolute movement than MID/LOW? | No increment supports STOP recommendation |
| L3 conversion residue | Does HIGH improve signed residue beyond identical unconditional breakout? | No increment supports STOP recommendation |
| L4 TOP2 increment | Does fixed TOP2 improve the all-core base under beta/occupancy controls? | If absent, retain all-core base |
| L5 flow increment | Does fixed upper-tercile aligned flow add value on the same events and survive reversed-sign mirror? | If absent, permanently drop flow for this object |

Each layer reports `observed / ideal / interpretation`; no `pass` field. The operator signs
`ADVANCE`, `DROP MODIFIER`, or `STOP` before another layer is opened.

## 7. Deterministic rule freeze

1. Base is always HIGH-vol + completed breakout + four-hour episode on all five symbols.
2. L4 can add only TOP2; TOP1/TOP3 cannot become executable.
3. L5 can add only upper-tercile aligned flow.
4. No winning symbol, side, threshold, horizon or exit selection.
5. Final config and input hashes freeze before CONFIRM.
6. CONFIRM reports retention/shrinkage and cannot select a replacement.

## 8. Controls and validity requirements

### Matched random timing — primary attribution

Disjoint non-breakout next-four-hour opens matched on symbol, direction, UTC slot, volatility tercile,
calendar third and hold; at least 2,000 deterministic seeds and equal occupancy. It changes timing and
future path while preserving direction/exposure marginals. Plant curve: 0.5×/1×/2× plausible effect.

### Unconditional breakout — mechanism control

MID/LOW breakouts are disjoint from HIGH episodes and use the identical trigger, entry and hold. This
owns the claim that volatility contributes beyond generic breakout drift.

### Direction derangement and benchmarks

Direction is deranged at fixed event times with zero fixed points across at least 2,000 seeds. Drift-only
direction and exposure-matched BTC are benchmarks, never machine vetoes.

### Hard future destroy

Derange each post-entry path to another eligible within-symbol/calendar-third date, zero fixed points,
while pre-entry features remain unchanged. Survival or failure to detect the future-label sentinel
invalidates the artifact; it is not evidence against the signal.

## 9. Dependence, uncertainty and power

- Count events by symbol, UTC date/week, direction, tercile and calendar third before outcomes.
- Report same-timestamp clusters, overlap exclusions, missing-path attrition and effective dates.
- Bootstrap UTC-date blocks retaining all cross-symbol events; sensitivity at 1/3/7 days.
- Per-symbol first; pooled disclosure only unless homogeneity is demonstrated.
- Mean, median, 20% trimmed mean, block sensitivity and bootstrap seed ranges co-report.
- Leave-one-symbol and leave-one-calendar-third out; top day/week/symbol/top-decile concentration.
- Every layer reports realised MDE; `MDE > plausible effect` is UNPOWERED, never a negative.
- CONFIRM opens only if prospective MDE ≤ chronologically shrunk DESIGN effect.

No event-count or power number is asserted at checkpoint opening. Those values must come from the
outcome-isolated census and be frozen in `SPDR-011/design.md` before outcome contact.

## 10. Cost disclosure

```text
SPREAD-COST-DISCLOSURE:
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: reported cost understates total cost; reported net performance is overstated
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

The research allowance covers slippage/impact sensitivity; it is not a disguised spread estimate.
Run-2 shadowing, if eventually authorised, measures decision-to-fill costs prospectively without
retrofitting historical outcomes.

## 11. Hard gates versus reports

**Hard:** holdout/TEST isolation, causal `≤t-1` provenance, schema/fence validity, future-destroy,
positive-control detection, Nautilus estimand reconciliation.
**Informative:** all effect sizes, uncertainty, MDE, control collapse, cost curves, concentration,
physicality and value labels. The operator alone advances or stops value layers.

## 12. Amendment ledger

| Amendment | Direction | Running count |
|---|---|---|
| A1 — operator removed all fixed spread proxies; missing spread is null with mandatory partial-cost caveat | `LOOSER` | 1L / 0T / 0N |

Any later change to data, instruments, trigger, state, horizon, cost regime, control, threshold,
direction rule or route requires an amendment before outcome contact. After results exist, it is a new
design, not a rescue amendment.

## 13. Stop boundary and deliverables

This opening delivers only the registered family and checkpoint container. It authorises no census,
outcome column, SPDR execution, EXP execution, TEST, holdout or shadow action.

Next permitted work is an outcome-isolated count-only census and `SPDR-011/design.md`. That design
must include the full mandatory declaration blocks, prospective MDE, golden traces and fresh-context
QA before the operator is asked to approve execution.
