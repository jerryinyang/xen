# Phase 013 — Substrate Revision: Anchor Move-Size Diagnostic

**Checkpoint type:** Research phase design.
**Date drafted:** 2026-06-12.
**Status:** **OPEN — G0 PASS 2026-06-12** (operator-ratified
`D0-predeclarations.md`; ATR prominence `k=1.0`, floor multiple `M=2`; all
P1–P8 frozen; registry amended, Phase 013 batch). No TRAIN/TEST/holdout row
has been read under any `/ANCHOR` definition; EXP-047 TRAIN contact
authorized behind the P8 regression-suite gate. Next: Stage-1 scoping of
EXP-047.
**Candidate family:** `CF-AVWAP-001` (continued from Phases 004–012),
exercising the registered non-baseline branch `CF-AVWAP-001/ANCHOR`.
**Follows:** `2026-06-12-012-entry-side-gross-screen` (CLOSED —
ENTRY_GROSS_FLAT; G1 mechanical, 0 TEST reads, ledger unchanged).
**Source:** the Phase 012 §1.4.2 / §10 operator pre-commitment — *"if the
gross screen is flat, the programme pivots to substrate-level revision
(Stage-C detectors `/LB` `/MB` `/ATR` `/ANCHOR` or a new candidate
family)."* Operator agreed 2026-06-12 to open the pivot with a cheap,
TRAIN-only **move-size** diagnostic that decides between an in-family
anchor revision and a full new-family pivot.

## 1. Provenance

### 1.1 The corrected diagnosis that defines this phase

Nine phases (004–012) worked one event substrate: the AVWAP **bounce**
entry. A framing correction made before this design (verified in
`python/src/xen/avwap.py:390–421`) is load-bearing and is recorded here so
the pivot does not inherit the prior mischaracterisation:

> The substrate is a **trend-continuation pullback entry**, not a
> mean-reversion fade. In a bull regime the machine *arms* when a completed
> close falls below the AVWAP (a pullback to the adverse side) and *triggers
> a long* when a later close reclaims the AVWAP **in the regime direction**.
> The trade is taken *with* the established MA(20,50) trend; the only
> mean-reversion in it is the pullback being waited for.

This reframes every prior negative result. The accumulated evidence is not
"the signal is on the wrong side" — it is the opposite:

- **Entry direction is sound.** Phase 011 trained per-instrument exits on the
  37-cell COVERED grid and found the **gross proxy positive in 31/37 cells**.
  The entry reliably sits on the correct side of the move.
- **The captured move is too small to clear cost.** Net medians were −5 to −7
  bps at every grid point of both exit families under frozen CONSERVATIVE
  costs (Phase 011, FOUNDATION_NON-TUNABLE). The lifetime the substrate
  harvests — AVWAP reclaim → 1.0-MAD band target, or cut at the next MA
  regime flip, or the FH(12) cap — is a thin slice of the trend leg the entry
  correctly enters.
- **Every in-substrate lever is exhausted.** Entry parameters (`/ALPHA`,
  `/MA-DOMAIN`) are CLOSED-MEASURED (Phase 012: gross moved 1–2 bps vs 5–20
  bps floors). Exit families E1–E5 were FLAT (Phase 010). Per-instrument exit
  training was non-tunable (Phase 011). A broker-verified cost review (Phase
  012 §1.1, IC Markets raw) confirmed the cost floor is realistic — the gap
  cannot be honestly re-marked away.

The binding inequality has not changed since Phase 007: **available
captured move < round-trip cost.** What has changed is the certainty that
no parameterisation *within the bounce vehicle on the current anchor* closes
it.

### 1.2 The structural lever this phase tests

A ratio is fixed only by raising the numerator (move) or lowering the
denominator (cost). Cost is frozen and broker-verified. Numerator tuning
inside the bounce vehicle is exhausted. The two structurally-untried levers
named by the operator pre-commitment are:

1. **`/ANCHOR`** — the registered Stage-C branch (gap #1, deferred since
   Phase 005): replace the **running-extreme** anchor (current baseline:
   lowest `Low` / highest `High` since the prior confirmed regime change)
   with a **significant-pivot** anchor (a deterministic, look-ahead-safe
   confirmed swing point). The anchor sets where the AVWAP originates, which
   sets the pullback-entry location, which sets the size of the move the
   entry sits in front of. This is the *only* registered lever that changes
   move geometry rather than reshuffling the same events.
2. **A new candidate family** — abandon AVWAP-bounce continuation entirely.
   Heavy: requires fresh readiness / calibration / parity passes (EXP-020 /
   027 / 029 analogs) for a new event definition.

### 1.3 Why a move-size diagnostic, and why first

A full new-family pivot is the expensive option; spending it on the
*assumption* that the AVWAP family is move-capped would repeat the Phase
008→011 pattern of building net machinery before the gross premise is
established. Phase 012's validated ordering — **screen the gross premise
cheaply on TRAIN before rebuilding any net/exit machinery** — applies
directly. The cheapest decisive read is the one that distinguishes the two
levers:

> Is the thin captured move a property of the **anchor placement** (fixable
> in-family via `/ANCHOR`), or **intrinsic** to MA(20,50)-regime trend legs
> at these timeframes (requires a new family)?

A gross, exit-agnostic **available-move-size distribution**, measured
identically on the current anchor and the `/ANCHOR` significant-pivot anchor,
answers exactly that. It consumes **0 slots, 0 TEST reads** and reads no
holdout — it is a TRAIN-only descriptive diagnostic, the same class as the
Phase 012 gross screen.

### 1.4 Binding constraints carried in

- **No holdout read exists for any package, ever.** All holdouts sealed
  (EURUSD contaminated-by-disclosure; Phase 009 shot spent). This phase adds
  no ledger entries (TRAIN-only by construction).
- **TEST-read ledger unchanged.** EURUSD-4h AT CAP; USTEC-4h / XAUUSD-4h at
  1; all else 0. Untouched here.
- **Cost model frozen** (Phase 011 P2, CONSERVATIVE RT + per-instrument
  financing). Read only as the reference floor; no net columns produced.
- **5m retired.** Domains: 1h, 2h, 4h.
- **A new anchor is a new event definition.** It does **not** inherit the
  EXP-043 readiness map or the EXP-044 calibration map — both are anchor-
  specific. `/ANCHOR` events are inadmissible until they pass an EXP-020-
  analog **readiness** gate (determinism, look-ahead safety, non-degeneracy,
  event floor). Full inference calibration (EXP-027 analog) and cTrader
  parity (EXP-029 analog) are **not** required for this TRAIN-only gross
  diagnostic; they become preconditions only for a future net/TEST phase.
- **Registry semantics are the authority** (Phase 011 lesson 1). `/ANCHOR`
  is a registered substrate branch; this phase exercises it as a substrate
  revision, which is in scope for the pivot (contrast Phase 012, where
  arm/trigger redefinition was explicitly out of scope and assigned here).

### 1.5 Operator decisions recorded 2026-06-12 (pre-design)

1. Open the substrate pivot with the **move-size diagnostic**, not a direct
   new-family build.
2. **Decision rule (pre-committed):** if the `/ANCHOR` available-move
   distribution remains capped near the cost floor → the move-size ceiling
   is **intrinsic to the AVWAP family** → route to a new candidate family.
   If `/ANCHOR` opens **materially larger** available moves in a composition
   of cells → route to an in-family `/ANCHOR` viability phase.
3. This phase is the diagnostic **only**. Both branches route to a *future*
   phase under its own design / D0; neither viability proof nor family
   selection is performed here.

## 2. Objective

Determine, on TRAIN data only and gross of all costs, whether replacing the
running-extreme AVWAP anchor with a significant-pivot anchor (`/ANCHOR`)
**materially shifts the available per-event favorable move-size
distribution** relative to the frozen per-cell cost floor, in enough cells
to justify an in-family viability phase — versus confirming the move-size
ceiling is intrinsic to the AVWAP family and routing to a new family.

This is one falsifiable question. It is not a viability test, a net screen,
or a family selection.

## 3. Track and gate structure

```
Tier 0 (desk, no runs)
  D0  Registry amendment (multiplicity-registry.md): Phase 013 batch.
      Freeze: the /ANCHOR significant-pivot definition (parameters);
      the readiness gate; the move-size statistic; the cost-floor
      reference; the material-shift composition threshold; the cell
      universe; the baseline-anchor reconciliation anchor.
        │
        ▼  GATE G0: predeclaration completeness — no TRAIN read before
        │  every D0 item is operator-ratified and the registry is amended.
        ▼
Track A — /ANCHOR readiness [0 slots, TRAIN-only, EXP-020 analog]
      Sub-step of EXP-047: generate /ANCHOR events on the cell universe;
      verify determinism, look-ahead safety, invariants, and the event
      floor. Cells failing readiness are excluded with record (they do not
      enter the move-size comparison).
        │
        ▼  GATE G1a: readiness — only READY cells proceed.
        ▼
Track B — Move-size distribution comparison [0 slots, TRAIN-only, diag]
      EXP-047: per READY cell, compute the gross available-move-size
      distribution for (i) the current running-extreme anchor and (ii) the
      /ANCHOR significant-pivot anchor, identically. Compare each
      distribution's location to the per-cell cost floor; classify shift.
        │
        ▼  GATE G1b: material-shift composition (mechanical).
        ▼
ANCHOR_MOVE_VIABLE ──→ future phase: /ANCHOR in-family viability
                        (readiness already passed; needs EXP-027/029
                        analogs + net training + TEST endpoint); own design/D0.
ANCHOR_MOVE_FLAT   ──→ move-size ceiling intrinsic to the AVWAP family;
                        route to a new candidate family; own design/D0.
```

- **TRAIN/TEST discipline:** TRAIN only (1-minute-row `train_end_ts`
  boundary, Phase 008 R1.3 convention). 0 TEST reads; ledger unchanged.
- One experiment (**EXP-047**, `CF-AVWAP-001/DIAG-007`), assigned at Stage-1
  scoping. Readiness and the move-size comparison are two sub-steps of one
  falsifiable question, not separate hypotheses.

## 4. Scope discipline

**In scope:** D0; the `/ANCHOR` ATR-prominence anchor definition; the
EXP-047 readiness sub-step (EXP-020 analog, new anchor) over the **full
17-instrument × {1h, 2h, 4h} universe** (EXP-043 grid; membership defined by
`/ANCHOR` readiness, not inherited from the old-anchor 37-cell map); the
EXP-047 move-size distribution comparison (current anchor vs `/ANCHOR`) on
the READY cell universe; G1 adjudication; retrospective with the routing
hand-off. The DE30 coverage truncation (broker history ends 2026-01-16,
VAL-003 disclosure) carries forward as a per-cell disclosure.

**Out of scope:** any net or cost-adjusted move-size column (gross only —
the floor is a *reference line*, never subtracted); any exit training,
selection, or portfolio machinery; any inference calibration (EXP-027
analog) or cTrader parity (EXP-029 analog) — those gate a *future* net
phase, not this one; any TEST or holdout contact; the other Stage-C
detectors (`/LB` `/MB` `/ATR`) — `/ANCHOR` is the move-geometry lever and is
tested alone (a detector that changes *when* you trade, not *what move you
sit in front of*, is a separate question for a separate phase); new-family
design (it is a *routing destination*, not work performed here); any grid
extension, threshold change, or anchor re-parameterisation after a
distribution is seen; 5m; cross-instrument pooling for per-cell verdicts.

## 5. Item specification — EXP-047 (`CF-AVWAP-001/DIAG-007`, 0 slots)

### 5.1 The `/ANCHOR` significant-pivot anchor (ATR-prominence; fixed at D0)

The baseline anchor is the **running extreme** since the prior confirmed
regime change. `/ANCHOR` replaces it with an **ATR-prominence significant
pivot**: a deterministic, streaming-safe confirmed swing low (bull regime) /
swing high (bear regime) whose **retracement prominence exceeds `k × ATR`**,
selected from completed bars only. "Prominence" is the
counter-move away from the candidate extreme that confirms it as a genuine
swing (not a running-extreme tick). The concrete rule and its parameters —
`ATR_period`, the prominence multiple `k`, the swing-confirmation convention,
a predeclared tie-break when multiple qualifying pivots exist in the segment,
and a **fallback to the running extreme** when no pivot clears `k × ATR` — are
fixed at D0. The ATR is computed on the same domain bars from completed bars
only (streaming-safe). Hard requirements:

- **Look-ahead safe:** the anchor is selectable using only bars completed at
  or before the regime-confirmation bar; no future bar may move it.
- **Deterministic:** identical input → identical anchor (replay drift 0).
- **Streaming-compatible:** a sequential state update, consistent with the
  `xen.avwap` machinery contract.
- Everything else about the substrate is **frozen** to baseline: MA(20,50)
  regime detector, typical-price source, `TickVolume**0.75` weight, 1.0-MAD
  band, arm/trigger-at-AVWAP-line event rule, pyramid handling. Only the
  anchor pivot-selection rule changes.

### 5.2 Move-size statistic (gross, exit-agnostic)

The diagnostic measures the **available favorable move**, not the move any
particular exit captures — that is the quantity the pivot is hypothesised to
enlarge. Per cell × anchor, on TRAIN events only, gross, real prices:

- **Primary — favorable excursion (MFE):** the maximum favorable
  direction-signed real-price excursion from the trigger close over the
  event lifetime (lifetime = to MA-regime trend-change or analysis-set end,
  the EXP-022 lifetime boundary; unfinished events counted and disclosed,
  not dropped silently). Reported as a distribution: median and a robust
  spread (e.g. IQR), per cell × anchor.
- **Companion — adverse excursion (MAE):** the matching maximum adverse
  excursion, so a rightward MFE shift accompanied by an equal MAE shift (no
  net geometry gain) is visible and not mistaken for a win.
- **Context — matched-control MFE:** the same MFE on matched non-event bars
  in the same instrument/domain/regime direction (EXP-021/027 matching
  convention), descriptive only, to confirm any `/ANCHOR` rightward shift is
  not merely a higher-volatility sub-period the new anchor happens to sample.

No fixed-horizon expectancy headline (Phase 012 already measured gross(H) and
found it flat) — this phase asks the *ceiling* question (how big is the
available move), which is horizon-independent and the genuinely new read.

### 5.3 Cost-floor reference (per cell)

The frozen Phase 011 P2 model supplies the **reference line** the available
move must materially exceed to be worth capturing:

> `floor_i,d = RT_i + financing_i × days(lifetime, d)`

read descriptively at the cell's typical lifetime holding time. The floor is
**never subtracted** from any move-size value; it is plotted/tabulated as a
threshold the MFE distribution is compared against. (Holding-time formula
fixed at D0, reusing the Phase 012 item-4 convention generalised to the
lifetime exit.)

### 5.4 Per-cell shift classification and G1 statistic

Per cell, comparing `/ANCHOR` vs current anchor (fixed at D0; proposed form):

- **SHIFTED_VIABLE** iff the `/ANCHOR` MFE-median exceeds the current-anchor
  MFE-median by a predeclared material margin **and** the `/ANCHOR`
  MFE-median sits a predeclared multiple above the cost floor **and** the MAE
  shift does not erase the favorable gain **and** event count ≥ 30 TRAIN
  events **and** determinism replay passes.
- **NOT_SHIFTED** otherwise.

The phase-level statistic is the composition of SHIFTED_VIABLE cells.
Proposed threshold (echoing Phase 011 P5 / Phase 012 P6): **≥5 cells over ≥3
instruments** → `ANCHOR_MOVE_VIABLE`; otherwise `ANCHOR_MOVE_FLAT`. The
exact margins and the multiple are fixed at D0, before any distribution is
seen.

## 6. Selection discipline

- All anchor parameters, statistics, margins, the floor formula, and the
  composition threshold frozen at D0 before any TRAIN read.
- The diagnostic may return **nothing** — `ANCHOR_MOVE_FLAT` is a complete,
  routable outcome (it *positively* authorises the new-family pivot), not a
  failure of the diagnostic (Phase 011 lesson 3).
- No re-ranking, anchor re-parameterisation, threshold adjustment, or cell
  re-selection after any distribution is seen. Follow-up anchors require a
  new phase.
- The report carries the full per-cell MFE/MAE-vs-floor decomposition for
  **both** anchors regardless of verdict (Phase 011 lesson 2).
- The current-anchor MFE arm is the controlled reference; its gross figures
  reconcile against the EXP-045 / EXP-046 gross proxies on shared cells as
  an integrity check (Phase 012 baseline-row convention).

## 7. Methodological guardrails

- **Unpaired-population honesty:** the two anchors generate *different* event
  populations (different counts, timing). The comparison is a distributional
  *location shift*, not a paired test; the composition rule values both a
  rightward MFE shift and changed event availability (fewer, larger events
  can still win). Stated explicitly so no reader treats it as matched.
- **Available ≠ capturable:** a larger MFE is **necessary but not
  sufficient**. `ANCHOR_MOVE_VIABLE` authorises *spending a viability phase*
  that must still prove a deterministic exit can capture the move net of
  cost — exactly as Phase 012's gross screen authorised a follow-on, never a
  claim. The diagnostic measures a ceiling, not an edge.
- **Readiness is a hard gate.** A new anchor with look-ahead leakage or
  degeneracy would manufacture a spurious MFE shift; G1a (EXP-020 analog)
  must pass per cell before that cell's move-size read is admissible.
- **Power context (EXP-043/044 figures as priors only):** baseline TRAIN
  events run 1h 151–273, 2h 86–143, 4h 32–86 per cell; `/ANCHOR` will move
  these. The ≥30 floor and determinism check guard the small end; per-cell
  MDEs (16/32/64 bps on 1h/2h/4h) mean single-cell *expectancy* differences
  of a few bps are not resolvable — which is exactly why the read is a
  distributional **shift** in available move size against a fixed floor, not
  a per-cell significance test.
- **Substrate integrity:** event generation uses the frozen `xen.avwap`
  machinery with a parameterised anchor rule; the baseline anchor must
  reproduce Phases 004–012 bit-for-bit (the Phase 011/012 regression suite
  carries forward, extended to cover the anchor parameterisation before the
  first TRAIN read).
- **No net arithmetic on move-size values** beyond the floor *comparison*; no
  net columns anywhere (prevents quiet re-introduction of exit assumptions).

## 8. Gate specifications

### 8.1 G0 — predeclaration completeness

D0 closes only when `D0-predeclarations.md` is operator-ratified: the
`/ANCHOR` ATR-prominence pivot rule + parameters `ATR_period`, `k`,
confirmation, tie-break, running-extreme fallback (item 1), the readiness
criteria (2), the MFE/MAE/matched-control statistics + lifetime boundary (3),
the holding-time + floor formula (4), the per-cell shift margins and floor
multiple (5), the composition threshold (6), the event floor (7), the cell
universe — full 17-instrument × {1h,2h,4h} grid, readiness-defined membership
(8), the regression-suite extension requirement (9). Registry amended
(Phase 013 batch) before any TRAIN read.

### 8.2 G1a — readiness (mechanical, per cell)

A cell is READY iff: 0 invariant violations, determinism replay drift 0, no
look-ahead-safety failure, and ≥30 TRAIN `/ANCHOR` events. NOT_READY cells
are excluded from Track B with record (they are not move-size evidence).

### 8.3 G1b — move-size adjudication (mechanical)

- **ANCHOR_MOVE_VIABLE:** the SHIFTED_VIABLE composition meets the threshold
  (≥5 cells over ≥3 instruments, D0 item 6). Output: the shifted cell set,
  frozen as the in-family viability phase's input.
- **ANCHOR_MOVE_FLAT:** it does not. Phase closes; the move-size ceiling is
  recorded as intrinsic to the AVWAP family on the tested anchor; programme
  routes to a new candidate family.

## 9. Phase outcome criteria

| Outcome | Condition | Consequence |
|---------|-----------|-------------|
| **ANCHOR_MOVE_VIABLE** | G1b composition met | A future phase opens an in-family `/ANCHOR` **viability** track: EXP-027/029 analogs (calibration + parity, required before any net/TEST read), per-cell net exit training, portfolio/TEST endpoint — inheriting Phase 011's validated machinery under its own D0. The move-size shift is a ceiling, not an edge. |
| **ANCHOR_MOVE_FLAT** | G1b composition not met | The thin captured move is intrinsic to AVWAP-family geometry on this anchor; the in-family lever is closed. Programme routes to a **new candidate family** — own design/D0, fresh EXP-020/027/029-analog scaffolding. |

Either way: 0 slots, 0 TEST reads, ledger unchanged, holdouts sealed.

## 10. Non-goals and hand-off

- No new-family *design* here — only the routing decision toward it. If
  `ANCHOR_MOVE_FLAT`, the new-family phase starts from the Phase 011/012
  gross decomposition (entry direction sound, move too small) and must pick a
  mechanism whose *available move geometry* is structurally larger relative
  to cost; it owns full EXP-020/027/029-analog readiness/calibration/parity.
- No `/LB` `/MB` `/ATR` work — deferred; they are regime-timing levers, not
  move-geometry levers, and entry-timing variation is already gross-flat
  (Phase 012).
- No MTF, no execution-cost work (cost model frozen and broker-verified; a
  refresh may be declared at a future D0, never retroactively).
- No exit redesign — the exit lever is exhausted on the current anchor; a new
  anchor's exit training is a *viability-phase* question, gated behind
  `ANCHOR_MOVE_VIABLE`.

## 11. Amendment log

### 2026-06-12 — initial draft (no data contact)

Drafted from the Phase 012 §1.4.2 / §10 substrate-pivot pre-commitment and
the operator's 2026-06-12 decision to open the pivot with a TRAIN-only
move-size diagnostic. Carries the corrected substrate framing
(trend-continuation pullback entry, verified `avwap.py:390–421`). D0
predeclarations to be proposed in `D0-predeclarations.md` (DRAFT); none
derives from Phase 013 data; no row has been read under any `/ANCHOR`
definition.

**Operator decisions recorded 2026-06-12 (pre-data):** (a) `/ANCHOR` rule =
**ATR-prominence significant pivot** (§5.1); (c) cell universe = **fresh
`/ANCHOR` readiness grid over the full 17-instrument × {1h,2h,4h} universe**
(§4). **Remaining choices, defaulting to inherited conventions unless the
operator overrides at G0:** (b) per-cell material-shift margin + floor
multiple — proposed 1×SE-style margin per §5.4; (d) composition threshold —
proposed ≥5 cells over ≥3 instruments (Phase 011 P5 / Phase 012 P6). The
concrete ATR-prominence parameters (`ATR_period`, `k`, confirmation,
tie-break) are proposed in `D0-predeclarations.md` for G0 ratification; none
derives from data.

### 2026-06-12 — D0 closed, G0 PASS (no data contact)

Operator ratified `D0-predeclarations.md` P1–P8. The two flagged research
choices were decided: ATR prominence multiple **`k = 1.0`** (P1, the
`/ANCHOR` significance definition) and floor headroom multiple **`M = 2`**
(P5, the SHIFTED_VIABLE gate); remaining items inherit the Phase 011/012
conventions as drafted (no value changed between draft and ratification).
Multiplicity registry amended (Phase 013 batch, 0 slots, 0 TEST reads).
EXP-047 (`CF-AVWAP-001/DIAG-007`) assigned at Stage-1 scoping. TRAIN data
contact authorized behind the P8 regression-suite gate; TEST-read ledger
untouched by construction.
