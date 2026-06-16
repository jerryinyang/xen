# Phase 014-B D0 Addendum — CF-HA-HARAMI-001 (P14–P21)

**Checkpoint:** `2026-06-14-014-ha-harami-substrate-and-capture`
**Governing design:** `014-B-design.md` (this directory); extends `design.md` §7 and the
ratified `D0-predeclarations.md` (P1–P13, G0 PASS 2026-06-14).
**Status:** **RATIFIED — G0-B PASS 2026-06-15 (operator).** P14–P21 are frozen governance
parameters for 014-B (P14 binding endpoint = **median** per-event expectancy, mean disclosed;
P18 `ATR_MULT_TRAIL = 0.5`, tunable later via the registered sensitivity grid). P1–P13 are inherited
unchanged except where a P14+ item explicitly supersedes a *binding endpoint* choice (P14
supersedes P12 as the binding metric; P12 `r` is retained as a disclosed secondary).
**Discipline:** all 014-B work is **gross** (no costs); detection on HA candles; **every
outcome metric on real prices** (`RealOpen/High/Low/Close`), never HA prices. Holdouts
sealed; no new-universe row read under the HA-harami event definition. Nothing here is tuned
against data; any change after ratification is a new registered branch or a dated amendment.

> **Mandatory-reading precondition (binding).** No 014-B scope is admissible until it records,
> in `scope.md`, that `014-A-conditioning-gap-and-validation-lessons.md` was read and that the
> experiment honours the conditioning / harami-anchor / descriptive-position / expectancy
> rules. Enforced at Stage 4 (REVISE if absent).

---

## P14 — Binding endpoint: gross per-event expectancy (supersedes P12 as binding)

For each event, the rule (entry + barriers/exits) produces a **realised gross return**,
direction-signed, **ATR-normalised** (divide by the cell's confirmation-bar ATR(14) so cells
are comparable), computed on **real prices** under the P15 fill model.

- **Per-cell endpoint (binding):** **median** per-event realised gross return `E_cell`
  (operator decision 2026-06-15 — robust to the fat-tailed per-event return distribution),
  with a regime-clustered moving-block bootstrap CI (`b = round(m^(1/3))`, `N_BOOT = 10_000`,
  fixed seed) — the EXP-049/EXP-027 machinery.
- **Per-cell viability (for characterisation and the G2 readout):** `E_cell` (median) with
  **CI_low > 0** and **≥ 30 events**. Composed by **P11** (≥5 cells over ≥3 instruments).
- **Disclosed secondaries (never binding):** **mean** per-event return; first-hit `r` (P12);
  win rate; the P4/third-barrier censoring fraction.
- **Zero-baseline / power:** a cell with < 30 events is NOT_VIABLE-by-power (non-reportable
  for the readout), never an undefined ratio.

Rationale: a first-hit rate is blind to partial exits and trailing stops; the binding metric
must be one the family's position-management mechanisms can move (lessons §8.6).

## P15 — Intrabar fill model (method standard; replaces the worst-case tie-break)

When a single domain bar could touch more than one barrier/exit level, fills resolve in
**path order** under a fixed intrabar-motion assumption (operator):

- **Bullish bar** (`Close ≥ Open`): `Open → Low → High → Close`.
- **Bearish bar** (`Close < Open`): `Open → High → Low → Close`.

The first level reached along that path fills first. This supersedes EXP-049's blanket-adverse
tie-break for every 014-B outcome read. The assumption is a **documented approximation** of
unobserved intrabar motion (1-minute base bars are not replayed inside the domain bar); it is
disclosed in every result that depends on it, and EXP-054 quantifies its effect vs the
worst-case baseline. This is the "dedicated fill-rule method validation" the registry deferred
(Phase 010 carried item).

## P16 — Conditioned signal definition (the live family signal)

The 014-B efficacy object (EXP-053 lead) is:

1. an HA harami detected on HA candles (frozen detector, EXP-048), **AND**
2. the **current move's magnitude-so-far** — distance from the last *confirmed* ZigZag pivot
   (known) to the current price — is **≥ the 75th percentile** of the trailing-20
   confirmed-move magnitudes (the `/STRONG-STAT` live filter, P7). `/STRONG-HA` (P8) is the
   registered alternative form.
3. **Entry is anchored at the harami** (the harami confirmation bar close), to capture its
   lead over the ZigZag's `ATR_MULT × ATR` giveback — **not** at the ZigZag trend-change
   confirmation.

**Position-in-move (P9, ≥0.67) is descriptive-only and is never used as a live filter** — the
move's end pivot is future information for an in-progress move (family-doc causality, lines
113–118, 137–149). EXP-050's metric stays a characterisation lens.

## P17 — `/EXIT-PARTIAL` (favourable-side scaled exits)

Take-profit only; the adverse-target model is unchanged. Full entry weight split into **≤ 3**
equal parts. Two predeclared variants (no post-result selection between them):

- **Variant #1 (event triggers):** three legs exit on, respectively, the **first profitable
  bar close**, the **calculated favourable target** (whatever favourable model is in force),
  and a **reversal event** (opposing harami/strong-move signal or ZigZag trend-change).
- **Variant #2 (percentage-to-target):** legs exit at predeclared fractions of the final
  favourable target distance (e.g. 1/3, 2/3, full), ≤3 splits.

All legs evaluated on real prices under the P15 fill model. Causal (no leg references future
bars). Usable alone or combined with P18.

## P18 — `/EXIT-TRAIL-STRUCT` (adverse-side structure trailing stop)

Adverse exit driven by a **second, smaller-`ATR_MULT` ZigZag** (predeclared
`ATR_MULT_TRAIL = 0.5`; sensitivity is the registered `/THIRD-TIME`-analog grid, no
post-result selection) on real bars:

- On a new confirmed **pivot high** (long trades): move the trailing stop to the **most recent
  confirmed pivot low**.
- On a new confirmed **pivot low** (short trades): move the trailing stop to the **most recent
  confirmed pivot high**.
- **Exit** when price fills the trailing stop (real prices, P15 fills).

The trailing ZigZag is causal (pivots used only once confirmed). Usable alone or combined with
P17 (partial favourable exits + structure trailing adverse).

## P19 — Long-horizon availability diagnostic (EXP-055 / AVWAP-analog)

Over the **full reversal move** following a conditioned harami (pivot-to-next-confirmed-pivot;
completed-move grouping is the family doc's descriptive allowance), measure, gross,
ATR-normalised:

- lifetime favourable **MFE** (max favourable excursion) and adverse **MAE** (max adverse
  excursion), per event; per-cell medians and distributions;
- vs a **cost-floor-analog reference line** (a fixed ATR fraction, declared; never subtracted —
  reference only, mirroring Phase 013 EXP-047).

Output is the AVWAP-comparison fork: *availability good + capture missing* (keep iterating
geometry/exits) vs *no available move* (closure well-supported). Reuse EXP-047
`move_size.py` machinery.

## P20 — Composition, power, baselines (014-B)

- **Composition:** P11 (≥5 cells over ≥3 instruments) for any family-level "viable"/"material"
  claim, applied after per-cell adjudication.
- **Power:** ≥30 events per cell on the conditioned population; conditioning will reduce event
  counts vs the unconditioned base (EXP-051 retained fraction f ≈ 0.20–0.27) — cells dropping
  below 30 after conditioning are NOT_VIABLE-by-power, disclosed, never defaulted.
- **Baselines (P13 carried):** matched-count random timestamps (same cell/regime) and the
  MA(20,50) alternative segmentation, scored through the identical expectancy metric.

## P21 — G2 adjudication (no intermediate gates)

The full 014-B slate (EXP-053–060) is measured before any adjudication. A single **G2** desk
review (operator ratification) applies the §8 outcome criteria of `014-B-design.md`. **No
early-closure path exists inside 014-B**: a negative on any single geometry never closes the
phase. PROCEED_TO_SCREEN registers a candidate branch (its first slot) only at G2.

---

## Slot & ledger accounting (binding)

- All 014-B experiments are **characterization/diagnostic: 0 candidate slots, 0 TEST reads**.
  The registered variant branches (incl. the new `/EXIT-PARTIAL`, `/EXIT-TRAIL-STRUCT`)
  consume a slot only when a future scope activates one as a screening candidate — which, per
  P21, cannot happen before G2 PROCEED_TO_SCREEN.
- TEST-read ledger unchanged; holdouts sealed; no new-universe row read under the HA-harami
  event definition.

## Ratification checklist

- [x] P14–P21 reviewed and accepted (operator, 2026-06-15) — P14 median binding (mean
      disclosed); P18 `ATR_MULT_TRAIL = 0.5`, tunable later.
- [x] `multiplicity-registry.md` Phase 014-B batch records HYP-006–013 / EXP-053–060 and the
      two new branches before any result-producing code.
- [x] `candidate-families/harami.md` lists `/EXIT-PARTIAL`, `/EXIT-TRAIL-STRUCT` and the
      fill-model standard.
- [x] No 014-B data contact before ratification (no `results/` under EXP-053+).
- [x] Operator sign-off → **G0-B PASS 2026-06-15.** Pipeline entry point: EXP-053
      (conditioned-signal efficacy), Stage-1 scope after the mandatory lessons read.
