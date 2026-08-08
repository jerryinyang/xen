# Design Requirements — Mandatory Declarations

Every `design.md` carries these blocks verbatim (filled in). QA pre-exec rejects a design
missing any block. Each exists because its absence shipped a real defect (issue IDs from
`consolidation-issues-014-017.md`).

---

## 1. Mechanism statement

```
MECHANISM: <the regularity exploited, its horizon, its event cadence, and the P&L-bearing
object (leg / episode / per-bar carry). One paragraph, falsifiable.>
DERIVED: estimand=<...> null=<...> horizon=<...> test=<...>  # each traceable to the mechanism
```

Anti-pattern (L-13): an evaluation stack reused from a previous family unchanged. If the
estimand/null/horizon would be identical for a completely different mechanism, they were not
derived — start over.

## 2. Object identity declarations

```
OBJECT-IDENTITY:
  measurement object == trading object: <YES + what both are | justification>   # B-8/L-16
  measured conditioning event == traded entry event: <YES + what both are>      # B-4
  effect-splitting windows non-overlapping: <YES + windows | N/A>               # B-9
```

B-4 test: describe the exact bar/price state at which the strategy commits capital; the
availability/quality measurement must condition on THAT state, not a correlated one (close-breach
vs band-touch cost CF-MR-004 its entire availability leg).

## 3. Control validity proofs (one block per control)

```
CONTROL <name>:
  question answered: <what attribution/robustness question>
  population: <control pool>; DISJOINT from signal population: <why>            # B-1
  bite: <co-designed synthetic plant showing the control can detect an effect of
        the expected size — no MDE curve, no detection floor (INFR-022 L-63)>    # B-5 shape
  non-vacuity: <which sufficient statistic of the metric it moves>              # B-6
  expected outcome if H true: <...>; if H false: <...>
  disclosure: collapse fraction reported (control effect / raw effect)          # B-2
  destroy form (if permutation): DERANGEMENT (zero fixed points) | other + why  # L-28
```

Degeneracy test (B-1): if the strategy fires on every member of the conditioning set, a
"matched control at the same conditioning value" is the signal population itself — Δ≈0 by
construction. Every control block must state what the control could possibly show that the
signal series cannot.

Vacuity test (B-6): a permutation preserving the outcome multiset cannot referee a mean-based
metric. State the statistic the destroy actually perturbs.

**Derangement rule (L-28):** any control or null arm that *destroys* timing/alignment via
permutation of a schedule, labels, or indices must use a **derangement** (zero fixed points).
A plain permutation leaks signal through fixed points (VAL-008: 11.1% alignment → collapse
only 0.87). State `destroy form: DERANGEMENT` in the block; if a non-derangement destroy is
intentional, predeclare residual fixed-point rate and why the bite remains valid. Builds on
L-14 / L-19.

## 4. Leak tripwire

```
TRIPWIRE: <future-shuffle | time-reversal | causal misalignment | ...>
  must collapse the edge; expected collapse fraction ≈ <...>
  vacuity check: <why this destroy can collapse THIS metric>
  if permutation-based: derangement=YES (zero fixed points; L-28)
  integrity_bite: INTEGRITY_Z × bootstrap_SE (same SE family as the control's own
                  estimator; default INTEGRITY_Z = 2.8 unless this design names another
                  constant — documented in the integrity section)  # N6b
```

The tripwire is the ONLY control class with blocking authority (validity of the emission,
not value of the edge). Its integrity bite scale is a **validity threshold on a planted
leak contrast — not a powering method for research estimands** (INFR-022 N6b): it must never
be called MDE, never a detection floor, and must not use MDE/MDE_Z/UNPOWERED vocabulary.

## 5. Interpretation bands (per stratum — OPERATOR-ONLY tags, never machine fields)

```
BANDS (per stratum):
  SUPPORTED:      effect ≥ <size> with ci_low > <bound>
  WASH:           |effect| < <noise scale> (report as A≈B, not as refutation)
  CONTRADICTED:   effect ≤ <size> with ci_high < <bound>
POOLED: disclosure-only unless homogeneity shown.
```

INFR-022 N11: bands are **operator-supplied tags only** — the design may predeclare the
plain-language bands the operator MAY use to tag a report layer after reading numbers; they
are never machine-assigned, never gate, never drop rows, and never appear as machine fields
on emission rows. `UNPOWERED` as a machine row label is deleted; small-count rows are always
reported next to their counts (N3).

## 6. Sample-size statement (INFR-022 L-63 — replaces the AMENDMENT-7 power statement)

```
SAMPLE-SIZE:
  expected events per stratum: <table>            # planning context only
  minimum_n_for_primary_inference: <optional per stratum>   # DESCRIPTIVE tag only —
        # rows below it are still reported with their counts and intervals (N3/N10);
        # the tag limits only the *language* of primary inference, never the row
  declared_fixed_comparator: <the pre-specified baseline model every conditioned arm is
        read against — estimate + uncertainty + counts; no threshold applied>
  channels:                                      # per-channel scale declaration (R4)
    - name: <...>
      sigma_denominator: <paired_delta | outcome_level | ...>
      # channels with different denominators MUST NOT share one numeric ladder
  strata predeclared thin: <list>                # reported with counts — never hidden,
        # never read as negatives (B-5), never labelled UNPOWERED
```

Rules:
1. **R1/R5** — expected counts and historical context are **context only**, never gates and
   never thresholds on a realised estimate.
2. **R4** — every channel declares `sigma_denominator`; different denominators are never
   ranked on one ladder.
3. **N3/N10** — no row is dropped, trimmed, top-N pruned, relabelled, promoted, demoted, or
   omitted because of its count, interval width, or any sample-size quantity. A wide interval
   is reported as a wide interval, not as an absence.
4. **N4** — every adaptive/conditioned arm is read against the declared fixed comparator,
   never against another adaptive arm, never against a threshold.
5. **Stripped (prohibited in designs):** MDE, `mde_bps`/`mde_sigma`, `MDE_Z` (except the
   renamed validity constant in §4, which must be called `INTEGRITY_Z`), detection floors
   (`2.8/√n`, `MDE_Z × SE` on research estimands), mechanism ceilings (`√p × Sharpe`), power
   curves / end-to-end power calibration, "at power", "resolved/unresolved at this power",
   "below/above detection floor", machine `UNPOWERED`/`WASH`/`CLEARS_FLOOR` row labels.

## 7. Golden trace (for QA)

```
GOLDEN-TRACE: <2-3 events: timestamp, input state, expected entry price/side, expected exit
reason/price, hand-derived from this design. QA diffs these against the emission before
execution sign-off; the developer must not generate them.>
```

## 8. Integrity vs informative split

```
HARD (block): tripwire collapse, holdout, causal provenance, estimand reconciliation,
  zero-cost compliance (no non-zero cost without a recorded operator cost directive).
INFORMATIVE (operator judges): all effect sizes, significance reads, robustness reads,
  PSR, collapse fractions. No auto-verdict thresholds anywhere.
```

## 9. Screen-effect conversion pin (mandatory when the design cites SPDR/screen evidence — L-21)

Dimensionless screen numbers become money claims at this seam; EXP-025 inflated its target
4× by asserting the wrong ATR divisor from memory. Any design that converts a screen-derived
normalised effect into bps/money must declare:

```
CONVERSION-PIN:
  divisor object: <verbatim from the screen code — indicator, period, timeframe, lag,
                   e.g. "LTF 5min ATR(14)[t−1], spdr00X_screen.py:<line>">
  measured value: <TRAIN-median of that exact object on the target instrument(s), in bps —
                   computed from data, never recalled>
  resulting effect: <screen effect × measured value = <X> bps/trade>
  zero-cost note: the programme is ZERO-COST (INFR-022) — no cost floor applies; the
                   experiment must still be framed as apparatus/characterisation unless the
                   operator separately sanctions deployment claims (which remain refused by
                   rule).
```

Each line is verifiable against data; QA traces this block as a clause. Sample-size
statements (§6) and interpretation bands (§5) must use the pinned effect. Full convention:
`docs/references/spdr-lane.md` §Unit convention.

## 10. Zero-cost disclosure (mandatory on every design — INFR-022 directive 1)

```
ZERO-COST-DISCLOSURE:
  cost_model: NO_COST_CHARGED
  spread: not modeled
  commissions: not modeled
  swaps/funding: not modeled
  implication: every figure in this document is gross and cost-free; no spread, commission,
    or swap enters any calculation. Realised results would differ (likely worse) under any
    real cost schedule.
  prohibited_claims: fully-net, cost-complete, tradable, deployable
  lifting: only an explicit operator directive may introduce a cost model for a scoped
    experiment; the directive is recorded in that experiment's design.md.
```

All three lanes (XENA, SPDR, EXP) default to zero cost. "Zero" is a model, not a
measurement. The retired cost stack (`bybit_round_trip_cost_bps`, FTMO tables,
`spread_scale_route`) is archive-only (`xen/evaluation_cost_legacy.py`, ARCHIVED banner).

## 11. Cost directive clause (only when an operator directive requests costs)

A design that charges costs MUST carry the operator's directive:

```
COST-DIRECTIVE:
  directive_id: <operator directive reference>
  reason: <operator-signed reason string — recorded verbatim>
  scope: <experiment-scoped: this design only>
  functions: <the exact cost functions/parameters re-enabled>
  run_dir_file: operator_cost_directive.json (written next to the manifest / run dir before
                execution; QA traces design clause + file)
```

Without this clause (and the file), non-zero `--cost-bps`, `charge_costs=True`, and any cost
function call are refused by code asserts. Deployability/tradability claims remain refused
by rule — the zero-cost model does not loosen them.

## 12. Amendment-direction ledger (mandatory once any pre-measurement amendment lands — L-23)

Every pre-measurement amendment to a registered design declares:

```
AMENDMENT-<n>: <one-line change> — DIRECTION: LOOSER | TIGHTER | NEUTRAL
  running count: <L> looser / <T> tighter / <N> neutral
```

After the final amendment, re-derive the expected false-qualifier count under the global null
with the FINAL gate set (apply the selection rules to the random-direction battery runs); if
materially above the declared budget, tighten one gate back. A one-directional streak ≥ 3 is
an explicit operator flag at the execution gate.

## 13. Battery/eligibility/null design rules (mandatory for battery-gated, multi-cell, or capped-read designs — L-24)

1. **Time-stability eligibility (F02):** a seed battery prices direction-randomization only.
   Eligibility must add a time-stability read — TRAIN net positive in ≥2 of 3 chronological
   thirds, or a declared concentration ceiling (top-decile trade / top-quarter share).
2. **Exit-matched nulls (F04):** if a qualifying statistic depends on a path-dependent exit
   (exit* ≠ benchmark), each battery seed re-runs under exit*, and the exit-selection step is
   registered in the multiplicity ledger; if infeasible, exit* is demoted to disclosure.
3. **Derived tripwire thresholds (F06):** phase-shift retention REJECT thresholds are computed
   from the real TRAIN autocorrelation of the shifted stream (with CI), never asserted.
4. **Sample-size notes, never hide rules (F07, INFR-022):** a design may pre-declare a
   minimum n for *primary-inference language* — a descriptive tag only: the row, estimate,
   interval and n still appear below it (N3/N10). No MDE-consistent read floor, no n-veto,
   no row demotion from counts.
