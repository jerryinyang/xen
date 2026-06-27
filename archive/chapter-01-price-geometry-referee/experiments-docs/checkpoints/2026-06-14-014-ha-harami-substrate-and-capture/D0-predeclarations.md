# Phase 014 D0 Predeclarations — CF-HA-HARAMI-001

**Checkpoint:** `2026-06-14-014-ha-harami-substrate-and-capture`
**Governing design:** `design.md` (this directory).
**Status:** **RATIFIED — G0 PASS 2026-06-14 (operator).** All of P1–P13 are frozen as
predeclared governance parameters; P4 was revised to the operator's adaptive
duration-derived time cap before ratification. No row has been read under any harami
event definition. Nothing here is tuned against data. Any change after this point is
a new registered branch or a dated amendment, never an in-place revision.

**Discipline:** all Phase 014 work is **gross** (no costs). Harami detection is on HA
candles; **every outcome metric is on real prices** (`RealOpen/High/Low/Close`),
never HA prices. ZigZag pivots are future information until confirmed; only the
trend-change confirmation bar is a point-in-time reference. The final 30% global
holdout remains sealed and no new-universe row has been read under the HA-harami event
definition; 15m/30m cells require VAL-004 PASS.

---

## P1 — ZigZag substrate (DECIDED)

ATR estimator **Wilder**, `atr_period = 14`, `ATR_MULT = 1.0`. Warmup: no
pivot/threshold until ATR is defined (≥14 completed real bars); pre-warmup bars
carry no trend state. Seeding on the first defined bar: bullish bar (`Close > Open`)
→ trend Bullish, pivot `High`; bearish → trend Bearish, pivot `Low`. Trend-change
confirmation: first completed bar closing beyond `pivot ∓ ATR_MULT × ATR` adversely
to the current trend. Computed on real (non-HA) bars. Sensitivity is
`CF-HA-HARAMI-001/ATRMULT`, not an in-place change.

## P2 — Favourable target (DECIDED)

Benchmark favourable target = retrace **50%** of the immediately preceding *confirmed*
move, measured from the signal-confirmation price, on real prices. Frozen at the
confirmation bar. (100% was an illustrative example in the source draft, not the
default.)

## P3 — Adverse target (proposed)

Benchmark adverse target = **1:1 R:R** — adverse distance equals the favourable
distance, on the opposite side of the entry. Frozen at the confirmation bar.
Alternatives are registered branches: `/ADV-EXTREME` (previous-move extreme),
`/ADV-NONE`.

## P4 — Third barrier (revised per operator)

Benchmark third barrier = a **per-cell, causally-adaptive fixed-holding time cap**,
not a uniform constant. For each event:

```
N_event = max(6, round(1.5 × median(duration_bars of the trailing 20 confirmed
                                     moves in this instrument+domain cell)))
```

completed domain bars after the confirmation bar, where `duration_bars` is the bar
count between consecutive confirmed trend-change events (a move's own realized
length), measured strictly on moves **confirmed before** the signal.

**Rationale (operator).** The cap should adapt to each cell's characteristic move
tempo rather than a hand-set per-domain constant. Because lower timeframes traverse
the same economic move in many more bars, a duration-derived cap **automatically**
grants smaller timeframes a larger bar-count window (tolerating their higher
noise-to-signal ratio) and larger timeframes a shorter one — exactly the intended
scaling, derived structurally rather than tuned. This mirrors the programme's
accepted "structural derivation, not outcome-tuning" precedent (Renko/ZigZag ATR
sizing). `(window = 20, k = 1.5, floor = 6 bars, statistic = median)` are governance
parameters fixed at G0, never tuned against outcomes; k-sensitivity is the registered
`/THIRD-TIME` branch.

**Causality / determinism.** The rolling median uses only moves confirmed before the
event and is frozen at the confirmation bar. **Warmup:** an event whose trailing
window holds `< 5` confirmed moves has no defined cap and is **excluded from the
EXP-049 capture read** (insufficient context, disclosed) — never defaulted silently.

**Censoring disclosure.** The third-barrier censoring fraction is reported per cell;
a shorter adaptive cap on fast-alternating cells may raise censoring — disclosed, not
hidden. The `/THIRD-EVENT` (opposing-signal) exit remains the registered structural
alternative.

## P5 — `LOOKBACK` (proposed)

Default **`LOOKBACK = 1`**: the immediately preceding confirmed move is the absolute
price reference for the favourable/adverse targets. `LOOKBACK > 1` yields magnitude
estimates only (no absolute levels) and is the `/MAGTARGET` / `/LOOKBACK` branch.

## P6 — Strong-move filter default (proposed)

Default **OFF** (base harami). The core signal is characterized unfiltered first;
filters (`/STRONG-STAT`, `/STRONG-HA`) are variants varied one-at-a-time against this
default in EXP-051.

## P7 — `/STRONG-STAT` defaults (proposed)

Rolling window = trailing **20 confirmed moves** (per cell, causal — confirmed moves
only). Threshold (primary, non-parametric): move magnitude **≥ the 75th percentile**
of the window's move magnitudes. Magnitude = price excursion of the confirmed move
(scale-free within instrument). Registered alternative inside `/STRONG-STAT`'s
predeclared grid: **≥ median + 1×MAD** of the window. No post-result selection
between forms.

## P8 — `/STRONG-HA` defaults (proposed)

Run length **`X = 3`** consecutive HA bars, each with (a) real body ≥ the trailing-20
median HA real body and (b) no opposing wick (no lower wick for bullish HA bars, no
upper wick for bearish). Purely causal by construction.

## P9 — "Near-exhaustion" (HYP-003) (proposed)

**Definition:** a harami is *near-exhaustion* if its confirmation bar sits at
position **≥ 0.67** of the confirmed move by **price excursion**
(`(signal_price − move_start) / (move_end − move_start)`, direction-signed), i.e. the
final third. Duration-fraction position is reported as a secondary descriptive view.

**Causality note:** position-in-move uses the *confirmed* move boundaries
(pivot-to-pivot), which is permitted because HYP-003 is **descriptive
characterization of completed moves**, not a live signal — no trading decision uses
the unconfirmed pivot. This is the family doc's explicit "completed-move grouping"
allowance.

**Cluster materiality:** harami signals are *materially clustered near exhaustion* in
a cell iff the observed final-third rate exceeds the P13 baseline final-third rate by
**≥ 10 percentage points**. Composed by P11.

## P10 — "Materially different" move populations (HYP-004) (proposed)

A strong-move filter identifies a *materially different* population in a cell iff
(a) the filtered set's **median move magnitude ≥ 1.5×** the unfiltered median, **and**
(b) the **retained fraction ∈ [0.10, 0.50]** (selective but not degenerate). Both
conditions required; composed by P11. Cross-cell consistency is reported.

## P11 — Per-cell composition rule (proposed)

Any family-level "material" claim requires the per-cell criterion to hold in
**≥ 5 cells over ≥ 3 instruments** — the programme convention (Phases 012/013 P5/P6).
Per-cell outcomes are independent; the composition is mechanical, applied after
per-cell adjudication.

## P12 — Capture-geometry viability (HYP-002 routing) (proposed)

Per cell, on EXP-049 default barriers (P2/P3/P4/P5), gross, exit-agnostic:

- **Primary endpoint:** `r = P(favourable before adverse | resolved)` where
  `resolved = fav-hits + adv-hits` (third-barrier/time-cap events excluded from the
  denominator). Symmetric 1:1 barriers ⇒ a zero-edge null of **r = 0.50**.
- **Viable cell:** `r ≥ 0.55` **and** bootstrap (regime-clustered) CI_low **> 0.50**
  **and** **≥ 30 resolved events**.
- **Routing:** capture geometry is VIABLE for the family iff viable in **≥ 5 cells
  over ≥ 3 instruments** (P11) → continue to 014-B; else CHARACTERISED_NOT_VIABLE.

**Disclosed secondaries (never the binding endpoint):** `fav / all events` (counts
the time-cap as non-favourable) and the **third-barrier censoring fraction** per
cell. **Zero-baseline handling:** a cell with `< 30 resolved events` is
**NOT_VIABLE-by-power** — non-reportable for routing, never an undefined or infinite
ratio; `resolved = 0` ⇒ NOT_VIABLE-by-power, not `0/0`.

## P13 — HYP-003 baselines (proposed)

Two look-ahead-safe baselines, both matched per cell:

1. **Random matched-count timestamps** drawn from the same cell and regime direction
   (fixed seed), scored through the identical position-in-move metric.
2. **Alternative move segmentation:** MA(20,50) crossover regimes (the validated
   AVWAP-family detector, code already in `xen`) used to define moves, scored
   identically. Tests whether "near exhaustion" is an artifact of the ZigZag
   segmentation rather than a property of harami timing.

---

## Slot & ledger accounting (binding)

- All Phase 014-A/B experiments are **characterization/diagnostic: 0 candidate slots,
  0 TEST reads.** The 12 registered variant branches consume a slot only when a
  future scope activates one as a screening candidate.
- A candidate branch for screening is registered only at the close of 014-B, with the
  selected-on-TRAIN disclosure.
- TEST-read ledger unchanged; holdouts sealed; no new-universe row read under the
  HA-harami event definition.

## G0 ratification checklist

- [x] P3–P13 reviewed; accepted (P1/P2 operator-decided; P4 revised to the adaptive
      duration-derived cap per operator).
- [x] `multiplicity-registry.md` Phase 014 batch confirms the family, HYPs, and
      variant surface.
- [x] VAL-004 (15m/30m temporal integrity) sequenced before EXP-048 reads those cells.
- [x] No data contact has occurred (no `results/` under any Phase 014 EXP).
- [x] Operator sign-off recorded → **G0 PASS 2026-06-14**. Pipeline entry point:
      VAL-004, then EXP-048.
