# Checkpoint 018 — Trade Opportunity Modelling / Capture Geometry

- **Opened:** 2026-07-25
- **Status:** `OPEN — SPDR-018 + SPDR-018B CLOSED; EVIDENCE INVENTORY AND THREE-EXPERIMENT STEP-3 DESIGN APPROVED 2026-07-30; IMPLEMENTATION NOT YET AUTHORISED`
- **Reflection:** `reflection-mid.md` — the confirmed evidence through SPDR-018B, each observation
  with its evidence class and the adaptive-management decision it may inform. It selects **no** next
  experiment and **no** universal outcome measure.
- **Family:** `CF-VOLDIR-001` (`REGISTERED`) — **extension** of checkpoint-017, not a new family
- **Governing SoT (substance precedence):** `.ignore/what-next/alts/opportunity.md`
  This design **translates** that brief 1-to-1; it does not replace or thin it.
- **Predecessor:** `checkpoints/2026-07-23-017-structural-vol-direction-programme/` —
  **CLOSED 2026-07-25** (`retrospective.md`)
- **Container:** `SPDR-018` → approved evidence inventory → `SPDR-021/022/023`
  characterisation → operator interpretation → conditional `XENA-VOLDIR-001`
- **Authority:** family REGISTERED; SoT operator-signed 2026-07-25. Registration does **not**
  authorise execution. No XENA / TEST / holdout without operator gates.

```
SPREAD-COST-DISCLOSURE
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: every money figure understates true cost; reported net is overstated
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

## Why this checkpoint exists

Checkpoint-017 delivered its diagnostic product and closed with the extraction question
**unresolved at power**, not refuted: SPDR-014 produced 0 powered cells of 927 (MDE 20 / 172 / 796
bps against a ≤10 bps floor) while leaving three coherent, unpowered direction leads on the table.
Its powered positives — a reliable range-based volatility level, a forecastable next-swing
magnitude, a multi-bar volatility-state gate — are real but are **magnitude** objects with no signed
term attached.

This checkpoint first **resolves that residue at power** — every 017 open question, in its original
statement — and then asks whether capture geometry can convert whatever `(p, W, L)` picture emerges.
It is a **specialised expansion** of checkpoint-017's findings, not a re-litigation of them.

---

## 1. Governing sources and precedence

1. `.ignore/what-next/alts/opportunity.md` — **SoT for this checkpoint** (substance must not change).
2. `docs/references/chapter-06-governance.md` — live gate and permission boundary.
3. `docs/signal-registry/candidate-families/cf-voldir-001.md` — registered family contract.
4. `docs/references/spdr-lane.md` — SPDR integrity (TRAIN-only, disposition-only, matched controls).
5. This checkpoint — sequence, IDs, ownership, stop conditions, frozen defaults.

On conflict: SoT substance > this design's procedural freeze > per-SPDR design narrowings. Per-SPDR
designs may **narrow** arms and horizons; they may not reintroduce refused objects (§7).

Checkpoint-017's RAW brief and O3 sequence brief remain valid **for checkpoint-017**; they do not
govern here.

---

## 2. Binding premise (SoT §1)

> **Unconditional direction is dead. Conditional direction is unpowered, not refuted. Volatility is
> a multiplier on a direction term, never a substitute for it.**

**Why the stronger claim was rejected.** On a driftless signed path with a fixed-horizon exit,
`E[r_h] = 0` exactly, which forces `p·W = (1−p)·L`. No exit, hold, or sizing rule breaks that
equality; it only trades `p` against `W/L` along the zero line. Xen booked this analytically
(`CF-VOLHARV-001/HYP-001`) and empirically (SPDR-013 `time` arm: avail +441 ≈ |damage| −457,
`p_right` 0.468).

**What this gates — and what it does not** (SoT §1.1):

- **Gates:** opening any capture experiment as an **edge search**.
- **Does NOT gate:** the checkpoint, the exploration, or the magnitude work. A powered result
  below break-even **routes** (end-state 3), it does not terminate. `SPDR-018` is a **powering
  experiment**; being an input to the capture-axis decision is a consequence of that job, not its
  definition.

---

## 3. The opportunity identity (binding organising object — SoT §2)

```
E[gross per leg] = p · W − (1 − p) · L
E[net   per leg] = p · W − (1 − p) · L − cost

  p = P(r_h > 0 | state)   W = E[r_h | r_h > 0]   L = E[−r_h | r_h < 0]
  p_be_net = (L + cost) / (W + L)          edge = p − p_be_net
```

Exact by the definition of conditional expectation. A rate × magnitude form is not a substitute:
`(2p − 1) × E[|move|]` equals this only when `W = L`, and a capture ratio may not multiply a
magnitude that is already realised (SoT §2.1).

**Two consequences for the research target:**

- The target is **not** "is `p > 0.5`" — it is "is `p` above its own `p_be_net`", which can be
  satisfied at `p < 0.5` whenever `W > L`.
- **`W/L` is a real, measurable, currently-unclaimed degree of freedom** — and payoff asymmetry is
  exactly what exits, targets, stops and holds move, so it is the natural handle for the capture
  branch, and must be measured per cell before 019/020 are designed.

| Axis | Object | Status | Owner |
|---|---|---|---|
| **A. `p`** | conditional rate, per state | **UNPOWERED** across the 017 residue | `SPDR-018` |
| **B. `W`, `L`, `W/L`** | win size, loss size, payoff asymmetry | **NEVER MEASURED** | `SPDR-018` |
| **C. `E[\|move\|]`** | the scale that sets `W` and `L`: vol level (IC 0.34); T-GT-CUR (+0.21, 21/21); R-MARKOV k=4/12 | **PROVEN** | fold in by amendment |
| **D. capture** | exits, targets, holds, trailing, sizing — the levers that move `W/L` against `p` | measured, not optimised | **unregistered — no vehicle** |
| **E. `cost`** | spread never charged (2026-07-23) | **standing exclusion + caveat; not an open item** | infra |

κ is a **diagnostic**, never a multiplicative term: "what fraction of the best available point the
policy retained", labelled non-tradable.

---

## 4. Fixed question (checkpoint)

> For every question checkpoint-017 left UNPOWERED or INCONCLUSIVE, measured in its **original
> statement**: can it be resolved to its own target precision on this data — and if so, what is
> the answer? Then, given whatever `(p, W, L)` picture emerges, can opportunity-modulated capture
> geometry convert it into expectancy that clears the partial-cost floor?

```text
MECHANISM:
  Two stages. Stage 1 is a PRECISION experiment, not a mechanism experiment: the 017 residue is
  sample-limited rather than effect-limited, and each arm inherits its parent screen's mechanism,
  object and estimand verbatim - only the data behind each estimate changes. Stage 2 is
  extraction: the signed direction rule stays fixed; predeclared volatility adaptation may change
  the strategy's intrinsic event/order geometry and its post-entry capture without tuning direction.
DERIVED:
  estimands = each parent's estimand verbatim, PLUS a uniform (p, W, L, W_L, p_be_net, edge)
              decomposition on every cell carrying a signed return
  null      = each parent's own registered controls re-run at the new n, plus a magnitude-matched
              comparator for magnitude-defined conditioners (SoT §9 M-3)
  horizon   = each parent's frozen horizons; no new horizon is introduced
  test      = block-bootstrap CIs and dependence-matched MDE (SoT §9 M-1) on every cell; the primary
              read is "resolved / not resolvable on this data"
OBJECT-IDENTITY:
  SPDR-018 measurement object == each parent's object, unchanged. No estimand substitution,
    no un-nesting a conditioner out of its event. Parent parity is asserted in code.
  Any Step-3 measurement object == the extraction object frozen at the mid reflection;
    no silent object switch between screen and strategy
```

---

## 5. Sequence

### Step 1 — `SPDR-018` — power the complete 017 residue

**Not** a direction experiment and **not** a gate design. Four arms, each reusing its parent
screen's `screen_code/`, each item in its **original statement**, no omissions:

| Arm | Parent | Residue covered |
|---|---|---|
| **A** | SPDR-012 | V-REGIME-HMM (76/83 unpowered); V-TAIL at D1; the DESIGN-band date deficit across V-LEVEL / V-REGIME / V-XS; V-CLOCK D1; §6.4 clause unsatisfiability + calendar-thirds vacuity |
| **B** | SPDR-013 | `stop`/`trail`/`time` arms; the **125 positive-mean cells that are every one unpowered**; ZZ structural leg per symbol; M15 arms. **Where `W` and `L` get measured on real episodes** |
| **C** | SPDR-014 | the residual object itself (**0 of 927 powered**); shock-MOMO; ordered `last_k` L→H and the `LHL` mirror; E-TOUCH/E-CLOSE asymmetry — **all in the original event-nested form**; magnitude scaling; z/h dose; DESIGN→CONFIRM sign flip; pooled rate lean; **`DA-STRADDLE` as characterisation only** |
| **D** | SPDR-015 | transition counts (`n_trans` < 50); run-length MAE; T-GT-MED10 and the failing MED5 cells; 2a H4 k=1; R-HMM-RV; D1 stickiness; **the CONFIRM verify slice SPDR-015 never scored** |

**Only authorised drop: `SPDR-017`** — closed NOT_WORTH on mechanism grounds (model IC ≈ 0, DERIVED
layer inert, three destroys indistinguishable). Powering an absent mechanism buys nothing.

**Operator directives shaping it:**

- **Multiplicity is disclosed, not rationed.** These are follow-up confirmations of registered
  open questions, not new candidate mining.
- **Original statement, no estimand substitution.** Legitimate levers only: pool with
  σ̂-normalisation, use the full TRAIN span where the parent permits, score CONFIRM explicitly,
  report effective (not nominal) coverage. A cell that still misses its target is reported
  **`NOT_RESOLVABLE`** with the shortfall quantified — a valid answer to an open question.
- **Data roles are exclusive.** Crypto pooled = the powered estimate; cTrader = an independent
  replication read, scored separately, **never pooled into `n`** (different vol scale, session
  structure, funding, cost basis; and a different fence — `train_end` 2023-11-22 — makes a shared
  DESIGN/CONFIRM split impossible).
- **Parent parity is asserted in code:** each arm must reproduce its parent's published cells on
  the parent's own band. That is the proof the object was not silently re-specified.

**Standing design rules (SoT §9), binding:** report the **block** MDE not the iid form;
co-report the exact-span subset (`h` is an index offset, not wall-clock); give magnitude-defined
conditioners a magnitude-matched comparator; use effective multi-symbol coverage; treat collapse
fraction as disclosure-only near a zero mean.

### Step 2 — mid-checkpoint reflection

Reads the full `(p, W, L)` picture across all four arms and decides what Step 3 should be —
**including the possibility that the interesting handle is `W/L` rather than `p`**. It also books
each 017 open question as resolved, or as `NOT_RESOLVABLE` on this data.

- Some cell clears `p_be_net` (via the rate, via payoff asymmetry, or their joint) → freeze the
  extraction object and open Step 3.
- No cell clears it, but the residue is now **powered** → the honest read is that the *signed*
  branch is closed; the magnitude results still parameterise capture work, and end-state 1 or 3
  is taken at the retrospective, not here.
- A powered result **opposite** to registration → end-state 3: it **routes** to a counter-design
  under new registration. **It does not terminate the checkpoint.**

**This reflection does not close the checkpoint on a null rate.** Operator-facing written options
+ recorded decision. Artifact: `reflection-mid.md` in this checkpoint directory (created when the
reflection runs, not at open).

### Step 3 — adaptive opportunity management

**DESIGN APPROVED 2026-07-30; implementation and execution not yet authorised.** The binding
programme design is `adaptive-management-design.md`:

- `SPDR-021`: fixed candlestick-breakout benchmark;
- `SPDR-022`: MOMO after `E-TOUCH` / `E-CLOSE`;
- `SPDR-023`: MR after `E-TOUCH` / `E-CLOSE`.

All three run independently. Each reports its fixed strategy, every applicable volatility component
against the strategy's native parameters in both direct and reverse orientations, and every
applicable external management device individually. Only predeclared native-native and
management-device combinations are allowed; the two grids are not crossed. Outcomes are
origin-/device-native; all strata are visible; power is informative; no per-experiment verdict is
issued. NautilusTrader is required for native order and competing-exit semantics. The family-level
interpretation occurs only after all three analyses.

### Step 4 — XENA (conditional)

`XENA-VOLDIR-001` only if Step 3 graduates a cost-surviving base under separate authority.
Unchanged from checkpoint-017; still **RESERVED**.

---

## 6. Research items and sequence

| Order | Item | Purpose | Start gate | Status |
|---:|---|---|---|---|
| 1 | Checkpoint open + SoT freeze | Register 018; freeze identity, axes, lead list | Operator accept SoT | **COMPLETE 2026-07-25** |
| 2 | `SPDR-018` design | Freeze the four arms, the residue inventory, the uniform `(p,W,L)` layer, power targets, controls | Checkpoint open | **COMPLETE 2026-07-25** — `python/experiments/SPDR-018/design.md` |
| 3 | `SPDR-018` run + analysis | Resolve the complete 017 residue | design + execution authority | **COMPLETE / CLOSED 2026-07-26** — `HYP-D5` **SUPPORTED**; 1,413 powered signed cells vs SPDR-014's 0/927; 18 HARD checks; **0 of 1,413 clear `p_be_net`**; `W/L` 96.7% mirror-determined. No gating verdict (§2). `python/experiments/SPDR-018/report.md` |
| 3b | `SPDR-018B` run + analysis *(added; the cTrader leg SPDR-018 narrowed by defect)* | Replicate the residue on an independent asset class | design + execution authority | **COMPLETE / CLOSED 2026-07-26** — `HYP-D5` **PARTIALLY SUPPORTED**; structure replicates more tightly (mirror R² **0.9746**), **0 of 315 clear `p_be_net`**; **C2 neither replicated nor refuted**. `python/experiments/SPDR-018B/report.md` |
| 4 | Mid-checkpoint reflection | Book each 017 question resolved / NOT_RESOLVABLE; inventory the confirmed evidence and what it licenses | SPDR-018 analysis | **APPROVED 2026-07-30.** Evidence only. `reflection-mid.md` |
| 5 | ~~Spread pin~~ (infra) | Spread cost | operator | **RETIRED AS AN ITEM 2026-07-23** — spread is never charged programme-wide (`evaluation-framework.md` §Chapter-04): no quote data on the T1 lane, fixed proxies refused in code. Nothing is scheduled or awaited. The consequence is permanent, not pending: reported net is overstated, the caveat travels on every record, and AMENDMENT-C2 refuses every money, expectancy, tradability and graduation claim |
| 6 | Step-3 design (adaptive opportunity management) | Incremental effect of volatility-adaptive vs fixed native parameters and external management, per component | operator approval of item 4 | **APPROVED 2026-07-30; NATIVE-ARM AMENDMENT APPROVED.** `adaptive-management-design.md`; `SPDR-021/022/023` |
| 7 | Step-3 implementation + run + analysis | Three independent Nautilus SPDR characterisations | approved implementation plan + execution authority | **NOT YET AUTHORISED** |
| 8 | Operator gate D | Graduate base / terminal diagnosis | Step 3 | unauthorised |
| 9 | `XENA-VOLDIR-001` | Portfolio/search on graduated bases | D graduates + separate design/QA/approval | **RESERVED** |

No historical TEST. No holdout. No automatic family verdict.

---

## 7. Refusals

Inherited from chapter-06 governance:

- Range-break as primary direction device without new evidence
- Win-rate as a primary direction metric
- Unbounded indicator / ML zoo without frozen arms
- TEST / holdout contact
- Automatic family open/retire from experiment code (retrospective only)
- Deployable / fully cost-complete claims under no-spread accounting

New for this checkpoint:

- **Any expectancy claim from exits, holds, or sizing on a joint `(p, W, L)` that does not clear
  `p_be_net` at power** — the `E[gross]=0` kill; refused by construction.
- **Any rule, band, or gate phrased against `p > 0.5`** — the break-even is `p_be_net` (§3): an
  edge can exist at `p < 0.5` whenever `W > L`.
- **A blended opportunity score reported without its term-level decomposition.**
- **Researching direction prediction** — new entry models, trend filters, SMA/ZigZag sign
  variants, or tuning any entry parameter to improve `p`. Direction/event logic stays fixed; only
  the approved direct/reverse native-geometry arms may vary threshold, expiry, `z` or `H`.
  Direction is **measured, not targeted**.
- **Pure direction-agnostic *strategy* branches** (both-side, straddle-class, grid-class) while the
  SoT §0 scope constraint stands. SPDR-013's ambient-harvest line is **parked, not pursued**.
  *Exception (operator, 2026-07-25):* SPDR-014's `DA-STRADDLE` is powered in `SPDR-018` as
  **characterisation only** — a measured payoff cell, never a strategy branch.
- **Sizing reported as improving expectancy** — sizing changes variance, not mean.
- **Narrowing the `SPDR-018` residue inventory.** Every 017 UNPOWERED / INCONCLUSIVE item is in
  scope in its original statement; the only authorised drop is `SPDR-017`.

---

## 8. Frozen data scope (defaults)

| Item | Decision |
|---|---|
| Primary catalog | Bybit USDT linear perps, `data/catalog/`, INFR-011 fence |
| Universe | Top 25 by 30d USD volume (AMENDMENT-U1); pin `cf-voldir-001-universe.json` |
| Replication catalog | `data/catalog_ctrader/` (EURUSD, XAUUSD, USTEC); fence `python/experiments/INFR-021/artifacts/fence-manifest.json`, sha256 `4cdc7b01dd47200710d0d961639d55d52e1129ca89096e841eafd816b6061de0` |
| cTrader role | **Replication only** — never pooled into the powered estimate |
| cTrader holdout | **2024-12-13 onward — never queried** |
| Bybit TRAIN | All screens; code-asserted fence; DESIGN primary, CONFIRM verify |
| Historical TEST | **Never** |
| Global holdout | **Never** |
| Costs | Fees + discrete funding + allowance = ~13.5 bps; **spread null / not charged**; partial-cost caveat mandatory |
| Horizons | `h ∈ {4, 12, 24}` bars; H1 primary; frozen per SPDR design |

---

## 9. Intended checkpoint end-states (exactly one, taken at the retrospective — never by code, and never by `SPDR-018` alone)

1. **Terminal capture-geometry package.** The 017 residue is powered and **no cell clears
   `p_be_net`** at any horizon on either band, and the `W/L` handle does not move it — the identity
   has no positive term. Volatility is recorded as a reliable **descriptive** object with no
   extractable signed edge at this cost floor.
2. **Graduated base.** Some cell clears `p_be_net` — via the rate, via payoff asymmetry, or via
   their joint — and capture work converts it under partial cost. Only then does
   `XENA-VOLDIR-001` become discussable under separate authority.
3. **A powered counter-outcome that routes.** A powered result *opposite* to registration (a
   reversal where continuation was expected, or a `W/L` handle where a rate was expected) opens a
   counter-design under new registration. **This is a finding, not a null** — SoT §7's exploration
   guardrail is binding here.

---

## 10. Registration and ID assignment

| Object | ID | Hypothesis |
|---|---|---|
| Checkpoint | `2026-07-25-018-trade-opportunity-capture-geometry` | — |
| Powering sweep over the full 017 residue | `SPDR-018` | `CF-VOLDIR-001/HYP-D5` |
| Breakout adaptive-management characterisation | `SPDR-021` | `CF-VOLDIR-001/HYP-D8` |
| MOMO adaptive-management characterisation | `SPDR-022` | `CF-VOLDIR-001/HYP-D9` |
| MR adaptive-management characterisation | `SPDR-023` | `CF-VOLDIR-001/HYP-D10` |
| Conditional XENA | `XENA-VOLDIR-001` | `CF-VOLDIR-001/HYP-E` (unchanged) |

`SPDR-016` was closed **SUPERSEDED / NEVER RUN** at the checkpoint-017 retrospective; its intent is
preserved verbatim as `SPDR-018`'s declared lead list. **Runs require operator execution authority.**
The two capture-axis IDs registered on 2026-07-25 were **withdrawn and permanently voided on
2026-07-30** and are not reused. Their replacements were registered only after the evidence
inventory and replacement design were approved. Registration does not authorise implementation or
execution.

---

## 11. Pointers

| Resource | Role |
|---|---|
| `.ignore/what-next/alts/opportunity.md` | **SoT — substance precedence** |
| `adaptive-management-design.md` | Approved common contract for SPDR-021/022/023 |
| `checkpoints/2026-07-23-017-structural-vol-direction-programme/retrospective.md` | Closure of the evidence base |
| `docs/references/chapter-06-governance.md` | Live gate |
| `docs/signal-registry/candidate-families/cf-voldir-001.md` | Family contract |
| `docs/references/spdr-lane.md` | SPDR vehicle integrity boundary |
| `python/experiments/SPDR-014/report.md` | The three leads, with magnitudes and n |
| `python/experiments/SPDR-015/report.md` | The proven conditioner hand-off |
| `python/experiments/INFR-021/report.md` | cTrader catalog + fence |
