# The Unsigned Failed-Break Bounce — Standalone Viability Review

**Purpose.** SPDR-008 killed the *signed* trap-load warrant (CF-SIGAUC-001, powered null on three
boundaries). It left behind one object that **clears its cost floor**: the unsigned failed-break
reversal at prior value-area and prior-session-extreme levels. This brief asks the question the
screen was never designed to answer — **stripped of the signed claim, is that object a model?**

**Status.** Extraction + re-analysis of already-emitted SPDR-008 DESIGN/CONFIRM data. **No new
experiment, no new claim, no family status change.** Computed 2026-07-22 from
`python/experiments/SPDR-008/results/trap_{DESIGN,CONFIRM}.parquet` and `layers.json`.

**Verdict in one line:** the availability effect is **real, reproducible on 2 of 3 boundaries, and
too small and too one-sided to be a strategy** — it is a **~5–11% relative lift on a mean-based
excursion ceiling**, measured on an object for which **no realized return was ever computed**.

**Reading map.**

| Need | Where |
|---|---|
| This review | **this file** |
| The general availability-vs-capture problem | [capture-geometry-review.md](capture-geometry-review.md) |
| Design fixes for capture stacks | [capture-geometry-recommendations.md](capture-geometry-recommendations.md) |
| Family disposition + the signed null | [families-explored.md](../families-explored.md), `docs/signal-registry/candidate-families/cf-sigauc-001.md` |
| Dead ends (P-01 in particular) | [pitfalls-ledger.md](../pitfalls-ledger.md) |
| Source screen | `python/experiments/SPDR-008/` (`report.md`, `analysis.md` §A5/§A6) |

---

## 1. The object

A **failed break** at a structurally qualified level: price pokes through a boundary, fails to hold,
and reclaims. Entry on the reclaim, side = reversal direction. Three boundary types were tested
**independently** (no cross-boundary pooling for the promote rule):

| code | boundary |
|---|---|
| `IB` | this session's initial-balance edge |
| `PVA` | prior session's value-area edge (K-UNIFORM profile) |
| `PRIOR` | prior session's true extreme |

Universe: 194 A5-fitted Bybit USDT-perp symbols (breadth denominator 296, survivorship caveat
binding). **16,669 DESIGN traps / 26,348 CONFIRM traps.**

**What makes it interesting:** it is the *only* thing in the CF-SIGAUC-001 arc whose effect size sits
above the cost floor. Signed trap load is a powered null (ρ −0.015 / +0.023 / −0.033, MDE ≈ 0.02);
the unsigned geometry underneath it is not null.

**What makes it suspect before any number is read:** it is **price-only, single-instrument,
directional geometry** — the exact shape of **P-01**, which the programme has dispositioned dead
twice (Chapter 01 AVWAP arc; SPDR-007's price-only session spine). The re-open bar for P-01 is a
*new information source*, and stripping the signed claim removes the only thing that was new.

---

## 2. What reproduces, and what does not

`T4_availability` = trap MFE − matched-random-timing MFE, in IB-width units, day-clustered CI.

| boundary | DESIGN contrast | CONFIRM contrast | reproduces? |
|---|---|---|---|
| **PVA** | **+0.479 IBw**, CI [0.402, 1.219] | **+0.295 IBw**, CI [0.069, 0.867] | **yes** — both bands, pooled and day-mean agree |
| **PRIOR** | **+0.484 IBw**, CI [0.145, 0.786] | **+0.270 IBw**, CI [0.120, 0.666] | **yes** — both bands |
| **IB** | +0.043 IBw pooled *(day-mean +0.702, CI [0.24, 1.21])* | **−0.494 IBw**, CI includes zero | **NO** |

**IB is an artifact, and its mechanism is documented.** The reported `contrast` is event-weighted;
the `day_clustered_ci` is centred on the **unweighted day-mean**. Pooled IB DESIGN is ≈ 0 (+0.043)
while the day-mean is +0.702 — the "excludes zero" is produced entirely by day weighting, and
CONFIRM flips negative. **Any future use of this object must drop IB and align point estimate and
interval on one weighting.**

So "consistent availability" is true for **two** boundaries, not three.

---

## 3. Why it still is not a model — four measurements

### 3.1 The lift is small relative to a base that random timing already gets

| boundary / band | trap MFE | matched-random MFE | absolute lift | **relative lift** |
|---|---|---|---|---|
| PVA DESIGN | 5.457 IBw | 4.978 IBw | +0.479 | **+9.6%** |
| PVA CONFIRM | 5.846 | 5.551 | +0.295 | **+5.3%** |
| PRIOR DESIGN | 4.891 | 4.407 | +0.484 | **+11.0%** |
| PRIOR CONFIRM | 5.242 | 4.971 | +0.270 | **+5.4%** |

Random-timing entries on the same symbols capture **~90–95%** of the excursion the conditioned
events do. The level is not creating the move; it is marginally concentrating one that is already
there. **That is the P-01 statement in numbers**, and it is the same shape as SPDR-007's spine
(signal 0.333 vs control 0.343) and the Chapter-01 AVWAP finding (event MFE ≈ matched-control MFE).

### 3.2 The measured quantity is a ceiling, not a return

The emission carries `mfe_rev_bps`, `mfe_rev_norm`, `mae_rev_norm`, `race` — **there is no realized
return column at any exit, in either band.** MFE is the best price the path ever offered. Converting
it to P&L requires an exit rule, and no exit rule was ever specified or measured.

This is precisely the **capture-geometry wall** catalogued in
[capture-geometry-review.md](capture-geometry-review.md): availability ≠ capture, and the programme
has now hit it in five vehicles. Citing ~31–56 bps of "edge" from an MFE contrast is a **Mode-A**
error unless an exit is declared and charged.

### 3.3 Adverse excursion is nearly as large as favourable

Computed from the raw parquet (`mae_rev_bps` = `mae_rev_norm` × implied IB-width in bps):

| boundary (DESIGN) | median MFE | median MAE | ratio |
|---|---|---|---|
| PVA | 352.4 bps | **261.9 bps** | 1.35 : 1 |
| PRIOR | 328.1 bps | **244.8 bps** | 1.34 : 1 |
| IB | 386.1 bps | 307.3 bps | 1.26 : 1 |

(CONFIRM: 267/235, 266/204, 333/244 — same shape.) You must survive ~0.75 bps of adverse movement
for every 1 bps of favourable movement available. Any capture stack on this object is fighting a
near-symmetric path.

### 3.4 Under the screen's own exit convention, four of five events stop out

`race` is a realized three-way outcome — target = **full rotation to the opposite edge**, stop =
**back through the poke extreme**, same-bar hits resolved **pessimistically as STOP**
(`xen.sigbar.trap._race_outcome`):

| boundary | band | TP | STOP | TIMEOUT |
|---|---|---|---|---|
| PVA | DESIGN | 14.6% | **81.4%** | 4.0% |
| PVA | CONFIRM | 13.5% | **83.2%** | 3.2% |
| PRIOR | DESIGN | 5.1% | **81.6%** | 13.4% |
| PRIOR | CONFIRM | 5.6% | **81.3%** | 13.0% |
| IB | DESIGN | 38.4% | 61.6% | 0.0% |
| IB | CONFIRM | 41.0% | 58.8% | 0.2% |

**Read this fairly.** It is *one* exit convention and a deliberately ambitious one — a full rotation
target with a stop sitting just beyond entry. A nearer target would convert more often. The point is
not "81% loss rate"; the point is that **the only realized-outcome statistic in the emission is
strongly negative, and no alternative exit was ever measured.** The object's P&L is unknown, not
promising.

---

## 4. Statistical fragility carried from the source screen

Three defects that bind on any re-use, all disclosed in `SPDR-008/analysis.md` §5:

1. **Every contrast is a mean on a heavily right-tailed quantity.** `mfe_rev_norm` medians are
   3.2–3.6 IBw against means of 4.9–5.5; q99 ≈ 25–32; max 141–211. Small-IB-width sessions inflate
   the normaliser. T2/T3/T4 are all mean-based and therefore tail-driven. (The rank-based T1 ρ — the
   screen's primary — is immune, and it is cleanly null.)
2. **The median/trimmed re-read was scheduled and never ran.** It was ckpt-015's cheap analysis
   follow-up; the checkpoint closed without it. Until it exists, treat the ~31–56 bps figure as an
   **upper-ish bound**, per L-19-style tail discipline.
3. **T4's CI omits control-side resampling variance**, and its point estimate and interval use
   different weightings (§2). Intervals are optimistic and the estimator is mismatched.

---

## 5. What it would take to make this a model

Not a re-read of SPDR-008 — a **new design**, in a **price-geometry family**, not a signed-flow one.
The minimum contract:

| # | Requirement | Why |
|---|---|---|
| 1 | A **realized-return estimand** at a declared exit, open-to-open, in money units | MFE is a ceiling; §3.2 |
| 2 | **Exit ablation** — ≥3 exit families, verdict must not be exit-contingent | Chapter-01 EXP-081/084 precedent: 0/11 exit arms cleared |
| 3 | **Median / trimmed** primary statistic + finite guards | §4.1; the mean is tail-driven |
| 4 | **Control-side resampling** in every CI; one weighting for point and interval | §4.3 |
| 5 | **Cost charged on the binding leg** — per-symbol spread, not the 14 bps ex-spread floor | Cost floor here is fee 11 + funding 3, spread still **UNUSABLE** (INFR-019 never built) → **no net claim is admissible today** |
| 6 | **PVA/PRIOR only**, IB excluded and stated | §2 |
| 7 | A **P-01 distinctness argument that survives without the signed input** | The Δ measurement was the whole warrant; removing it puts the object back inside a twice-dead pitfall |

Requirement 7 is the hard one, and it is a **mechanism** question, not a statistics question. Without
a new information source, this is single-instrument directional price geometry with a ~5–11%
availability lift over random timing — which is the profile the programme has already refuted twice.

---

## 6. Disposition

**Keep as market-science characterisation. Do not promote. Do not re-open as a family without
clearing §5.7.**

Recorded honestly: failed breaks at prior value-area and prior-session extremes are followed by
modestly wider favourable excursions than matched random entries, reproducibly across two TRAIN
bands, on 194 instruments. That sentence is true and worth keeping. It is **not** a tradability
claim, and the emission contains no evidence that could support one.

The one-line summary from the source analysis still stands and should be quoted rather than
softened:

> *"Nothing signed clears it; the unsigned availability that does is a ceiling, not a return."*
> — `SPDR-008/analysis.md` §A6

---

## 7. Cross-references

- **Capture geometry**: this is another instance of the programme's highest-frequency disqualifier —
  see [capture-geometry-review.md](capture-geometry-review.md) §1.2 failure modes and the
  independent-review checklist at its tail.
- **P-01** ([pitfalls-ledger.md](../pitfalls-ledger.md)): single-instrument directional price
  geometry; re-open requires a new information source, screened availability-first.
- **CF-SIGAUC-001** (`docs/signal-registry/candidate-families/cf-sigauc-001.md`): **CLOSED
  2026-07-22**. This object is the family's retained characterisation, not a surviving candidate.
- **Availability-first rule** ([methodology-canon.md](../methodology-canon.md)): screening
  availability before capture is correct — but an availability *pass* must never be reported in
  return units.

---

*Written 2026-07-22 from emitted SPDR-008 data at the checkpoint-015 close. Re-analysis only: no
new experiment was run, no TEST or holdout data was touched, and no family status was changed by
this document. Append-merge at the next rollover if the object is ever designed properly.*
