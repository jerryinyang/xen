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
3. Per-leg net distribution: mean, median, std, q01/q05/q95/q99, per cell. Where does the money
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
11. Cost sensitivity: at what round-trip cost does the net edge die? How far is that from the
    frozen cost map?
12. For each control read: collapse fraction, not just survive/die. Is the control sensitive to
    the dominant mechanism at all (B-3 shape)?
13. For every headline number: one "what would make this wrong?" probe, executed (e.g. recompute
    under alternative attribution, drop censored legs, split halves).
14. Power (AMENDMENT-7): for any negative, report the row's own CI and — if a floor is shown —
    a same-SE-family floor only (`MDE_Z × bootstrap_SE` of that estimator). Is "no effect"
    distinguishable from "cannot see"? Preflight counts and planning constants are context,
    never a second test on the realised estimate.
15. Channel scales (AMENDMENT-7 R4): does every channel declare its `sigma_denominator`?
    Are two channels with different denominators being ranked on one ladder?
16. Universal floor failure (L-56 diagnostic): did *every* read fail a floor? If so, check
    scale mismatch before writing a null — wrong-scale floors fail all reads.

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
| **Wrong-scale detection floor (L-56 / AMENDMENT-7 / P-28)** | Floor = `k/√n` or planning `MDE_Z` used as pass mark beside bootstrap CI; dual SE per row; channels with different `sigma_denominator` ranked on one ladder; every read "unresolvable" while CIs still speak — check scale before null story |
| **Floor-derived row labels (AMENDMENT-7 R3)** | Any `WASH`/`UNPOWERED`/`CLEARS_FLOOR`/synonym as a *row* verdict from power — report estimate+CI+context only |

---

## `analysis.md` template

```markdown
# Data Analysis: <EXP-ID>

## 1. Integrity gate (blocking)

| Check | Result | Evidence |
|---|---|---|
| Estimand validation (all cells blocking_pass) | PASS/FAIL | results/estimand_validation.json |
| Provenance trace (verdict-bearing columns ≤ t-1) | PASS/FAIL | <file:line rows below> |
| Leak tripwire collapsed + non-vacuous | PASS/FAIL | <control, raw vs destroyed, collapse fraction> |
| Holdout untouched | PASS/FAIL | <evidence> |
| Price-primary (Nautilus emission under fence; STUB attestation = FAIL) | PASS/FAIL | data/nautilus_runs/… |
| T1 spread-scale routing declared + respected | PASS/FAIL | design SPREAD-SCALE-ROUTING block |
| No experiment-local accounting defs | PASS/FAIL | check_no_local_accounting |

<Provenance table: column | inputs & timestamps | ≤ t-1? | file:line>

## 2. Question list
<numbered; every question ANSWERED (§ ref) or UNANSWERED (reason)>

## 3. Evidence FOR the hypothesis
<each item: observation, effect size, CI, n, stratum coverage>

## 4. Evidence AGAINST the hypothesis
<same rigor; includes unpowered-vs-absent distinctions>

## 5. Anomalies & open questions
<unexplained observations; suggested probes; anything the operator should push on>

## 6. Recommended verdict (experiment hypothesis only — NOT final, NOT family)
- Recommendation: SUPPORTED / NOT SUPPORTED / INCONCLUSIVE / WASH (A≈B within noise)
- Driven by: <the 2-3 decisive pieces of evidence>
- Would change if: <what probe/result would flip this>
- Final verdict is the operator's.
```

## Report discipline

- Every number traceable: script path in `analysis_code/` + emission file.
- Effect sizes with CIs, never bare p-values; per-stratum before pooled.
- Symmetric skepticism: a wash is a wash — do not dress A≈B as a refutation, and do not
  inflate a within-noise positive.
- Terse format (tables/bullets); `analysis.md` is uncapped but dense.
