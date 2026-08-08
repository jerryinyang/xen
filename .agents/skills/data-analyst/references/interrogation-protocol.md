# Interrogation Protocol

Question-generation protocol + `analysis.md` template. Successor to the auditor's
checklist tables: those verified numbers reproduced; this extracts what the data actually says.

---

## Mandatory minimum question set

Answer all of these for every experiment (add mechanism-specific questions on top).
"Report says X" is never an answer — every answer computes from raw emissions via canonical
`xen` code.

### Accounting & object identity
1. Do per-bar and per-leg totals reconcile per cell? (from `estimand_validation.json`; restate.)
2. What is the P&L-bearing object (leg / episode / per-bar)? Does the design's estimand match
   the object the strategy actually trades? (L-16)
3. Per-leg gross distribution: mean, median, std, q01/q05/q95/q99, per cell. Where does the money
   actually come from?

### Structure & concentration
4. Episode anatomy (multi-leg arms): episode count, duration distribution, legs/episode,
   max concurrent legs, net/episode distribution.
5. Concentration: net total without the top 1/3/5 winning episodes (or legs). Does the edge
   survive removing the tail?
6. Per-year totals: is the effect stable across years or one regime's artifact?
7. Per-stratum: every headline re-derived per instrument/cell. Which strata drive it, which
   contradict it?

### Physicality & behaviour
8. Occupancy: what fraction of time in market, and does that match the strategy's design story?
   (A 70%-occupancy "dislocation fader" is a grid — say so.)
9. Annualised return / Sharpe / maxDD vs the same emission's buy-and-hold: plausible for the
   instrument class? What do these numbers say about what the strategy IS?
10. Exposure risk: max open legs, drawdown in exposure-weighted terms, worst episode MAE,
    underwater durations.

### Robustness & falsification
11. Zero-cost verification (INFR-022): confirm the emission and all reads are gross and
    cost-free — no non-zero commission/fee/funding/spread column (estimand gate
    `no_cost_charged`), no cost function called, no net-of-cost figures; the
    ZERO-COST-DISCLOSURE caveat sits on every money-bearing table. Any costed read must trace
    to the recorded operator cost directive (design clause + `operator_cost_directive.json`).
12. PSR pairing (INFR-022 directive 4): every mean trade/leg bps read carries `psr` + `psr_n`
    computed on the SAME per-trade series and population (never another population's n).
    NaN + n stated when n < 2; the row still appears (N3).
13. For each control read: collapse fraction, not just survive/die. Is the control sensitive to
    the dominant mechanism at all (B-3 shape)?
14. For every headline number: one "what would make this wrong?" probe, executed (e.g. recompute
    under alternative attribution, drop censored legs, split halves).
15. Sample-size context (INFR-022 L-63): every row reports its n / effective n; a negative is
    accompanied by the row's own CI width ("no effect" vs "cannot see"). No MDE / floor /
    power label is used as a row verdict — small-n rows are reported with their counts (N3).
16. Direct comparison (N4): is every conditioned arm read against its pre-specified declared
    comparator, never against another adaptive arm and never against a threshold?

---

## Failure patterns worth probing (condensed from the audit-era catalog)

| Pattern | Probe |
|---|---|
| Off-by-one / lag errors | Recompute one signal by hand at 2-3 timestamps from raw bars |
| Wrong split | Confirm chronological ordering + 70% cut by timestamp, not row position |
| Fill plausibility | Fills within bar [Low, High] (tolerance); breach rate |
| **Nautilus fill-ts off-by-one (L-29)** | Fill-ts = decision-bar close = wall-clock open of fill bar. Naive `searchsorted` on bar closes mis-indexes by one. **Anchor:** `EntryFillPrice == next-bar RealOpen ± 1 tick` (or design fill basis) on a sample of legs |
| Duplicate/missing events | Event counts vs bar counts; duplicate timestamps |
| Pooled masking | Per-stratum table vs pooled headline; one stratum vetoing or carrying |
| Gate-shape blindness | Effect shape (location/tail/asymmetric) vs what the statistic measures |
| Mean-invariant control | Does the destroy control move the metric's sufficient statistic at all? |
| Non-derangement destroy (L-28) | Permutation controls: measure fixed-point rate; must be 0 (derangement) or residual disclosed |
| Acausal favourable-index (L-01) | Own-bar close used as that bar's intrabar limit |
| Synthetic prices | Any P&L touching HA/Renko constructed prices |
| Multi-leg accounting (L-18) | Any per-bar series not built by `xen.adjudication` |
| **Costs entering a live calculation (INFR-022)** | Any non-zero commission/fee/funding/spread column, `--cost-bps ≠ 0` without a recorded directive, net-of-cost figures, missing zero-cost caveat |
| **Power machinery as row verdicts (INFR-022 L-63)** | MDE / `MDE_Z × SE` / `k/√n` floors, power curves, `UNPOWERED`/`WASH`/`CLEARS_FLOOR` machine labels, rows hidden or demoted for low n — report estimate + CI + count, operator judges |
| **PSR missing beside a mean (INFR-022 directive 4)** | Any mean trade/leg bps read without `psr` + `psr_n` on the same series |

---

## `analysis.md` template

```markdown
# Data Analysis: <EXP-ID>

## 0. Boundary statement (N1 — binding)

This record issues NO verdict, names NO winner, ranks NO arm, claims NO tradability/
deployability, and gates NO companion experiment or family action. Every observation below
is labelled observed (read directly from an emitted artifact) or inference (a mechanism
reading of observed numbers that is not itself measured). Zero-cost model: every figure is
gross and cost-free (ZERO-COST-DISCLOSURE).

## 1. Integrity gate (blocking)

| Check | Result | Evidence |
|---|---|---|
| Estimand validation (all cells blocking_pass) | PASS/FAIL | results/estimand_validation.json |
| Zero-cost compliance (`no_cost_charged`, no directive-gap costs) | PASS/FAIL | estimand gate + design §10/§11 |
| Provenance trace (verdict-bearing columns ≤ t-1) | PASS/FAIL | <file:line rows below> |
| Leak tripwire collapsed + non-vacuous (bite = INTEGRITY_Z × bootstrap_SE, N6b) | PASS/FAIL | <control, raw vs destroyed, collapse fraction> |
| Holdout untouched | PASS/FAIL | <evidence> |
| Price-primary (engine emission under fence; STUB attestation = FAIL) | PASS/FAIL | data/nautilus_runs/… |
| No experiment-local accounting defs | PASS/FAIL | check_no_local_accounting |

<Provenance table: column | inputs & timestamps | ≤ t-1? | file:line>

## 2. Question list
<numbered; every question ANSWERED (§ ref) or UNANSWERED (reason)>

## 3. Evidence FOR the hypothesis
<each item: observation, effect size, CI, n, stratum coverage; PSR + n beside each
mean-trade/leg bps read, same series>

## 4. Evidence AGAINST the hypothesis
<same rigor; small-n rows reported next to their counts — never hidden, never labelled>

## 5. What would make the headline numbers wrong (N7)
<for each headline: the probe that would falsify it, and whether it was run>

## 6. Anomalies & open questions
<unexplained observations; suggested probes; anything the operator should push on>

## 7. Recommended verdict (experiment hypothesis only — NOT final, NOT family)
- Recommendation: SUPPORTED / NOT SUPPORTED / INCONCLUSIVE / WASH (A≈B within noise)
- Driven by: <the 2-3 decisive pieces of evidence>
- Would change if: <what probe/result would flip this>
- Hand-off: final verdict is the operator's; named probes runnable against the existing
  emission.
```

## Report discipline

- Every number traceable: script path in `analysis_code/` + emission file.
- Effect sizes with CIs, never bare p-values; per-stratum before pooled.
- Symmetric skepticism: a wash is a wash — do not dress A≈B as a refutation, and do not
  inflate a within-noise positive.
- Terse format (tables/bullets); `analysis.md` is uncapped but dense.
