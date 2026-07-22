# INFR-018 — Design: Instrument Build & Freeze (CF-SIGAUC-001, Stage I Phases 1–3)

**Item:** INFR-018 · **Family:** CF-SIGAUC-001 · **Checkpoint:** 014 §4 · **Stage:** I (instrument building)
**Source (NORMATIVE):** `.ignore/what-next/orderflow/ohlc/SIGNAL-SIGNED.md` — Appendix B Phases 1/2/3, §2.1, §2.3, §2.5, §6.4, A5–A7.
**Predecessor:** `python/experiments/INFR-017/report.md` §8 (frozen-input contract).
**Deliverable:** a hash-pinned **instrument registry** — anchor + pooled-vs-spot-check table, the frozen A6 rule, the profile kernel with its calibration note, the §2.3 class thresholds.

**Stage-rigor rule (binding, source Appendix B).** A Stage I output is **a parameter or a validated instrument, never evidence that anything works**. Tuning here is free; each kill-gate is a hypothesis carrying full rigor. Nothing in this item may be cited as evidence that any signal pays.

---

## §0 Scope fence — what this item may and may not produce

| | |
|---|---|
| **Produces** | anchor id + IB length; A6 discriminator rule + parameters; profile kernel id + calibration displacement; §2.3 class residual thresholds; realised universe membership; one hash-pinned registry JSON |
| **Must NOT produce** | any expectancy, grade, bps figure, cost-adjusted number, hit rate, or "signal fires here" claim for any S-statement or model. **Producing one makes Stage II unattributable.** |
| **Enforcement** | every racing statistic is emitted **only as a contrast against its own matched control** (§3.4, §4.4); absolute per-anchor / per-discriminator levels are written to artifacts under `CALIBRATION_ONLY: NOT_AN_EDGE_CLAIM` and are barred from the report's headline; the registry pin stores the **winner's identity and rank order**, never its expectancy |
| **Band** | DESIGN bank for all tuning/selection; CONFIRM bank for one confirmation per gate. **TEST never read. Holdout never queried.** Stage I confirmations are **TRAIN-INTERNAL** and must be labelled as such in every artifact — they are not out-of-sample in the programme's sense (checkpoint §5, D3) |
| **Counted reads** | 0. **Slots:** 0 |

### Applicability of standard design blocks

This item runs **no strategy and books no P&L**, so several mandatory blocks are declared N/A with reason rather than silently omitted (INFR-017 precedent):

| Block | Status |
|---|---|
| Nautilus `BacktestNode` emission; `xen.adjudication` estimand; `xen.estimand_validation` gate | **N/A — no strategy, no fills, no positions, no P&L.** The price-primary rule binds *edge-generating* experiments; this item generates parameters. Any Stage II candidate built on this pin **does** run in Nautilus. Enforced by §0 scope fence: if this item ever computes a P&L object, it is out of scope and re-runs. |
| §9 CONVERSION-PIN (screen→money) | **N/A** — no dimensionless effect is converted to money here. The money floor is SPDR-007's binding first act (card §6). |
| §10 SPREAD-SCALE-ROUTING; §11 spread-as-verdict-leg | **N/A** — no tradability or SUPPORTED band is emitted. Additionally **inoperable**: `SpreadBps` is pinned UNUSABLE (INFR-017 W2) and `t1_round_trip_spread_bps` passes it through unfloored. No cost read occurs in this item. |
| §12 amendment ledger | Opens empty: **0 LOOSER / 0 TIGHTER / 0 NEUTRAL**. Any pre-measurement change appends here with direction. |
| §13 battery rules | **Applies** — see §3.4, §4.4, §6. |
| L-29/L-30/L-31 (Nautilus fill-ts, dispose, one-node-per-process) | **N/A** — no engine run. |

### Frozen inputs — verified on disk 2026-07-20, not recomputed

| Input | Hash / state | Verified |
|---|---|---|
| `INFR-017/results/seasonal_baselines.parquet` | sha256 `1b7244c87aaafe293a945a8ac03a31222c95dcc232e7fb1d835d5227fa41ed72` | ✅ matches committed manifest **and** INFR-017 report §8 (**not** the discarded `78dd7988…`) |
| `INFR-017/results/column_pins.json` | `pin_sha256 e3b9fd9b9b5851b8a9a11f9ce34cd1e0fa8e10ea1fe1b210bd0090da379e6225` | ✅ |
| `SignedBar` contract (`xen.sigbar.data_types`) + `data/catalog_sigbar/` | `sigbar-0.1.0`; round-trip exact vs staging | ✅ |
| `INFR-017/results/a8_provenance_audit.json` | Δ bit-exact, `side` = **AGGRESSOR** (unanimous, median 26.2:1) | ✅ |
| Catalog fence | manifest sha `35d3375ec5ec18b3…`; `train_end 2023-12-18`; holdout `≥ 2025-01-08` | ✅ |

**Runtime re-verification is mandatory, not optional.** Every entry point re-hashes the baselines parquet and the pin and **aborts** on mismatch (`assert_frozen_inputs()`); the pin's `config_hash` is stamped into every output record. The baselines parquet is gitignored — if absent, regenerate via `INFR-017/code/seasonal_baselines.py` and confirm the sha before use.

**May NOT rely on** (INFR-017 §8): `SpreadBps` as a spread or cost input; any flip-pair spread number outside the 20 audited symbol-days; breadth beyond the 296 TRAIN-readable / 197 DESIGN-bank-covered instruments; the CONFIRM bank during a phase's own tuning; TEST; holdout.

### Data source

Bars are read from `python/experiments/INFR-011/data/staging/bars/*.parquet` (904 files, schema `OpenTime` naive-UTC, `Open/High/Low/Close/Volume/NTrades/BuyVolume/SellVolume/MeanBuy/MeanSell/SpreadAbs/SpreadBps`), intersected with the **ADMITTED** ledger. `data/catalog_sigbar/` holds only `_validation` — the signed lane is proven, not bulk-ingested; bulk ingest is not required by this item and is not in scope.

> **Measured discrepancy to reconcile at run time (do not assume).** 200 staging files carry DESIGN-bank bars, against the pinned **197** admitted-with-DESIGN-bank-coverage. The run emits the 3-symbol delta with each symbol's reason (staged-not-admitted / corrupt) to `results/universe_reconciliation.json`. An unexplained delta is a **REVISE**, not a rounding note.

---

## §1 Mechanism statement

```
MECHANISM: This item exploits no market regularity and forecasts nothing. It calibrates the
three measuring instruments that every downstream CF-SIGAUC-001 claim is measured WITH:
(1) WHEN a session starts on a 24/7 venue — the clock that concentrates recurring
    participation, which on a venue with no bell must be SELECTED from candidates rather
    than assumed (A7);
(2) WHAT COUNTS as acceptance beyond a boundary — the single load-bearing definition that
    splits the "price left the area" event into the trap branch and the acceptance branch
    (A6), inherited unchanged by every downstream statement;
(3) HOW WELL the bar-tier proxies reconstruct the finer truth they stand in for — the
    volume-by-price kernel against trade-level ground truth (§2.1), and whether the §2.3
    signed classes land where the mechanism says they should (structural edges) rather than
    uniformly.
The P&L-bearing object is ABSENT BY CONSTRUCTION. There is no leg, no episode, no carry.
The falsifiable content is instrument adequacy, not profitability.

DERIVED:
  estimand = three calibration contrasts, each an anchor/rule/kernel's excess over its OWN
             matched control — never an absolute level (§0 scope fence)
  null     = matched-control populations native to each gate: random-offset pseudo-anchors
             (I2), deranged outcome labels (I3), seasonal-residual-matched non-event bars (I4)
  horizon  = the anchored session remainder (I2, I3); the bar and the session window (I4) —
             each taken from the source's own horizon binding (§0.2), not chosen for power
  test     = calendar-day-clustered block bootstrap on paired contrasts, reported as
             report layers with interpretation bands (L-32/INFR-016), never as gates
```

**Anti-L-13 check.** None of this machinery transfers to another family: the estimands are anchor-excess, discriminator-separation, and kernel-displacement — each defined only by *this* source document's A6/A7/§2.1/§2.3. No prior Xen evaluation stack is reused; `xen.evaluation`'s bootstrap primitives are used as tools, not as a referee.

---

## §2 Object identity declarations

```
OBJECT-IDENTITY:
  measurement object == trading object:
    N/A BY CONSTRUCTION — no trading object exists in this item. Declared explicitly rather
    than answered YES: an instrument-build item that claimed object identity would be
    smuggling in a traded object. The identity obligation transfers to SPDR-007, which is
    the first item to have one, and which inherits this pin.
  measured conditioning event == traded entry event:
    N/A — no capital is committed. The conditioning events measured here (IB break, boundary
    poke, class print) are DEFINITIONAL objects being calibrated, not entries.
  effect-splitting windows non-overlapping: YES, and code-asserted —
    - I2: IB window [anchor, anchor+L) is disjoint from the break-search window
      [anchor+L, session_end); the excursion window opens strictly AFTER the break bar closes.
    - I3: the discriminator's qualifying window is disjoint from and strictly PRECEDES the
      outcome-label window. `assert_windows_disjoint()` raises on any overlap. This is the
      item's single most leak-prone seam: a discriminator that can see one bar of its own
      outcome would win the race by construction.
    - I4: the class-detection bar is excluded from the structural-level set it is scored
      against (a bar cannot be near a level it created).
```

---

## §3 HYP-I2 — Anchor selection (source Phase 1)

**Question.** On a 24/7 venue with no opening bell, does any candidate session clock concentrate breakout structure **more than an arbitrary clock of the same shape does**?

**Gate (source):** at least one anchor shows stable breakout expectancy. **Failure ⇒ defer to the Phase-5 breadth sweep before abandoning** (card §8) — a Phase-1 failure is a *park*, not a family kill.

### 3.1 Candidates — pre-registered, k disclosed

| id | anchor instant | sessions/day | rationale (source A7) |
|---|---|---|---|
| `A-UTC0` | 00:00 UTC | 1 (24h) | daily settlement / UTC-0 convention |
| `A-FUND` | 00:00, 08:00, 16:00 UTC | 3 (8h) | Bybit funding timestamps — a *different session structure*, not an offset of `A-UTC0` |
| `A-USOPEN` | 09:30 `America/New_York` | 1 (24h) | US equity open; **DST-correct via `zoneinfo`**, never a fixed UTC offset |
| `A-EUOPEN` | 08:00 `Europe/London` | 1 (24h) | EU equity open; DST-correct via `zoneinfo` |

**IB length** `L ∈ {15, 30, 60}` minutes (source S1: "first 15–60 min"). **Race grid = 4 anchors × 3 lengths = 12 cells.**

```
MULTIPLICITY (disclosed, source §6.7 "selection across k candidates is k hypotheses"):
  k = 12 pre-registered cells. No cell is added, dropped, or re-parameterised after any
  result is seen. The winner is a SINGLE (anchor, L) pair; the full 12-row table is emitted.
  Selection is on DESIGN only; CONFIRM sees exactly one cell, once (§3.6).
```

### 3.2 Session and break construction (frozen before results)

Per (symbol, anchor, L, session):
1. **IB** = `[High.max(), Low.min()]` over bars with `OpenTime ∈ [anchor, anchor+L)`. Session requires ≥ `0.9·L` IB bars and ≥ `0.9·(session_len−L)` post-IB bars, else `INCOMPLETE` (counted, never silently dropped).
2. **Break** = the first bar in `[anchor+L, session_end)` whose **close** is strictly beyond an IB edge. Direction = that edge's side. At most one break per session (the first); later re-breaks are not events.
   > **Declared ordering dependency.** Phase 1 precedes the A6 freeze, so it cannot use A6. It uses the source's minimal price-only precursor — *first close beyond* — identically across all 12 cells. Because it is applied identically to every cell **and to every control**, it cannot favour one anchor. This is recorded in the pin as `break_rule_at_phase1: FIRST_CLOSE_BEYOND (pre-A6, provisional, race-internal only)` and it is **not** the A6 rule; A6 is HYP-I3's output.
3. **Excursion**, measured from the break bar's **close**, over `(break_bar, session_end)`, on **real prices**:
   `MFE_norm = MFE / IB_width`, `MAE_norm = MAE / IB_width` (source S2 normalises by IB width — the L-21 unit pin: the divisor object is **the same session's IB high−low in price units**, stated with every number).

### 3.3 Racing statistic — a contrast, never a level

Per session: `A = MFE_norm − MAE_norm` (dimensionless, sign-symmetric, no cost, no direction claim).
Per cell: `Ā_real` = median of `A` over admitted sessions (median, not mean — heavy-tailed excursions, L-20).

**The reported racing statistic is the paired excess** `E = Ā_real − Ā_control` (§3.4). `Ā_real` alone is never a headline and never enters the pin.

**Stability** (source: "highest AND most stable"), reported as a layer, never a gate:
- sign consistency of `E` across the 3 chronological thirds of the DESIGN bank;
- fraction of per-symbol strata with `E > 0`, with per-symbol n and MDE;
- `E`'s IQR across symbols.

### 3.4 Control — matched random-offset pseudo-anchor

```
CONTROL pseudo_anchor:
  question answered: does THIS clock concentrate breakout structure more than an ARBITRARY
    clock of identical session shape? (source §6.3: conditional minus matched unconditional
    IS the edge; card §5 P-01 mitigation)
  population: for each real anchor, 30 pseudo-anchors of the same session-structure family
    (same sessions/day, same L, same symbol-days), placed as a stratified sample of the
    feasible clock arc with a seeded random phase, each ≥ 60 min from the minutes of THE
    ANCHOR IT CONTROLS (see AMENDMENT-1). DISJOINT from signal population: a different offset yields a different IB
    window, a different IB high/low, a different break bar, and a different session partition
    — the event sets share no members by construction. What it can show that the signal
    series cannot: whether ANY clock produces the same excursion asymmetry, i.e. whether the
    asymmetry is a property of the anchor or of intraday price behaviour generally.
  bite/MDE: co-designed plant, not a fixed one. Inject a synthetic seasonal breakout effect
    of size s at the true anchor only (widen post-break drift in the break direction by
    s·IB_width) and sweep s to trace the MDE curve for E at the realised n. The declared MDE
    is read OFF THAT CURVE at the realised session count, per stratum, and published before
    the real read (§6).
  non-vacuity: the destroy moves the IB window itself, hence the location of the boundary,
    the identity of the break bar and the excursion origin — i.e. the sufficient statistic
    (the conditional excursion-asymmetry distribution), not merely its labels. A permutation
    that preserved the session partition could not referee this and is rejected.
  expected outcome if H true: E > 0 and stable in sign across thirds and symbols for ≥1 cell.
  expected outcome if H false: E ≈ 0 for all 12 cells — the clock is not load-bearing.
  disclosure: collapse fraction (Ā_control / Ā_real) reported per cell alongside E.
  destroy form: not a permutation — an independent placement of the anchor offset. The
    derangement rule (L-28) is satisfied BY CONSTRUCTION and asserted rather than assumed:
    the ≥60-minute exclusion from the controlled anchor's own minutes guarantees zero fixed
    points, and `assert_no_fixed_points()` raises if any control clock shares a minute with
    the anchor it controls.
  class: within_sample_attribution → REPORT LAYER (INFR-016). Not a hard gate.
```

**AMENDMENT-5 — the plant's UNITS are the contrast's units (QA I-13 / I-48, 2026-07-21).**
The block above states the plant as a drift of `s·IB_width`. `common.mde_curve` sweeps the
finished day-level contrast series instead, and the two scales differ by a factor of two.
`code/mde_plant_equivalence.py` measures the relation rather than assuming it (artifact:
`results/mde_plant_equivalence.json`):

- A post-break drift moves the whole post-break path, so `post_high` and `post_low` both shift
  by `s·IB_width` in the break direction. `MFE` therefore **rises** by `s·IB_width` and `MAE`
  **falls** by the same amount, and `asym = MFE/W − MAE/W` rises by **2s**, not `s`. Measured
  on the winner cell across the whole grid: max deviation from `2s` is **2.9e-12**, while the
  deviation from `s` is the full `s` itself.
- Adding a constant `u` to every real-arm session raises each day's real-arm median by exactly
  `u` and leaves the control arm untouched, so the paired day-contrast series is exactly
  `contrast + u`. Max deviation **7.1e-15**, same day set at every `u`.

**Binding resolution.** The MDE is published in **contrast units** — the units `E` itself is
measured in — so `mde` and `below_own_mde` compare like with like and no reader has to convert.
The equivalent drift plant is **half** the published floor. This is a units declaration, not a
change of bar: no floor moves, and the `s` in the block above is hereby the induced contrast
shift. Stating it the other way round would put the floor in drift units and `E` in contrast
units, which is the units seam that made EXP-025's headline wrong by 4× (L-21/L-24).
  DIRECTION: NEUTRAL (units declaration; no threshold moves)
  running count: 0 looser / 4 tighter / 3 neutral
  TIMING: post-measurement — written 2026-07-21 after the DESIGN race was read. No number in the
  race artifact changes; the pin gains an explicit units field. RATIFICATION PENDING.

One further choice is deliberate rather than forced: the sweep re-centres first
(`values − median(values) + u`). This asks *what effect size a sample with this noise structure
could detect* — a detectability floor. Sweeping `values + u` would pile `u` on top of whatever
effect the data already contains, which is not a floor.

An earlier version of this paragraph (2026-07-21, superseded) claimed the drift raises `asym`
by `s` and cited a demonstration that added the plant straight to the `mfe` column and then
checked `asym` had moved — arithmetic on an identity. Recorded rather than deleted.

### 3.5 Leak tripwire (HARD — validity)

```
TRIPWIRE future_shift (class: future_destroy — HARD):
  Recompute each session's IB BOUNDARY LEVELS from bars in the NEXT session's IB window
  (a strict forward shift of one session), holding the break-search window, the excursion
  window, AND THE NORMALISER (ib_width = this session's own IB high−low) fixed.
  vacuity check: the shift changes the boundary levels themselves, so both the break event
  set and the excursion origin change — the sufficient statistic moves. It is not label-only.
  Divisor pinned (load-bearing): if ib_width moved with the boundary, the destroyed arm would
  differ from the real arm by a units change as well as by lost causality.

  DESTROY NULL (AMENDMENT-4 / I-29): foreign absolute levels typically sit outside the local
  price range → an immediate "fake break" → mean-reversion toward the true local range → a
  large opposite-sign A_shift (smoke ≈ −6.8 even with width fixed). That is the destroy's
  non-zero null, NOT evidence of a leak and NOT "no edge".

  SURVIVAL (what freezes): the destroyed contrast still looks like the raw one —
    (a) same-sign collapse_fraction with |cf| > 0.25, OR
    (b) |day_contrast_correlation| > 0.5.
  Freeze RE-DERIVES survival from those primitives (does not trust emitter `survives` alone)
  and requires finite day_contrast_correlation (I-34).
  IF the edge SURVIVES: construction is leaking future boundary information ⇒ EMISSION
  INVALID ⇒ fix and re-run. NEVER read as "no effect".
  A large opposite-sign E_shift with low day correlation is NOT survival — freeze proceeds;
  the value of E_raw is still a report layer against its matched control.
  POSITIVE CONTROL (I-34, required): plant raw arm = next-session IB (ib_shift=1), destroy
    with ib_shift=2; the plant MUST survive under the same adjudicator or the gate is
    insensitive and freeze refuses.
  permutation-based: NO (deterministic shift).
```

Plus, code-asserted on every read path (INFR-017 defect 7b(i) — a full-file scan with no band filter shipped once and reached the holdout):
`assert_band(df, band)` raising — never warning — on any `OpenTime ≥ band_end`, `≥ holdout_start`, or `≥ confirm_start` while in a DESIGN-tuning path.

### 3.6 CONFIRM protocol (TRAIN-INTERNAL)

After the DESIGN winner is frozen and written to disk with its hash, **exactly one** cell — the winner — is re-run on the CONFIRM bank with its controls, once. Runner refuses (raises) if a CONFIRM path is invoked before `results/anchor_freeze.json` exists. Every CONFIRM number is labelled `TRAIN_INTERNAL_CONFIRMATION: not out-of-sample in the programme's sense`.

### 3.7 Mandatory per-instrument spot-check (checkpoint §4, adherence resolution 2)

Pre-declared liquid set: **BTCUSDT, ETHUSDT, SOLUSDT** (n = 3 ≤ 5). The same 12-cell race is re-run per instrument on DESIGN.

```
DIVERGENCE RULE (pre-declared, so it cannot be argued after the table is seen):
  MATERIAL divergence  := the pooled winner ranks BELOW the median of the 12 cells locally
                          on ≥ 2 of the 3 instruments, OR its local E sign is negative on
                          ≥ 2 of 3.
  → record as a SCOPE LIMIT and ESCALATE TO THE OPERATOR BEFORE FREEZING. Do not auto-freeze.
  COSMETIC divergence  := anything else → freeze pooled, publish the full table.
  This spot-check is a SENSITIVITY READ, NOT a second selection budget: the pooled winner is
  NOT replaced by a local winner under any outcome. It can only (a) confirm, or (b) trigger
  operator escalation.
```

---

## §4 HYP-I3 — Acceptance discriminator race (source Phase 2; the most-ordered item in the document)

**Question.** Does any candidate A6 operationalisation separate **trap-type** from **acceptance-type** boundary outcomes?

**Gate (source):** the winner genuinely separates the two classes. **Failure is framework falsifier #3 — stop; do not proceed to Phase 3.**

> **Who stops.** Per INFR-016/L-32 the separation read is a **report layer** with bands (§4.6); it does not auto-stop. The layer is presented and the **operator** signs the stop-or-proceed. This is the only reading consistent with both the source's kill order and the programme's retirement of auto-verdicts.

### 4.1 The event population

A **poke** = the first bar in a session whose High (Low) exceeds an IB edge by ≥ δ, where `δ ∈ {0, 0.05, 0.10} × IB_width` (source S3 "a poke ≥ δ"). Uses the **frozen HYP-I2 anchor + L**. Sessions with no poke contribute nothing. Boundary set at Phase 2 = IB edges only (VA edges and prior extremes require the profile kernel, which is not frozen until HYP-I4 — declared ordering dependency, and the reason Phase 2 precedes Phase 3 in the source).

### 4.2 Candidate discriminators — pre-registered

**One shared qualifying window of 30 minutes** for every candidate (AMENDMENT-2). Each rule reads its own condition inside that window, so the outcome window opens at the same instant for all of them. Letting each candidate set its own window would confound the race with horizon — a 30-bar rule would be scored against a *different* outcome distribution than a 1-bar rule, and part of the winner would simply be "whose horizon suited the label".

| id | rule (evaluated on the qualifying window only) | params |
|---|---|---|
| `D1` | n consecutive closes beyond the edge | n ∈ {1,2,3} |
| `D2` | one close beyond + follow-through (next bar's close extends further beyond) | — |
| `D3` | proxy-value migration: the qualifying window's volume-weighted median price migrates beyond the edge | window W ∈ {15,30} min |
| `D4` | time-outside: ≥ τ of bars in the next W minutes close beyond | τ ∈ {0.50,0.75}, W ∈ {15,30} |
| `D5–D8` | **flow-augmented twins** of D1–D4: the same price rule **AND** both residual legs (A5 — never a raw Δ number): (a) direction — `(mean delta_ratio_resid) × poke_side > 0` (same-direction vs the seasonal norm); (b) magnitude — `mean delta_abs_resid > 0` (elevated aggression vs the seasonal norm). See AMENDMENT-3. | inherit |

**Race grid = 8 families × their parameters × 3 δ values.** The exact enumerated cell list is written to `results/a6_race_grid.json` **before execution** and hashed; QA diffs the executed set against it. Adding a cell afterwards is a design amendment with a direction (§12).

> **Hard constraint check.** `D3` uses a volume-weighted **median price over bars**, which is a per-BAR aggregate. It is **not** a per-level attribution and does **not** use the §2.1 kernel (unfrozen at this phase) or per-level Δ (barred outright, card ban 2). `D5–D8` use per-**bar** Δ only.

### 4.3 Outcome labels — the ground truth being separated

Assigned from the **outcome window**, which opens strictly after the qualifying window closes (§2, code-asserted):

| label | rule (source S3 / S4 test specs) |
|---|---|
| `ACCEPTANCE` | price travels ≥ 1·IB_width further beyond the edge before returning inside the IB range |
| `TRAP` | price returns inside and touches the **opposite** IB edge before exceeding the poke extreme |
| `UNRESOLVED` | neither by session end — **reported with its rate, never dropped**, and never folded into either class |

These are labels of what happened, used solely to select a classifier. **No expectancy, cost, direction claim, or grade is emitted from them** (§0 scope fence).

### 4.4 Racing statistic + controls

**Separation** `S = P(ACCEPTANCE | rule says accept) − P(ACCEPTANCE | rule says reject)`, computed on resolved events, with the **base rate** `P(ACCEPTANCE)` reported beside it so the lift is explicitly against the matched unconditional rate (source §6.3). Uncertainty: calendar-day-clustered block bootstrap (§6). Balanced-accuracy and class-support counts are reported as secondary disclosure; `S` is primary because it is invariant to the accept/reject call rate, which differs wildly across candidates.

```
CONTROL label_derangement:
  question answered: how much separation does this rule produce when the pairing between
    rule output and outcome is destroyed but both marginals are preserved?
  population: outcomes DERANGED across poke events within calendar-day blocks. DISJOINT: the
    (rule, outcome) pairs are disjoint from the real pairs at every index. What it can show
    that the signal series cannot: the separation attributable to class imbalance and
    call-rate asymmetry alone.
  bite/MDE: plant a synthetic rule with known separation s and confirm the deranged version
    reads S ≈ 0 across s — the MDE curve for S at the realised n is published before the read.
  non-vacuity: S is a difference of conditional rates; deranging outcomes destroys exactly
    the conditional dependence S measures. Marginals are preserved, so a rule that "wins" by
    calling accept 95% of the time is not rewarded.
  expected if H true: S_real ≫ S_deranged ≈ 0. If H false: S_real ≈ S_deranged.
  disclosure: collapse fraction (S_deranged / S_real) per cell.
  destroy form: DERANGEMENT (zero fixed points), regenerated until the fixed-point count is
    exactly 0 and asserted (L-28 — VAL-008 shipped an 11.1%-fixed-point destroy).
  class: within_sample_attribution → REPORT LAYER.

TRIPWIRE outcome_path_swap (class: future_destroy — HARD) [AMENDMENT-6]:
  Replace each event's OUTCOME-window price path with the outcome path of a DERANGED other
  event (matched on session length; zero fixed points, asserted). The swapped path is what
  BOTH the labels and the DISCRIMINATOR see:
    evaluated bars = the target's own bars strictly before outcome_start
                   ⧺ the donor's outcome-window bars, re-timed onto the target's window
    labels         = computed from that same spliced path
  The qualifying window is untouched, so a rule that reads only pre-outcome bars makes
  IDENTICAL calls against outcomes that are now unrelated to them.
  must collapse the edge; expected collapse fraction ≈ 0.
  SURVIVAL := |collapse_fraction| > 0.25 with the same sign as S_raw (the I2 survival form).
  non-vacuity: S is a difference of conditional acceptance rates given the rule's call.
    Replacing the outcome path moves the labels AND — for any rule that reaches past
    qualify_end — the calls, i.e. the joint distribution at its source, not its labels.
  bite: the positive control below. A destroy nobody has seen fire is not evidence.
  coverage: events with no usable donor path are dropped and their count published; the
    spliced fraction is reported beside the collapse fraction.
  IF S SURVIVES: the qualifying window is seeing outcome information ⇒ EMISSION INVALID ⇒
    fix the windows and re-run. Never read as "the discriminator works".

POSITIVE CONTROL i3_leak_plant (required; freeze refuses without it):
  a deliberately leaky discriminator (D4, w=240, read_past_qualify=True) evaluated on the
  SAME spliced bars. It reads the donor outcome path, and the labels come from the donor
  outcome path, so its separation MUST PERSIST.
  REQUIRED OUTCOME: SURVIVES. If the plant collapses, the destroy is not reaching the bars
  the rule reads and the gate's pass on the real cell carries no information.
```

**AMENDMENT-6 — the path swap must move the bars the rule READS, not only the labels
(QA run 6, I-45; 2026-07-21).**
The block above previously specified the same destroy but the implementation recomputed
labels from the donor path while still evaluating every discriminator on the TARGET's real
bars. The consequence is the exact inverse of the gate's purpose: a leaky rule stays
correlated with the *true* outcome path while the labels come from a *different* one, so it
decorrelates and collapses just like an honest rule. Every rule collapsed, no leak could ever
survive, and the positive control — required to COLLAPSE — certified that toothlessness
instead of testing it. The vacuity note was half right: an honest rule indeed cannot survive,
but the converse it silently relied on (that a leaky one can) was false in code.
  DIRECTION: TIGHTER — the gate acquires detection power it did not have, and the probe's
    required outcome flips from collapse to survival.
  TIMING: **pre-measurement for HYP-I3** — the gate has not been run and no I3 number exists.
  running count: 0 looser / 5 tighter / 3 neutral

### 4.5 CONFIRM protocol

Identical to §3.6: winner frozen on DESIGN (`results/a6_freeze.json` + hash), then exactly one CONFIRM run of the winner, labelled TRAIN-INTERNAL. **Source Phase 2 says "race on out-of-sample power"; within this checkpoint's declared holdout adaptation (D3) that is operationalised as DESIGN-select → CONFIRM-verify, and this substitution is recorded in the pin, not implied.**

### 4.6 Interpretation bands for `S` (labels, never gates — L-32)

```
BANDS — evaluated in this order (per stratum: per-symbol, per-δ, per-third):
  UNPOWERED:      MDE is None or MDE > 0.15 at the realised n → EXCLUDED FROM NEGATIVES (B-5),
                  reported as power, never folded into a failure. Tested FIRST so an underpowered
                  cell is not labelled WASH ("measured, cannot distinguish") when the truth is
                  "not measurable at this n" (L-32 / B-5).
  SEPARATES:      S ≥ 0.15 with cluster-bootstrap ci_low > 0.05, AND |collapse fraction| ≤ 0.25
  SUGGESTIVE:     ci_low > 0 but effect or collapse fails the SEPARATES bar
  CONTRADICTED:   ci_high < 0
  WASH:           |S| < the MDE at that stratum's n  → report as "cannot distinguish", never
                  as refutation (L-11)
POOLED: disclosure-only unless cross-symbol homogeneity is demonstrated (L-03).
```
The 0.15 / 0.05 / 0.25 numbers are **band labels for the operator's read**, not machine thresholds; nothing is auto-dropped at any of them, and no candidate is hidden (retired `one_subset` behaviour, L-32).

---

## §5 HYP-I4 — Instrument validation (source Phase 3 + §6.4) — three exits, all required

### 5.1 Exit 1 — profile kernel calibration against a finer reference

**A finer reference IS obtainable**, so `SKIP-NO-REFERENCE` is **not** taken: the Bybit public trade archive is downloadable on demand (`INFR-017/code/a8_provenance_audit.py:117`), giving trade-level **volume-at-price** — the exact truth the §2.1 proxy stands in for.

| | |
|---|---|
| Reference sample | the **same 20 symbol-days** already audited at INFR-017 A8 (BTCUSDT/ETHUSDT/SOLUSDT/DOGEUSDT/XRPUSDT × 2022-09-14, 2023-01-11, 2023-06-07, 2023-11-01), re-declared here. **Two of the four days (2023-06-07, 2023-11-01) fall in the CONFIRM band** — this is disclosed and permitted because kernel calibration measures *reconstruction fidelity of a bar aggregation*, not expectancy, and consumes no selection budget. The DESIGN-only subset is reported separately so the two scopes are never quoted interchangeably (the exact defect INFR-017 QA run 3 caught). |
| Candidate kernels | `K-UNIFORM` (volume spread uniformly across `[Low, High]`); `K-BODY` (weighted to `[min(O,C), max(O,C)]`, declared split); `K-PATH` (open → extreme-against → extreme-with → close crossing counts, source §2.1) |
| Truth | trade-level volume binned on a common price grid (tick-multiple bins, per symbol) over the same window |
| Displacement metrics | (a) **POC displacement** `|POC_kernel − POC_truth|` in ticks **and** in IB-width units; (b) **VA-edge displacement** for the ~68–70% value area; (c) **total-variation distance** between the two normalised distributions |
| Winner | lowest median POC displacement on the **DESIGN-bank days only**, ties broken by TV distance. Frozen once. CONFIRM-bank days are reported separately for reproduction and must not enter the selection (I-6). |
| Recorded in pin | winner id, `winner_selected_on: DESIGN`, three-kernel displacement table (DESIGN + CONFIRM scopes separate), the sample declaration, and `calibration: PERFORMED` |

**Barred:** the kernel calibrates **volume only**. Per-level Δ is estimate-grade and barred outright (source §2.1/Part 5, card ban 2) — no signed profile is constructed, calibrated, or emitted. Asserted in code.

Also emitted per §2.1: **per-level confidence** = share of a level's volume contributed by narrow-range bars, with the artifact-candidate flag rule (`POC whose narrow-range share < 0.2 ⇒ ARTIFACT_CANDIDATE`) pinned as a definition, not applied as a filter.

### 5.2 Exit 2 — §2.3 signed classes cluster at structural edges, and warning prints behave as flagged

**Class detection** uses A5 residuals exclusively (`volume_resid`, `range_resid`, `delta_abs_resid`, `delta_ratio_resid` from the frozen baselines) — **never a raw number** (hard constraint; A5).

```
THRESHOLDS ARE DERIVED, NOT ASSERTED (L-24 F06 discipline):
  "high percentile" and "low percentile" are fixed as PERCENTILE LEVELS of each metric's
  DESIGN-bank residual distribution (high = p90, low = p10), computed per symbol and pinned
  with the realised residual VALUE per symbol so the pin is reproducible and auditable.
  A flat residual cut asserted across symbols is rejected.
```

Classes per source §2.3: `ABSORPTION`, `DRIVE` (+ `DRIVE_WARNING_PRINT`), `DRY_UP`, `BLOWOFF`, `VACUUM_RUN`.

**Located classes (clustered):** `ABSORPTION`, `BLOWOFF`, `VACUUM_RUN`. **`DRY_UP` is detected and counted but not clustered** — source §2.3 defines it by a multi-bar *trend* in effort, not by a location, so a proximity claim would test something the mechanism does not assert. `DRIVE` / `DRIVE_WARNING_PRINT` enter the warning-print locational contrast only (§5.2 below).

**Level families** scored against (all causal ≤ t−1; event bar excluded from any level it created):
- this session's IB high / IB low (with `level_created_ts` = bar that set the edge);
- prior-session POC and VA high/low from the frozen kernel;
- prior-session high / low extremes.

**Clustering test.** For each *located* class event, `d_norm` = distance from the event bar's close to the nearest structural level above, normalised by IB width.

```
CONTROL residual_matched_nonevent:
  question answered: do class events sit nearer structural levels than ordinary bars of the
    SAME seasonal-residual regime?
  population: bars from the same session, stratified to match the class's volume_resid and
    range_resid deciles, that are NOT class events. DISJOINT: non-events by construction.
    What it can show that the signal series cannot: whether proximity to structure is a
    property of the CLASS or merely of high-volume/wide-range bars generally — which is
    exactly the confound that would make the classes decorative.
  bite/MDE: plant class events at known distances from levels and sweep; publish the MDE
    curve for the location contrast at realised n before the read.
  non-vacuity: the control varies class membership while HOLDING the residual regime fixed,
    so it moves the conditioning variable under test and nothing else.
  expected if H true: class events cluster nearer (contrast < 0) for the located classes.
  expected if H false: uniform — instruments unvalidated ⇒ HYP-I4 fails ⇒ stop before Stage II.
  disclosure: collapse fraction + per-class, per-symbol strata.
  destroy form: N/A (matched sampling, not permutation).
  class: within_sample_attribution → REPORT LAYER.
```

**Warning prints "behave as flagged"** = a *locational* claim only: `DRIVE_WARNING_PRINT` events (wide directional bar whose Δ opposes its close) are tested for a **different** structural-proximity profile than coherent `DRIVE` events. Deliberately **not** tested: any forward outcome of a warning print — that is a signal read (S10's hypothesis), belongs to checkpoint-015 Phase 6, and evaluating it here would breach §0.

### 5.3 Exit 3 — baselines and regime bands finalise

| Item | Outcome |
|---|---|
| A5 seasonal baselines | **Already frozen** at INFR-017 (`1b7244c8…`). This item consumes them, re-verifies the hash, and adds the derived per-symbol residual **threshold values** (§5.2) to the pin. |
| Δ truth window | **None required** — Δ *is* truth at bar scale (source §6.4). Recorded as such. |
| **Spread regime bands (§2.5)** | **`UNAVAILABLE — NO USABLE INPUT`** (operator decision, 2026-07-20). The stored `SpreadBps` is pinned UNUSABLE (INFR-017 W2: negative in 32.4% of BTC and 39.9% of ETH TRAIN minutes; a spread is non-negative by construction); the validated flip-pair replacement exists only on 20 symbol-days and a universe-wide recompute is an INFR-011-scale data operation, out of this item's budget. **Binding downstream consequence, written into the pin:** the source's §2.5 spread regime/veto layer — stress-regime conditioning, precision-location demotion, re-normalisation marking — **is not available to Stage II**, and every later read that would have used it must state its absence. This is recorded as a scope limit, not papered over. |

---

## §6 Universe, power, and uncertainty

### 6.1 Universe rule — binding block, declared before any cell runs

```
UNIVERSE (checkpoint §6 D4; anti-survivorship binding project-wide):
  n = 20 per day.
  Re-evaluation: daily at 00:00 UTC.
  Ranking statistic: trailing-24h QUOTE turnover = Σ over the 1440 bars of
      Volume × (High+Low+Close)/3   [USDT]
    — base-asset Volume is NOT comparable across symbols (1 BTC ≠ 1 DOGE) and is rejected as
    a ranking statistic. The divisor/unit object is stated here per L-21.
  Causality: the window ending at the re-evaluation instant uses bars with
    OpenTime < 00:00 UTC of that day (≤ t−1 minute). Code-asserted.
  Eligibility at day d: ≥ 1200 of the 1440 trailing bars present AND the symbol is ADMITTED.
    Eligibility is computed POINT-IN-TIME from the trailing window — the "197" figure is an
    empirical denominator, not a pre-computed membership list, so no forward-looking coverage
    filter enters selection.
  Tie-break: lexicographic by symbol.
  Delisting: a symbol that stops trading simply fails eligibility from that day forward. No
    backfill, no exclusion of its prior days.
  Emitted: full realised daily membership to results/universe_membership.parquet, plus the
    churn rate and the count of distinct symbols ever admitted to the panel.
```

### 6.2 Power statement

```
POWER (measured on disk 2026-07-20, not estimated):
  DESIGN bank effective span: most instruments start 2022-07-15 (4-year trailing cap; 120 of
    200 staged symbols begin that month), so the realised DESIGN bank is ~229 days, not the
    nominal 610. Median DESIGN-bank depth across covered symbols: 244,194 bars ≈ 170 days.
  Expected events:
    A-UTC0 / A-USOPEN / A-EUOPEN: ~229 sessions/symbol → ~4,580 pooled symbol-sessions
    A-FUND:                       ~687 sessions/symbol → ~13,740 pooled symbol-sessions
    breaks at ~60–80% of sessions → HYP-I2 pooled n ≈ 2,700–3,700 (daily) / 8,000–11,000 (fund)
    HYP-I3 pokes ≈ HYP-I2 sessions × poke rate; resolved (non-UNRESOLVED) fraction reported
    HYP-I4 class events: sparse by construction (p90/p10 tails) — per-class counts published
      BEFORE the clustering read, and any class below its MDE floor is declared UNPOWERED
  MDE: read off the co-designed plant curves (§3.4, §4.4, §5.2) at the realised n per stratum
    and PUBLISHED BEFORE the real read. No MDE is asserted from memory.
  Strata predeclared UNPOWERED (can never be read as negatives — B-5):
    - any per-symbol stratum with < 40 admitted sessions (short-listing symbols in the panel)
    - the 3 chronological-third splits on A-USOPEN/A-EUOPEN per-symbol (~76 sessions/third)
    - any §2.3 class whose realised per-symbol count is below its published MDE floor
    - the BTC/ETH/SOL spot-check per-instrument cells (n≈229 each) — these are a SENSITIVITY
      read whose divergence rule is pre-declared (§3.7); they are not powered for selection
      and must never be reported as a negative on any anchor
```

### 6.3 Uncertainty method

**Calendar-day-clustered circular block bootstrap** on the paired contrast, via `xen.evaluation.block_bootstrap_ci` (INFR-004/L-20 hardened: effective block capped `< n`, 5-seed battery with per-seed bound spread, `block_sensitivity` ½×/1×/2× sweep, `trimmed_mean` robustness read).

**Why cluster by calendar day, not by symbol-session:** sessions on the same UTC day across 20 crypto perpetuals share a market-wide shock; treating them as independent would understate variance by roughly the cross-sectional correlation. The resampling unit is the **calendar day**, carrying all symbols' sessions for that day together. This also satisfies source §6b (episode bootstrap, not bar bootstrap).

Reported as **"the 95% interval excludes zero"**, never as a p-value (L-20).

---

## §7 Integrity vs informative split

```
HARD (block — failure means EMISSION INVALID, fix the data/code and re-run; never "no edge"):
  - future-destroy tripwires: I2 future_shift, I3 outcome_path_swap
  - band fences: DESIGN/CONFIRM/TEST/holdout asserted (raise, never warn) on every read path
  - causal ≤ t−1 on the universe ranking statistic and every discriminator input
  - window disjointness (qualifying ⟂ outcome; IB ⟂ break-search ⟂ excursion)
  - frozen-input hash re-verification at every entry point
  - no per-level Δ attribution anywhere (asserted)
  - no local accounting primitives (`check_no_local_accounting`) — trivially satisfied, no
    accounting occurs; asserted anyway so the guarantee is machine-checked

INFORMATIVE (report layers; the OPERATOR judges — L-32/INFR-016):
  every E, S, displacement, clustering contrast, collapse fraction, stability read, and the
  pooled-vs-spot-check table. No `pass` field is emitted anywhere. Nothing is machine-dropped
  between layers. Interpretation bands are LABELS. The gate verdicts on HYP-I2/I3/I4 are
  OPERATOR ACTS on these layers, not machine outputs.
```

---

## §8 Golden trace — hand-derived, for QA to diff before execution

Computed from staging data under this design's frozen rules. The developer must **not** regenerate these; QA diffs the implementation's output against them.

```
GT-1  HYP-I2 construction — BTCUSDT, A-UTC0, L=60, session 2023-01-11 (DESIGN bank)
      IB window        [2023-01-11 00:00, 01:00)  → 60 bars
      IB high / low    17479.5 / 17416.5          → IB_width = 63.0  (36.11 bps of mid)
      first close beyond IB high : 2023-01-11 01:07:00, close 17490.5   ← the break
      first close below IB low   : 2023-01-11 02:17:00, close 17413.5   (later — NOT the event)
      break side       UP; excursion origin = 17490.5; window (01:07, 24:00)
      MFE 540.50 = 8.5794 IB_width   MAE 181.00 = 2.8730 IB_width
      A = MFE_norm − MAE_norm = +5.7064          [divisor object: this session's IB high−low
                                                  in price units — L-21 unit pin]

GT-2  HYP-I2 construction — SOLUSDT, A-FUND (08:00 session), L=30, 2023-01-11 (DESIGN bank)
      session          [08:00, 16:00);  IB [08:00, 08:30) → IB high/low 16.10 / 15.98
      IB_width         0.12
      first close below IB low : 2023-01-11 08:40:00, close 15.975     ← the break (DOWN)
      first close above IB high: 2023-01-11 09:22:00                    (later — NOT the event)
      break-bar delta  −14593.7 (buy_volume − sell_volume, per-BAR, exact)
      MFE 0.6850 = 5.7083 IB_width   MAE 0.1550 = 1.2917 IB_width   A = +4.4166
      Purpose: proves the 8h funding session partition and the DOWN branch, and that the
      first break in TIME wins regardless of side.

GT-1/GT-2 STATUS: both reproduce EXACTLY from the implementation
      (`python/tests/test_sigbar_infr018.py` pins the construction on a synthetic day; the
      live reproduction on staging data is recorded in the QA trace).

GT-3  Fence + hash behaviour (negative trace — must RAISE, not warn)
      (a) any read path invoked with OpenTime ≥ 2023-03-01 while in a DESIGN-tuning path
          → raises. (b) CONFIRM path invoked before results/anchor_freeze.json exists
          → raises. (c) baselines parquet whose sha256 ≠ 1b7244c8… → raises at entry.
      (d) any attempt to construct a per-level Δ profile → raises.
```

---

## §9 Deliverable — the hash-pinned instrument registry

`results/instrument_registry.json`, self-hashed (`pin_sha256` over the content with that field excluded — INFR-017 `column_pins.json` pattern), carrying:

| Block | Content |
|---|---|
| `frozen_inputs` | baselines sha, `column_pins` sha, fence manifest sha, `sigbar` pipeline version |
| `anchor` | winner id + IB length; the full 12-cell DESIGN table (E, control level, collapse fraction, stability); the CONFIRM row labelled TRAIN-INTERNAL; **the pooled-vs-spot-check table** and the divergence classification |
| `a6_rule` | winner id + parameters; the full race table; separation layer + bands; CONFIRM row; the `break_rule_at_phase1` provisional-rule note |
| `kernel` | winner id; three-kernel displacement table; `calibration: PERFORMED` + reference-sample declaration + DESIGN/CONFIRM day split; per-level-confidence definition |
| `class_thresholds` | per-symbol residual percentile levels **and** realised values; per-class counts; clustering layer |
| `spread_regime_bands` | `UNAVAILABLE — NO USABLE INPUT` + reason + the binding downstream consequence (§5.3) |
| `universe` | the rule verbatim, realised membership hash, churn, symbol count, the 200-vs-197 reconciliation |
| `scope_limits` | survivorship caveat; ~229-day realised DESIGN span; TRAIN-internal confirmation caveat; per-symbol thinness; every UNPOWERED stratum |
| `not_evidence` | explicit statement: nothing in this pin is evidence that any signal works (Stage I) |

**Stage II is unattributable on an unfrozen instrument** — this pin, and its hash, are the deliverable.

---

## §10 Complexity budget & execution order

| | |
|---|---|
| Statistical contrasts | 3 primary (E, S, clustering) + 1 displacement calibration |
| Controls | 3 matched (report layers) + 2 future-destroy tripwires (hard) |
| Code modules | `xen.sigbar.sessions` (anchors/IB/breaks), `xen.sigbar.acceptance` (A6 candidates), `xen.sigbar.profile` (kernels), `xen.sigbar.classes` (§2.3) — 4 shared modules; runners under `INFR-018/code/` |
| Plots | ≤ 5 (anchor race, separation race, kernel displacement, class clustering, stability) |

**Execution order is strict and is the source's order.** HYP-I2 → freeze anchor → HYP-I3 → freeze A6 → HYP-I4 → pin. A gate failure **stops** the item there and the pin records how far it got. HYP-I3 inherits I2's anchor; HYP-I4's class/level work inherits both. Any result obtained out of order is unattributable and re-runs (source Appendix B).

---

## §11 Amendment ledger

AMENDMENTS 1–3 are **pre-measurement** — logged during implementation, before any gate was run
on real data. **AMENDMENTS 4, 4a, 4b and 5 are NOT**: 4 was written after smoke on real DESIGN
bars, 4a and 5 after the full DESIGN race was read, 4b after it (though before any HYP-I3
number existed). Each carries its own dated TIMING block, and this preamble no longer claims
otherwise (QA runs 5–6, I-40 / I-54 — the same blanket claim was a MAJOR finding at I-35).
AMENDMENT-5 is stated in §3.4 beside the plant it governs rather than repeated here. Each
amendment states its direction and the running count (L-23).

```
AMENDMENT-1: pseudo-anchor control respecified — exclusion scoped to the anchor under test
             (not all four candidates); count 40 → 30; placement changed from rejection
             sampling to a stratified sample of the feasible arc with a seeded random phase.
  DIRECTION: TIGHTER
  running count: 0 looser / 1 tighter / 0 neutral
  WHY (three reasons, the first two found by implementation, the third by a test):
   (a) Correctness. Excluding EVERY meaningful clock makes the control less arbitrary than a
       genuinely arbitrary clock — an arbitrary draw may land near some other meaningful time,
       and removing those draws lowers the control level and INFLATES the contrast. Scoping the
       exclusion to the controlled anchor keeps the only constraint that matters (a control
       must not be a near-copy of what it controls) and biases the contrast conservatively.
   (b) Feasibility. Under the all-candidate exclusion the 8-hourly shape had too little of its
       480-minute cycle left to place the control clocks at all.
   (c) Reliability. Rejection sampling under a mutual-spacing constraint fails unpredictably as
       the arc fills: the 8-hourly shape leaves ~361 feasible minutes, where random greedy
       packing tops out near Renyi's parking constant and cannot reliably place 30 — one seed
       succeeded and the next raised. Stratified placement always succeeds, spreads the control
       clocks maximally, and lowers the variance of the arbitrary-clock estimate.
  n = 30 remains above the L-19 floor of 25.

AMENDMENT-2: one shared 30-minute qualifying window for every A6 candidate.
  DIRECTION: NEUTRAL
  running count: 0 looser / 1 tighter / 1 neutral
  WHY: removes a confound rather than moving a bar. With per-candidate windows the outcome
       window would open at a different instant per candidate, so the race would partly measure
       horizon rather than discrimination.

AMENDMENT-3: flow-augmentation rule for D5–D8 restated (I-10).
  DIRECTION: TIGHTER
  running count: 0 looser / 2 tighter / 1 neutral
  WHAT CHANGED: design §4.2 previously said `delta_ratio_resid > 0`. That literal is wrong on
    down-pokes (it would require above-normal BUYING to qualify as same-direction sell-side
    flow). Code now requires BOTH residual legs, with the ratio residual signed by poke side:
      (a) (mean delta_ratio_resid) × poke_side > 0
      (b) mean delta_abs_resid > 0
  WHY TIGHTER: the magnitude leg is an extra condition not in the old text; the signed ratio
    leg makes the rule mean the same thing on both sides rather than silently favouring up-pokes.
    Both legs still read A5 residuals only — no raw Δ threshold.
  A5 intact: both legs residualise; the two delta baselines remain separate (|Δ| scales with V).

AMENDMENT-4: HYP-I2 future-shift tripwire adjudicates SURVIVAL, not |cf|≈0 (I-29 / I-35).
  DIRECTION: NEUTRAL
  running count: 0 looser / 2 tighter / 2 neutral
  WHAT CHANGED: §3.5 no longer requires |E_shift| ≈ 0. Freeze fails only when the destroyed
    contrast SURVIVES (same-sign material cf, or |day_contrast_correlation| > 0.5).
  WHY NEUTRAL: the destroy form's null is non-zero by construction (foreign IB → fake break →
    mean-revert). Treating |cf| > 0.25 as automatic invalidity blocked every causal run
    (false freeze refuse) without improving leak detection. Survival adjudication still
    catches a construction that keeps the same day-contrast pattern under the destroy;
    leak sensitivity is not loosened.
  TIMING (QA run 3 I-35 — operator-ratified 2026-07-20): this HARD-gate respec was written
    after smoke on real DESIGN bars showed cf ≈ −6.8 with width fixed. It is therefore a
    **post-smoke** integrity respec, not pre-measurement. Operator ratifies direction NEUTRAL
    and the sealed thresholds (|cf|>0.25 same-sign; |day_corr|>0.5). Full DESIGN under the
    rule is admissible once I-34 bite plant is present; no re-seal re-run required solely for
    I-35.

AMENDMENT-4a (I-34, implementation, same gate — not a bar move): HYP-I2 freeze re-derives
  survival from primitives; day_corr is mandatory; a positive-control leak plant (raw arm =
  ib_shift=1, destroy = ib_shift=2) must itself SURVIVE or freeze refuses as insensitive.
  DIRECTION: TIGHTER (enforcement only)
  running count: 0 looser / 3 tighter / 2 neutral
  TIMING (QA run 5 I-40 — recorded 2026-07-21, RATIFICATION PENDING): authored AFTER the full
    DESIGN race had been run and read. It is therefore **post-measurement**, not
    pre-measurement. It moves no bar: the selection rule, the survival thresholds and the
    admission rules are untouched, and the only change is that the freeze now REFUSES an
    artifact whose tripwire has never been shown to fire. No result was re-read or re-ranked
    because of it; the DESIGN race was re-run to emit the plant, and every pre-existing number
    reproduced identically.

AMENDMENT-4b (I-37, QA run 5, recorded 2026-07-21 — same enforcement, second gate): the HYP-I3
  freeze requires its positive control too. `is_i3_gate` was computed and never read, so a
  path-swap tripwire could be frozen with no sensitivity evidence at all.
  DIRECTION: TIGHTER (enforcement only)
  running count: 0 looser / 4 tighter / 2 neutral
  TIMING: post-measurement for HYP-I2, PRE-measurement for HYP-I3 — the I3 race has not been
    run. No I3 number exists to be affected.
```

**Final-gate re-derivation (L-23).** Running count: **0 LOOSER / 5 TIGHTER / 3 NEUTRAL**. No
amendment loosened leak detection; AMENDMENT-4 corrects a mis-specified null (operator-
ratified post-smoke); 4a and 4b tighten freeze enforcement with a bite plant on each gate;
5 declares the plant's units and moves no floor; 6 gives the HYP-I3 path-swap tripwire
the detection power its own text claimed and flips its probe from collapse to survival.
There is in any case no auto-qualification to price: every value read in this item is a report
layer and no machine threshold selects, drops, or hides a candidate (L-32).

The hard gates — every machine refusal in the item, since naming only some of them made the
ledger read as if the others did not block (QA runs 5–6, I-41 / I-54 / I-64):

1. the two future-destroy tripwires (HYP-I2 survival, HYP-I3 path-swap collapse with sign
   clause), each of which must also carry a positive control that fires — required
   unconditionally, not keyed on the gate's name (`freeze_and_pin._assert_tripwire`);
2. the band / holdout / frozen-hash / window assertions (`fences.assert_band`,
   `fences.assert_frozen_inputs`);
3. `_assert_full_universe` — a freeze on a smoke-scale race is refused, because smoke and full
   runs write the same filenames;
4. `sessions.assert_no_fixed_points` — a control clock sharing a minute with the anchor it
   controls raises (L-28);
5. the CONFIRM-before-freeze refusal in each runner — a CONFIRM band cannot be opened until
   the corresponding freeze file exists;
6. `fences.assert_no_per_level_delta` — per-level signed attribution raises rather than
   producing a plausible artifact;
7. `check_no_local_accounting` inside `build_registry` — the registry refuses to emit if an
   accounting primitive has appeared in the experiment directory;
8. the band check on the universe reconciliation the registry cites;
9. the §3.7 spot-check MATERIAL branch. This one is value-keyed (the pooled winner below the
   local median, or negative, on ≥2 of 3 instruments) and so is named explicitly. It does not
   adjudicate a verdict and never re-ranks: it **escalates to the operator before freezing**,
   which is what keeps it compatible with L-32 and with INFR-016's retirement of auto-deciding
   value gates;
10. `acceptance.assert_windows_disjoint` — outcome opens strictly after qualify;
11. HYP-I3 runner refuses to start without `anchor_freeze.json` (execution order);
12. `_spot_check_divergence` refuses when the spot-check table is absent;
13. `evaluate_discriminator` refuses when A5 residual columns are missing on a flow cell.

There is a 5-long TIGHTER streak (amendments 1, 3, 4a, 4b, 6). All five are enforcement or
correctness, none moves an acceptance bar, and the two most recent before 6 add positive
controls rather than thresholds — but the streak is recorded here rather than left for a
reader to count. Timing enumeration of amendments: **1–3 / 4 / 4a / 4b / 5 / 6**.
