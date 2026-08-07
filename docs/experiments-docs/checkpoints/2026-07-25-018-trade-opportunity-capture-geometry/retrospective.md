# Checkpoint 018 — Retrospective (CLOSED)

- **Opened:** 2026-07-25
- **Closed:** 2026-08-07 — operator-signed
- **Family:** `CF-VOLDIR-001` — **`RETIRED — CHARACTERISED, NOT TRADABLE`** (status change; see §7)
- **End-state:** **CAPTURE GEOMETRY CHARACTERISED / NO EXTRACTABLE EDGE AT THE MEASURED JOINT.**
  Not a bare null: the checkpoint measured the joint `(p, W, L)` at power, established *why*
  it sits where it sits, and demonstrated that the levers proposed to move it are either
  arithmetically constrained mirrors of each other or below their own detection floors.
- **Reads:** TRAIN only. **0 counted TEST reads. 0 multiplicity slots spent.** Global holdout
  sealed throughout, on both universes.
- **Successor:** none within this chapter. The chapter closes here
  (`archive/chapter-05-voldir-capture-geometry/ROLLOVER.md`).

```
SPREAD-COST-DISCLOSURE
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: every money figure in this checkpoint understates true cost
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

The spread exclusion is a **standing programme-wide condition since 2026-07-23**, not an open
item of this checkpoint. It travels with every number below.

---

## 1. What the checkpoint asked

Checkpoint-017 closed with the extraction question unresolved *at power* — 0 of 927 cells
powered. Checkpoint-018 asked one question in two parts:

1. **Can the residue be powered at all**, and if so, where does the joint `(p, W, L)` actually
   sit relative to its own net break-even?
2. **Is there capture geometry** — native entry/exit/management adapted to volatility state —
   that moves that joint in a direction the fixed baseline does not already contain?

The organising identity was corrected at the checkpoint's opening and held throughout:

```
E[net] = p·W − (1−p)·L − cost
p_be_net = (L + cost) / (W + L)
edge = p − p_be_net
```

The target was explicitly **not** `p > 0.5`. An edge exists at `p < 0.5` whenever `W > L`.
This mattered: it is the reason the checkpoint measured `W/L` as a first-class handle rather
than treating hit rate as the object.

Both parts were answered. The checkpoint delivered its diagnostic product.

---

## 2. Execution record

| Item | Vehicle | Outcome |
|---|---|---|
| Powering sweep over the complete 017 residue | `SPDR-018` | **COMPLETE AND CLOSED** 2026-07-26 — `HYP-D5` SUPPORTED (powering succeeded; no gating verdict). 37,791 cells / 24,098 signed; 18 HARD checks, 0 failed |
| Second-universe replication | `SPDR-018B` | **COMPLETE AND CLOSED** 2026-07-26 — `HYP-D5` PARTIALLY SUPPORTED. cTrader EURUSD/XAUUSD/USTEC, INFR-021 fence; 7,578 cells; 11 HARD + 1 INFORMATIVE, 0 failed. **Replication only — never pooled into crypto `n`** |
| Mid-checkpoint reflection | *(no emission)* | **SIGNED 2026-07-30** — evidence inventory + three-experiment replacement design approved |
| Adaptive management, breakout substrate | `SPDR-021` | **COMPLETE** — six TRAIN cells, amended rerun `20260803T140238Z`, integrity-clean, 13/13 reproduction hashes |
| Adaptive management, MOMO breach | `SPDR-022` | **COMPLETE** — same stamp, same integrity standard |
| Adaptive management, MR breach | `SPDR-023` | **COMPLETE** — same stamp, same integrity standard |
| Confirmation extraction across 021/022/023 | *(no emission)* | **SIGNED 2026-08-05** — eleven confirmations `X-01…X-11`; four refutes, zero economic support |
| Successor characterisation, SIZE-only | `SPDR-024` | **COMPLETE** — four cells (`crypto`/`ctrader` × `H1`/`H4`), 17 HARD each, `blocking_pass` true on all four; **H4 run for the first time in the programme**. First emission defective (§5), purged, re-emitted under AMENDMENT-7 |
| XENA graduation | `XENA-VOLDIR-001` | **RESERVED, never opened** — no graduated base, at any point |

Integrity across the whole checkpoint: every emission passed its own declared HARD set,
reconciled **by name and by count** (the count reconciliation is itself a checkpoint-018
apparatus addition, forced by `L-52`). No emission was adjudicated on a value gate.

---

## 3. What the checkpoint established

### 3.1 The joint sits at break-even, and the distance is cost

Measured, both universes, powered:

| | crypto (25 symbols) | cTrader (3 instruments) |
|---|---|---|
| Powered signed cells | **1,413** (against 017's 0 of 927) | **315** |
| `p` | 0.3887 | 0.4868 |
| `p_be_net` | 0.4992 | 0.4855 |
| `edge` | **−0.0728** | gap **+0.0013** |
| `W` / `L` | 128.65 / 75.55 | — |
| `W/L` | 1.4844 | — |
| Gross mean | −1.18 bps | **−0.080 bps = 0.006σ** |
| Cells clearing **net** break-even | **0 of 1,413** | **0 of 315** |
| Cells clearing **gross** break-even | 32.5% | — |
| Share of the gap that is **cost** | **91%** | **95.8%** |

The identity reconciles to 1.46e-11 bps. The structure replicates on the second universe
**more tightly than on the first** — which is the strongest single statement the checkpoint
produced, because the two universes share no instruments, no venue, no cost model and no
data vendor.

**Mechanism.** The joint is not near break-even by coincidence. It is near break-even because
`W/L` is ~97% the **arithmetic mirror** of `p` — R² 0.9667 (crypto) and **0.9746** (cTrader),
slope 0.9656. Exit geometry moves `W/L` by 36–67×, and `p` moves inversely by very nearly the
compensating amount, leaving the mean where it was. 82.8% (crypto) and 93% (cTrader) of cells
are statistically indistinguishable from the driftless mirror. **`W/L` is not a free lever.**
It is the same number as `p`, written differently.

### 3.2 Adaptive capture geometry adds nothing over the fixed baseline

Eleven confirmations from `SPDR-021/022/023` (full ledger:
`confirmation-extraction-021-023.md`). The load-bearing ones:

- **X-01 — the two breach screens are one substrate.** `SPDR-022` and `SPDR-023` are the same
  trades with the sign flipped; their fixed baselines cancel to **exactly zero**, symbol by
  symbol, and their native geometry effects mirror at r = −0.98. The apparent "native geometry
  effect" is a **direction artifact**, not a geometry effect.
- **X-02 — admission rules never change what a shared trade is worth.** Threshold, expiry and
  band `H` alter *which* trades happen and move the value of the shared ones by **exactly zero
  on ~2.3 million paired trade rows**. They belong on the origin lens only. `BAND_Z` — a price
  offset, not an admission rule — is the one exception and does move outcomes.
- **X-03 — vol-gated hold length is inert.** Moves elapsed-time metrics exactly as coded and
  trade value not at all: 6/6 cells, effect 0.03–0.60× its own detection floor.
- **X-04 — vol-gated stop distance is worse than a fixed one.** Gating **shrinks** the
  loss-severity effect 1.3–18× versus the plain fixed distance.
- **X-05 / X-06 — vol-scaled trails give back more when wider** and bank no larger share of the
  move; nothing is recoverable after a vol-adapted stop.
- **X-07 — the one surviving lever.** Sizing down in flagged high-volatility states makes
  drawdowns shallower: **236 of 236 resolving rows on one side, 6/6 cells**, on the
  best-populated device in the study. But the median effect sits **below the detection floor
  everywhere** (est/MDE 0.20–0.97) and collapses under continuous scaling. Direction near-certain,
  magnitude unmeasured. This is what routed `SPDR-024`.
- **X-11 — hold caps on top of level exits destroy value**, 4–60 bps a trade in all six cells
  (comparator caveat: single-device arm, so device count was not held fixed).

### 3.3 Three structural blindnesses, found and fixed

`SPDR-021/022/023` could not answer three questions **by construction**, not by weakness:

1. **Selection quality was unaskable** — rejected origins carried `outcome_bps = 0.0`, so the
   counterfactual for a declined trade did not exist.
2. **Regime conditioning was unaskable** — arms were *gated by* volatility state but outcomes
   were never *labelled with* realised state.
3. **Sizing was unaskable** — per-trade bps is per-unit-notional, so the paired SIZE delta was
   exactly `0.000000` on 1,400 of 1,400 rows in **all six cells**. The primary estimand was
   arithmetically blind to the one device that survived.

`SPDR-024` was registered specifically to make these three askable, and emitted all three:
realised regime label per origin and per trade (`E1`), counterfactual outcome for excluded
origins (`E2`), and a **capital-normalised** primary estimand (`E6`) that is not blind to size.

### 3.4 What SPDR-024 then measured

Four independent cells, never pooled across universe or horizon. SIZE only —
`STATE_HALVE_HIGH` on eight volatility components plus continuous `SCALE_NORMALISED` on
`RANGE_SCALE` / `SWING_SCALE`. Gross, no cost of any kind.

- **Scale channel.** Effects are small in σ̂ units relative to their bootstrap floors on most
  rows; intervals **frequently cross zero** at the governing treatment. On `crypto_H1`, 4 of 10
  governing rows are CI-negative — the expected arithmetic sign when SIZE is halved on a
  positive-expectancy baseline, not evidence of a harmful device.
- **Exposure is not selectivity.** SIZE exposure terms are first-class and often larger than the
  selectivity terms. Gate-permutation p-values **frequently fail to reject** the null that the
  volatility gate is exchangeable with a random gate. A raw paired SIZE difference can look like
  edge when it is mostly `(E[size] − 1) × baseline mean`.
- **Selection channel.** Cell- and arm-specific; many regime-matched contrasts sit near zero
  relative to their own bootstrap SE. `crypto_H1` and `crypto_H4` disagree in sign — and are not
  pooled.
- **Vol-state as a baseline filter (operator probe §15).** `HIGH − LOW` **never clears zero on
  mean or on Sharpe** at any cell's pooled level. `crypto_H1` HIGH *level* mean and Sharpe are
  both CI-positive, but the **contrast** still crosses zero. H4 points the other way. Decision-time
  HIGH vs LOW is **not a clean multi-cell selectivity filter** on this breakout.

`SPDR-024` did not rescue the surviving lever. It made the lever measurable and the lever did
not clear.

---

## 4. What stays open, and is NOT refuted

Booked here so no future chapter mistakes silence for refutation.

| Item | Status | Why it is terminal, not negative |
|---|---|---|
| **C2 — shock-MOMO** | **Terminal `NOT_RESOLVABLE`, unresolved-and-parked** | Crypto read +22.6 bps (pct 0.95, n 505). `SPDR-018B` neither replicated nor refuted it: the comparator is not a neutral yardstick (its own mean runs +0.97 EU → +12.05 Asia, Asia null entirely above zero, blind upward), the effect vanishes in EU and concentrates in Asia, and an independent rebuild flipped `P-MR` 0.067 → 0.826. **P1 was skipped by operator decision** (no `SPDR-018C`), so nothing further was run. **Never book this as a refutation.** |
| **C3** | **Terminally unpowerable in its registered form** | All 1,946 unresolved cells are already fully levered; median cell is 81× short and would need **201 years** of 25-symbol history at its own event rate; 88.3% need >20 years. Unpowerable ≠ refuted. |
| **C9, D3, D4** (`SPDR-018B`) | **OPEN, never run** | Not nulls. Never emitted. |
| **P6** — Asia magnitude × shock | **Unregistered lead** | ~+10 bps Asia vs ~0 EU. Observed, never registered, never tested. |
| Direction-agnostic structure (both-side / straddle / grid) | **Parked by operator, not refuted** | Deferred at checkpoint opening and never revisited. |

---

## 5. The SPDR-024 detection-floor defect — what happened and what it cost

The first `SPDR-024` emission returned "unresolvable" on essentially every read. The cause was
not thin data. It was a **scale mismatch between the floor and the effect**, with five inflations
compounding on top.

**Mechanism.** For a pure SIZE device the σ̂-normalised estimand is arithmetically pinned to the
baseline's **per-trade Sharpe ratio** — 0.032 to 0.059 across these four cells. The detection
floor was `MDE_Z / √n` with `MDE_Z = 2.8`. Clearing a floor beneath that ceiling requires
**2,270–7,501 independent blocks** in the best case per cell, and only **one of four cells** had
them. Three of four cells were **incapable of resolving anything before the run started**, by
arithmetic that was computable at design time and was not computed.

Four compounding defects sat on top:

1. The yardstick was built from estimates that had themselves been declared unresolved.
2. `2.8` is a **sample-size target, not a significance bar** — it was used as a test threshold
   beside a bootstrap SE the floor ignored.
3. Two channels with two different σ̂ denominators (scale uses `paired_delta`; selection uses
   `outcome_level_bps`) were read on **one shared numeric ladder**.
4. The pre-execution power gate and the post-execution ladder used **different standards**.

**Resolution.** Operator decision 2026-08-07: clean fix, artefact purge, full re-emission. The
pre-fix emission was **deleted**, not annotated — it is not readable and not recoverable. The
re-emission ran under **AMENDMENT-7 R1–R5**: detection floors share the CI's own SE family; no
result or power labels attach to a row; scale and selection denominators are declared and never
share a ladder; `MDE_Z` is context, never a pass mark. The pre-A7 analysis scripts are retained
under `analysis_code/legacy_pre_a7/` as method history only.

**Cost.** One full re-emission of four cells. **No wrong conclusion was published** — the defect
was found by the analyst before any verdict was taken, and independently validated against the
artefacts and code on 2026-08-07 before the fix was authorised.

This is the checkpoint's most transferable output and is the entire content of the chapter's
Renew phase (see `ROLLOVER.md` §Renew).

---

## 6. Why the checkpoint ends here

Both parts of the question were answered, and the answers foreclose the route:

1. The residue **was** powerable, and powered it shows the joint at break-even with **91–96% of
   the distance being cost, not rate**. There is no rate improvement to find that would matter,
   because the deficit is not a rate deficit.
2. `W/L` — the handle the whole capture branch rested on — is **not an independent quantity**.
   It is ~97% the arithmetic mirror of `p` on two unrelated universes. Moving it 36–67× moves
   the mean not at all. The capture-geometry premise was that this handle was free. It is not.
3. Every volatility-adaptive device that was supposed to move the joint either does nothing
   measurable (hold, X-03), does less than its fixed counterpart (stop, X-04), gives back more
   (trail, X-05/06), or has a consistent direction with a magnitude below its own floor after a
   purpose-built experiment was run to measure it (size, X-07 → `SPDR-024`).
4. The single most promising conditioning story — vol state as a selectivity filter — **never
   clears zero on the contrast** in any cell, on mean or on Sharpe.

The remaining live threads (§4) are not blocked by evidence. They are blocked by **data volume
that does not exist** (C3: 201 years) or by an operator decision not to spend another experiment
(C2). Neither is a research route.

---

## 7. Family disposition — operator-signed

**`CF-VOLDIR-001` → `RETIRED — CHARACTERISED, NOT TRADABLE`.**

What retirement means here, precisely:

- The family's **structure is characterised**, not merely rejected: the joint is measured at
  power on two independent universes, the mirror relation between `p` and `W/L` is quantified,
  and the cost share of the gap is bounded at 91–96%.
- Retirement is **not** a refutation of C2 or C3. Both are booked as terminal `NOT_RESOLVABLE`
  (§4) and carry that label permanently.
- **Re-opening requires a new information source** — not a new exit rule, not a new volatility
  transform, not a second pass at the same lattice. The programme has now spent checkpoints
  016, 017 and 018 on this family; three of the four levers are refuted at power and the fourth
  is below its floor after a dedicated experiment.
- The **cost precondition is the binding one**: no successor to this family may be evaluated at
  all while spread remains uncharged, because the entire measured deficit is cost.

---

## 8. Lessons (candidates for the knowledge base)

Carried into `docs/knowledge-base/lessons-and-amendments.md` as `L-56…L-61`, each with its
mechanism, and into `pitfalls-ledger.md` as `P-28…P-31`.

| # | Lesson | Source |
|---|---|---|
| L-56 | A detection floor and the effect it judges must share a scale — and for a device whose estimand is pinned to a known ratio, the ceiling is computable **at design time** | `SPDR-024` §5 |
| L-57 | A control that reproduces the real estimate **exactly** has never tested anything — assert that the control **differs** | X-09 |
| L-58 | A device that changes only *which* trades happen cannot change *what shared trades are worth*; read admission rules on the origin lens | X-02 |
| L-59 | A screen that **gates by** a state but never **labels** realised state cannot answer any question about that state | `SPDR-021/022/023` §3.3 |
| L-60 | A per-notional estimand is arithmetically blind to sizing — paired SIZE delta is exactly zero, and zero is not a null | `SPDR-021/022/023` §3.3 |
| L-61 | A pooled figure over three instruments is one instrument — dropping `XAUUSD` flips the pooled cTrader native sign | X-10 |

---

## 9. Ledger

| Quantity | Value |
|---|---|
| Counted TEST reads spent | **0** |
| Multiplicity slots spent | **0** |
| Holdout contact | **none** — sealed on both universes throughout |
| Emissions produced | 10 run-groups (`SPDR-018`, `018B`, `021`×2, `022`×2, `023`×2, `024`×4 cells) |
| HARD checks failed | **0**, across every emission |
| Families opened | 0 |
| Families retired | **1** — `CF-VOLDIR-001` |
| XENA universes opened | 0 |

Raw Nautilus emissions for this checkpoint were **purged at the chapter rollover** as
regenerable from pinned code. Analysis artefacts, self-checks, preflight and performance
records are retained in the archive.

---

## 10. Route out

The chapter closes with the family retired and no successor registered. What the next chapter
inherits:

**Established and reusable (apparatus, not candidates):**
- The corrected identity `E[net] = p·W − (1−p)·L − cost` and the `edge = p − p_be_net` framing,
  including the fact that the target is not `p > 0.5`.
- The AMENDMENT-7 floor apparatus (R1–R5) — now programme-wide, see Renew.
- The three mandatory emissions established by `SPDR-024`: realised regime label per origin and
  trade, counterfactual outcome for excluded origins, and a capital-normalised estimand.
- HARD-check **count** reconciliation by name (`L-52`), now standard.
- The cTrader second universe (INFR-021 fence) as a replication instrument — with `L-61`'s
  warning that three instruments is not a substrate.

**Binding constraints carried forward:**
- Spread is uncharged programme-wide. No money, expectancy, or tradability claim is licensed by
  rule, independent of any pending work.
- The dead levers of §3.2 must not be re-tested: vol-gated hold, vol-gated stop distance,
  vol-scaled trail, and post-stop recovery. All four are refuted at power.
- `TIME_DERANGEMENT` is removed as a control — it was vacuous, returning the identical number to
  the real estimate on 100% of rows in all six cells.

**What a re-open would require:** a genuinely new information source. Not a new exit rule, not a
new volatility transform, not a re-parameterisation of the same lattice.
