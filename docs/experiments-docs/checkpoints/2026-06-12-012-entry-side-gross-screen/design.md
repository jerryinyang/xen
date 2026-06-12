# Phase 012 — Entry-Side Gross Screen

**Checkpoint type:** Research phase design.
**Date drafted:** 2026-06-12.
**Status:** **CLOSED 2026-06-12 — ENTRY_GROSS_FLAT** (G1 adjudicated in
[G1-gate-review.md](G1-gate-review.md): no non-baseline variant meets the
P6 composition threshold — best 3 cells vs ≥5/≥3; EXP-046 audit PASS,
post-experiment governance APPROVE; 0 TEST reads, ledger unchanged.
Programme pivots to substrate revision per §1.4.2. Retrospective:
[retrospective.md](retrospective.md).) Phase history: **G0 PASS
2026-06-12** (operator-ratified `D0-predeclarations.md`; all items frozen;
registry amended); Track A (EXP-046) TRAIN contact authorized behind the
P8 regression-suite gate.
**Candidate family:** `CF-AVWAP-001` (continued from Phases 004–011).
**Follows:** `2026-06-11-011-per-instrument-foundation` (CLOSED —
FOUNDATION_NON-TUNABLE; G2 FAIL, 0/37 membership; 0 of ≤6 TEST reads spent).
**Source:** operator §9 routing decision, 2026-06-12 — Route 1 (entry-side
exploration) chosen over substrate revision and execution-cost work, with the
explicit fallback: **if the gross screen is flat, the programme pivots to
substrate-level revision** (Stage-C detectors `/LB` `/MB` `/ATR` `/ANCHOR`
or a new candidate family).

## 1. Provenance

### 1.1 The Phase 011 result that defines this phase

Phase 011 gave the AVWAP baseline entry its fair fight on the exit side:
per-instrument×domain exit training (two families × 8-point grids) on the
37-cell COVERED grid. Result: **0/37 portfolio members** — but with the
decisive decomposition (retrospective §3):

- **Gross proxy positive in 31/37 cells.** The few-bps gross bounce edge is
  real and survives training.
- **Net medians −5 to −7 bps at every grid point of both exit families.**
  Frozen CONSERVATIVE costs consume the gross edge in full.
- **Exit training reallocates gross edge; it cannot raise it.** The exit
  lever is measured and exhausted on this substrate.

The binding inequality is `gross edge > cost floor`, and the untried levers
on the gross side are the entry parameters — MA(20,50), tick-volume exponent
0.75 — placeholders frozen since the brainstorming document, deliberately
deferred in every phase since 004 (`/ALPHA`, `/MA-DOMAIN` registered, never
swept). A 2026-06-12 broker-pricing review (IC Markets raw-account
comparison) confirmed the frozen cost model is realistic-to-conservative,
not exorbitant: the gap cannot honestly be closed by re-marking costs.

### 1.2 The question, sharpened

Phase 011 retrospective §8.2: *"If entry-side is chosen: the first question
is whether any entry variant raises **gross** per-event edge materially
above the P2 cost floor on TRAIN — a gross-side screen, cheap, before any
net machinery is rebuilt."* This phase is exactly that screen and nothing
else. No exit training, no portfolio construction, no TEST contact.

### 1.3 Binding constraints carried in

- **No holdout read exists for any package, ever.** All holdouts sealed
  (EURUSD contaminated-by-disclosure; Phase 009 shot spent).
- **TEST-read ledger unchanged by Phase 011:** EURUSD-4h AT CAP (2 counted
  reads); USTEC-4h and XAUUSD-4h at 1 each; all other strata at 0. This
  phase adds **no** ledger entries (TRAIN-only).
- **Cost model frozen** (P2, Phase 011): CONSERVATIVE RT + per-instrument
  financing; no post-result iteration. This phase reads it only as the
  reference floor — gross returns are never net-adjusted here.
- **5m retired** from primary strategy use. Domains: 1h, 2h, 4h.
- **Cell universe:** the Phase 011 37-cell COVERED grid (EXP-043 readiness +
  EXP-044 calibration maps carry forward). Excluded cells (JP225-2h + 13
  NOT_COVERED) stay excluded; re-entry requires a new readiness/calibration
  pass.
- **Registry semantics are the authority** (Phase 011 lesson 1). Verified
  before drafting: `/ALPHA` (tick-volume exponent) and `/MA-DOMAIN` (trend
  detector parameters) are genuine **entry/substrate parameters** — they
  change the anchor placement and event population. The band multiplier is
  not an entry lever and does not appear in this phase.

### 1.4 Operator decisions recorded 2026-06-12 (pre-design)

1. §9 routing: **Route 1 — entry-side exploration**, opened in its cheapest
   form (TRAIN-only gross screen).
2. **Pre-committed fallback:** if the screen returns ENTRY_GROSS_FLAT, the
   programme pivots to substrate-level revision — no second entry-parameter
   phase on this substrate.
3. Structural entry redefinitions (`/ENTRY`-class arm/trigger changes) are
   **out of scope** — the A0 framing error showed entry-mechanism
   redefinition is substrate revision in disguise and belongs to the pivot
   branch, not to a parameter sweep.

## 2. Objective

Determine, on TRAIN data only, whether any predeclared entry-parameter
variant of the AVWAP bounce substrate (`/ALPHA` × `/MA-DOMAIN`,
one-at-a-time around the frozen baseline) raises **gross per-event
expectancy** materially above the frozen per-cell cost floor in enough
cells to justify rebuilding the net/exit machinery in a follow-on phase.

## 3. Track and gate structure

```
Tier 0 (desk, no runs)
  D0  Registry amendment (multiplicity-registry.md): Phase 012 batch;
      variant grids, gross statistic, cost-floor formula, clearance and
      composition thresholds fixed (§8.5 / D0-predeclarations.md).
        │
        ▼  GATE G0 (§8.1): predeclaration completeness — no TRAIN read
        │  before every D0 item is frozen.
        ▼
Track A — Entry-variant gross screen [0 slots, TRAIN-only, diag]
      EXP-046: for each variant v (7 incl. baseline) × each of the 37
      cells: generate events on TRAIN, verify determinism + event floor,
      compute gross per-event expectancy at the reference horizons,
      compare to the per-cell cost floor with the predeclared margin.
        │
        ▼  GATE G1 (§8.2): clearance count vs composition threshold.
        ▼
ENTRY_GROSS_VIABLE ──→ follow-on phase (013): exit training + portfolio
                        machinery on the winning variant(s); own design/D0.
ENTRY_GROSS_FLAT  ──→ pivot to substrate revision (operator pre-decision
                        §1.4.2); this design's §10 records the hand-off.
```

- **TRAIN/TEST discipline:** TRAIN only (R1.3 1-minute-row `train_end_ts`
  boundary; TEST and holdout untouched). 0 TEST reads; ledger unchanged.
- The screen is one experiment (EXP-046, assigned at Stage-1 scoping). One
  falsifiable question; the per-variant work is a parameter grid, not
  separate hypotheses.

## 4. Scope discipline

**In scope:** D0; EXP-046 gross screen on the 37-cell grid × 7 variants (incl. baseline);
G1 adjudication; retrospective with the routing hand-off.

**Out of scope:** any exit training or selection; any net/portfolio
machinery; any TEST or holdout contact; structural entry redefinition
(`/ENTRY` arm/trigger changes — pivot branch material); full `/ALPHA` ×
`/MA-DOMAIN` cross-grid or any variant combination (a follow-on may scope a
single combined variant under its own D0); grid extension after curves are
seen; cost-model iteration; 5m; the 14 excluded cells; cross-instrument
pooling for per-cell clearance verdicts.

## 5. Item specification — EXP-046 (Track A, 0 slots)

### 5.1 Variant set (one-at-a-time around baseline; 7 total)

| Axis | Registry branch | Values | Baseline |
| --- | --- | --- | --- |
| Tick-volume exponent α | `/ALPHA` | {0.0, 0.375, 0.75, 1.0} | 0.75 |
| MA pair (fast, slow) | `/MA-DOMAIN` | {(10,25), (20,50), (40,100), (60,150)} | (20,50) |

One-at-a-time: each non-baseline value of one axis runs with the other axis
at baseline → 3 + 3 + 1 baseline = **7 distinct variants including baseline**
(α=0.0 is the unweighted-anchor structural edge case within the `/ALPHA`
three). *(Count corrected 2026-06-12 pre-data-contact: an earlier draft said
"8" by double-counting α=0.0; the frozen P1/P2 grids are unchanged — see
§11.)*
The baseline is run as the anchor row (its gross at the reference horizons
reconciles against EXP-045's gross proxy as an integrity check). Everything
else about the substrate is frozen: arm/trigger at the AVWAP line, MAD-band
definition, anchor rule, pyramid handling — identical to Phases 004–011.

Rationale for OAT rather than the 16-point cross: the screen asks whether
*any single lever* moves gross edge materially; interaction tuning on TRAIN
before any lever shows main-effect signal would be premature optimisation
and would multiply the selection space 2×.

### 5.2 Gross statistic (exit-agnostic proxy)

Per cell × variant, on TRAIN events only:

- **Gross per-event expectancy** (direction-signed, real prices, no costs,
  no financing) at fixed reference horizons **H ∈ {4, 8, 16} domain bars**
  — the exit-agnostic proxy convention. H=8 is the **binding** horizon;
  H=4/16 are robustness disclosures (a variant whose edge exists only at
  one horizon is fragile, recorded as such).
- Bootstrap SE of the H=8 gross mean (descriptive; the EXP-027 machinery's
  resampling layer reused; no binding p-values — this is a TRAIN screen,
  not an inference read).

### 5.3 Cost floor and clearance rule (per cell)

The frozen P2 model defines the floor the gross edge must clear:

> `floor_i,d = RT_i + financing_i × days(H=8, d)`

where `days(H, d)` is the deterministic calendar-day holding time of H
domain bars (predeclared formula, D0 item 4). A cell **clears** for variant
v iff:

1. `gross(H=8) ≥ floor + 1 × SE` (margin predeclared, D0 item 5), and
2. `gross(H=4) > 0` and `gross(H=16) > 0` (sign robustness), and
3. event count ≥ 30 TRAIN events (the Phase 011 P3 floor, re-declared), and
4. determinism replay passes for the cell×variant event set.

### 5.4 Phase verdict input (G1 statistic)

Per variant: the set of clearing cells. The phase-level question is whether
any **non-baseline** variant's clearing set meets the composition threshold
(D0 item 6 — proposed: ≥5 cells over ≥3 instruments, echoing Phase 011 P5).
The baseline's clearing set is reported as the reference row (expected ≈
empty at these floors, per EXP-045).

## 6. Selection discipline

- All grids, thresholds, and formulas frozen at D0 before any TRAIN read.
- The screen may return **nothing** (Phase 011 lesson 3) — ENTRY_GROSS_FLAT
  is a complete, routable outcome, not a failure of the screen.
- No re-ranking, grid extension, threshold adjustment, or variant addition
  after any curve is seen. Follow-up variants require a new phase.
- Winner reporting is mechanical: clearing-set size, then instrument
  diversity, then gross(H=8) margin sum — no judgement ranking.
- Per Phase 011 lesson 2, the report carries the full gross-vs-floor
  decomposition per cell×variant regardless of verdict.

## 7. Methodological guardrails

- **Multiplicity posture:** 7 variants × 37 cells × 3 horizons is a large
  descriptive table; nothing in it is a significance claim. The only binding
  artifact is the mechanical G1 count against the predeclared threshold.
  The 1×SE margin is a noise guard, not an error-rate guarantee — any
  follow-on phase treats the winning variant as **selected-on-TRAIN**
  (disclosed) and must re-establish everything through its own net training
  and TEST endpoint, exactly as Phase 011 would have. The P6 composition
  threshold is evaluated per variant, so 6 non-baseline variants give 6
  independent chances to meet it — this variant-level multiplicity, and any
  cross-cell noise correlation inflating the per-variant false-positive
  rate, are absorbed by exactly that selected-on-TRAIN treatment: G1
  authorizes spending a follow-on phase, never a claim. The threshold's
  value is inherited from Phase 011 P5 as the minimum breadth that makes a
  follow-on portfolio endpoint worth building, not as an FDR control.
- **Power context (from EXP-043/044, binding realized figures):** TRAIN
  events 1h 151–273, 2h 86–143, 4h 32–86 per cell at baseline rates;
  variant populations will differ (MA changes move anchor counts) — the
  ≥30 floor and determinism check guard the small end. Median per-cell MDE
  16/32/64 bps (1h/2h/4h) says single-cell gross differences of a few bps
  are not resolvable — which is why clearance is `gross vs floor` per cell
  and the phase verdict is a composition count, not a variant-vs-baseline
  significance test.
- **Substrate integrity:** event generation uses the frozen `xen.avwap`
  machinery with parameterized α and MA inputs; defaults must reproduce the
  baseline bit-for-bit (regression suite from Phase 011 carries forward;
  extended to cover α/MA parameterization before first TRAIN read).
- **No financing/cost arithmetic on gross returns** beyond the floor
  comparison; no net columns anywhere in the results (prevents quiet
  re-introduction of exit assumptions).

## 8. Gate specifications

### 8.1 G0 — predeclaration completeness

D0 closes only when `D0-predeclarations.md` is operator-ratified: variant
grids (item 1–2), reference horizons + binding horizon (3), holding-day
formula (4), clearance margin (5), G1 composition threshold (6), event
floor (7), regression-suite extension requirement (8). Registry amended
(Phase 012 batch) before any TRAIN read.

### 8.2 G1 — screen adjudication (mechanical)

- **ENTRY_GROSS_VIABLE:** ≥1 non-baseline variant meets the composition
  threshold. Output: the winning variant(s) (mechanical ordering, §6) and
  their clearing sets, frozen as the follow-on phase's input.
- **ENTRY_GROSS_FLAT:** no variant meets it. Phase closes; programme pivots
  to substrate revision per the operator's pre-commitment (§1.4.2).

## 9. Phase outcome criteria

| Outcome | Condition | Consequence |
|---------|-----------|-------------|
| **ENTRY_GROSS_VIABLE** | G1 threshold met by ≥1 variant | Phase 013 design opens: per-cell exit training + portfolio endpoint on the winning variant, inheriting Phase 011's validated machinery (stability plane, inverted inference, ledger) under its own D0 |
| **ENTRY_GROSS_FLAT** | No variant meets G1 | Entry-parameter lever exhausted on this substrate; programme pivots to substrate-level revision (Stage-C detectors or new family) — operator pre-decision, no further routing discussion needed |

Either way: 0 TEST reads, ledger unchanged, holdouts sealed.

## 10. Non-goals and hand-off

- No MTF work (premise unchanged from Phase 011: needs tradable cells).
- No execution-cost work this phase; a broker-verified cost-model refresh
  may be declared at a future D0 but never retroactively.
- If pivoting: the substrate-revision phase starts from the Stage-C
  registered branches (`/LB` `/MB` `/ATR` `/ANCHOR`, deferred since Phase
  005) and the Phase 011 gross decomposition; it requires new readiness/
  calibration/parity passes (EXP-020/027/029 analogs) for any new event
  definition.

## 11. Amendment log

### 2026-06-12 — initial draft (no data contact)

Drafted from the operator's §9 Route-1 decision with the pre-committed
substrate-pivot fallback. D0 predeclarations proposed in
`D0-predeclarations.md` (DRAFT); none derives from Phase 012 data; no TRAIN
row has been read under any variant definition.

### 2026-06-12 — D0 closed, G0 PASS (no data contact)

Operator ratified `D0-predeclarations.md` P1–P8 as drafted (no value changed
between draft and ratification). Multiplicity registry amended (Phase 012
batch, 0 slots, 0 TEST reads). EXP-046 assigned at Stage-1 scoping. TRAIN
data contact authorized behind the P8 regression-suite gate; TEST-read
ledger untouched by construction.

### 2026-06-12 — G1 adjudicated, phase CLOSED

EXP-046 complete in one pipeline pass (audit PASS 0C/0W/3 Info;
post-experiment governance APPROVE; no revision cycles). G1 adjudicated
**ENTRY_GROSS_FLAT** ([G1-gate-review.md](G1-gate-review.md)): best
non-baseline clearing set 3 cells (alpha_1.0 3/3 instruments; ma_40_100
3/2) vs the P6 ≥5/≥3 threshold; integrity preconditions all satisfied
(reconciliation 259/259 at 1e-9 bps; determinism 259/259; no event-floor
collapse). Routing per the §1.4.2 pre-commitment: substrate revision
(§10 hand-off). No threshold, grid, or rule was changed after data
contact. Retrospective written same day; 0 TEST reads spent.
