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
  bite/MDE: <MDE curve or co-designed plant showing detectable effect size>     # B-5 shape
  non-vacuity: <which sufficient statistic of the metric it moves>              # B-6
  expected outcome if H true: <...>; if H false: <...>
  disclosure: collapse fraction reported (control effect / raw effect)          # B-2
```

Degeneracy test (B-1): if the strategy fires on every member of the conditioning set, a
"matched control at the same conditioning value" is the signal population itself — Δ≈0 by
construction. Every control block must state what the control could possibly show that the
signal series cannot.

Vacuity test (B-6): a permutation preserving the outcome multiset cannot referee a mean-based
metric. State the statistic the destroy actually perturbs.

## 4. Leak tripwire

```
TRIPWIRE: <future-shuffle | time-reversal | causal misalignment | ...>
  must collapse the edge; expected collapse fraction ≈ <...>
  vacuity check: <why this destroy can collapse THIS metric>
```

## 5. Interpretation bands (per stratum — no binaries)

```
BANDS (per stratum):
  SUPPORTED:      effect ≥ <size> with ci_low > <bound>
  WASH:           |effect| < <noise scale> (report as A≈B, not as refutation)
  CONTRADICTED:   effect ≤ <size> with ci_high < <bound>
  UNPOWERED:      n < <floor> or MDE > <plausible effect> — excluded from negatives
POOLED: disclosure-only unless homogeneity shown.
```

## 6. Power statement

```
POWER: expected events per stratum: <table>
  MDE at n=<...>: <...> bps
  strata predeclared UNPOWERED: <list>   # these can never be read as negatives (B-5)
```

## 7. Golden trace (for QA)

```
GOLDEN-TRACE: <2-3 events: timestamp, input state, expected entry price/side, expected exit
reason/price, hand-derived from this design. QA diffs these against the emission before
execution sign-off; the developer must not generate them.>
```

## 8. Integrity vs informative split

```
HARD (block): tripwire collapse, holdout, causal provenance, estimand reconciliation.
INFORMATIVE (operator judges): all effect sizes, significance reads, robustness reads,
  cost sensitivity, collapse fractions. No auto-verdict thresholds anywhere.
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
  cost floor:     <spread estimate + commission + capture dilution (≈ gap/2)>; state whether
                   the resulting effect clears it — if not, the experiment must be framed as
                   apparatus/characterisation, not tradability.
```

Each line is verifiable against data; QA traces this block as a clause. Power statements (§6)
and interpretation bands (§5) must use the pinned effect, never the raw screen units.
Full convention: `docs/references/spdr-lane.md` §Unit convention + money-unit floor.

## 10. T1 spread-scale routing (mandatory on Bybit T1 lane — INFR-010 §4, INFR-012)

Before any verdict-bearing T1 read, declare:

```
SPREAD-SCALE-ROUTING:
  estimated_rt_spread_bps: <from pseudo-quote series via xen.evaluation.t1_round_trip_spread_bps>
  gross_edge_bps: <TRAIN gross estimand, same cell>
  t1_undecidable: <YES if |gross| < 3× rt_spread | NO>
  if YES: disposition AWAITING_MBP or T2 confirm (BTC/ETH/SOL only, post-collection);
          pooled T1 reads disclosure-only
```

Use `xen.evaluation.spread_scale_route(gross_edge_bps, rt_spread_bps)` — do not re-derive
the 3× threshold. QA blocks a tradability band that ignores `t1_undecidable: YES`.

## 11. Spread as a verdict leg (mandatory for any SUPPORTED/tradability band — L-22)

A commission-only net band never binds on 0-commission instruments (indices), and the most
likely SUPPORTED cell (dense, short-hold, high-turnover) is exactly where spread dominates.
Any band that can emit a SUPPORTED/tradable claim must make the **1× spread estimate a
binding leg**: CI_low > 0 must survive commission + 1× spread before the cell counts toward
the multiplicity family (SUPPORTED-GROSS may be reported separately as disclosure).
0.5×/2× spread remain disclosure-only sensitivity.

**Chapter 04 (Bybit):** spread pins come from per-symbol pseudo-quote series +
`xen.evaluation.bybit_round_trip_cost_bps` (fees + spread + funding). FTMO table is
archived — use only for chapter-03 VAL re-analysis.

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
4. **MDE-consistent read floors (F07):** the TEST-read n floor = the n at which the cell's MDE
   ≤ its **shrunk** TRAIN effect (shrinkage from fold attenuation), applied prospectively —
   never a bare n ≥ 50 against an unshrunk selected maximum.
