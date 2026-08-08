# Neutrality Standard (binding — INFR-022 directive 2)

Operator directive 2026-08-08 (INFR-022). The neutrality canon extracted from the
chapter-05 SPDR-021/022/023/024 executions — codified here as **binding** language for every
analysis, screen, report, and results artifact in the live programme (all lanes — XENA,
SPDR, EXP). Archive SoT for the extracted source: `archive/chapter-05-voldir-capture-geometry/`.

Sections: N1–N11 (binding text) · PSR pairing · Powering-strip definitions · N6b integrity
scale.

---

## N1 — No-verdict boundary

Every analysis record opens with a boundary statement: it issues no verdict, names no winner,
ranks no arm, claims no tradability/deployability, and gates no companion experiment or
family action. The word "pass" appears only as the literal name of an integrity field
(`blocking_pass`, `row_accounting.pass`), never as a judgement on a measured value.

## N2 — Observed vs inference

Every observation is labelled **observed** (read directly from an emitted artifact) or
**inference** (a mechanism reading of observed numbers that is not itself measured). Mechanism
inferences that change the reading of a number are stated next to the number.

## N3 — Counts and sample-size are context, never gates and never hide rules

No row is dropped, trimmed, top-N pruned, relabelled, promoted, demoted, or omitted from the
report because of its count, its interval width, or any sample-size quantity. Small-count rows
are **always reported next to their counts**. A design may pre-declare a minimum `n` for
*primary-inference language* (e.g. "below design minimum for primary inference") — that tag is
descriptive only; the row, estimate, interval, and `n` still appear. "A wide interval is
reported as a wide interval, not as an absence."

## N4 — Direct comparisons only

Every adaptive/conditioned arm is read against a **pre-specified declared comparator** (the
fixed baseline), never against another adaptive arm and never against a threshold.
Comparisons are direct estimate + uncertainty + counts. No arbitrary threshold, band, or gate
decides anything for any row.

## N5 — Populations named and separated

Every estimate row carries the population it describes (`eligible_origin_n`, `entry_fill_n`,
`close_n`, `common_fill_n`, `common_close_n`, effective blocks) with null (never a borrowed
number) where a population does not apply. Uncertainty is derived from the **matching**
population. Lenses (origin-inclusive vs common-close-trade; scale vs selection) are never
merged, never summed, never ranked on one ladder; per-stratum separation (universe, entry
variant, domain) is never pooled as a headline (pooled = disclosure-only).

## N6 — Controls are informative, gate nothing (value path)

Every control names its population, comparator, estimate, interval, count and effective count;
undefined rows carry an explicit `undefined_reason`. No control converts collapse, sign, or
interval behaviour into pass/fail/supported/refuted language.

## N6b — Validity-path exception (leak tripwire only)

The future-destroying leak tripwire remains the only control class with **blocking** authority
(validity of the emission, not value of the edge). Its integrity bite scale is **not** an MDE,
not a detection floor, and must not use `MDE` / `MDE_Z` / `UNPOWERED` vocabulary. Binding
replacement: a pre-declared **SE-family integrity scale** —

```
integrity_bite = INTEGRITY_Z × bootstrap_SE
```

of the **same estimator** as that control's CI (default `INTEGRITY_Z = 2.8` unless the design
names another constant). Document the constant in the design's integrity section. This is a
validity threshold on a planted leak contrast, not a powering method for research estimands.

## N7 — Symmetric evidence

Observations are reported symmetrically: consistent / contrary-concentrated / unresolved, with
equal rigor on both sides. Each record ends with a "what would make the headline numbers wrong"
section and a hand-off that names probes runnable against the existing emission.

## N8 — Analyst independence

`analysis.md` is written by a fresh-context analyst per experiment, reading raw emissions and
canonical artifacts only; no analyst reads another analyst's prose, no analyst mutates
emissions, no analyst issues an experiment or family verdict. `screen.md` is a neutral
quantification record — run IDs, integrity status, counts, control availability, cost caveat,
links to complete tables — with **no economic conclusion**.

## N9 — Cost caveat on every document

Every money-bearing report, analysis, screen and results artifact carries the zero-cost caveat
(INFR-022 §3.1) verbatim. "Pass" of integrity never implies any economic statement.

## N10 — Completeness

Every stratum, population and row that exists in the emission exists in the report; nothing is
hidden behind a pooled count; reproduction manifests (hash equality of analysis passes) are
persisted where the lane requires them.

## N11 — Value labels are operator-only

Machine code and automated report layers never assign `WASH`, `SUPPORTED`, `REFUTED`,
`CONTRADICTED`, `STRONG`, `SUGGESTIVE`, `UNPOWERED`, or synonyms as row verdicts. The operator
may optionally tag a report layer with plain-language interpretation after reading numbers;
those tags never gate, never drop rows, and never appear as machine fields on emission rows.

---

## PSR pairing (INFR-022 directive 4)

Probabilistic Sharpe Ratio (Bailey & López de Prado, 2012) with the skew/kurtosis-adjusted
variance term, computed from the **same per-trade series and population** as the average trade
(bps) it accompanies:

```
PSR(SR*) = Φ( (SR_hat − SR*) · √(n−1) / √(1 − γ3·SR_hat + (γ4−1)/4 · SR_hat²) )
```

`γ3`/`γ4` = empirical skewness/kurtosis of the per-trade bps series; `SR_hat` = **per-trade**
Sharpe (mean/std of that series — **not annualised**; designs that want an annualised SR must
declare the annualisation and compute PSR from that series instead); `n` = trades in that
population. Empirical moments only — no normality assumption. Default `SR* = 0` (design may
override). **PSR is evidence, never a gate.**

- Pairing rule: wherever a mean trade / mean leg return in bps is reported, `psr` + `psr_n`
  sit beside it, on the SAME series (never borrow another population's n).
- `n < 2` or non-finite moments → `psr = NaN` with `psr_n` stated; row still reported (N3).
- Code: `xen.evaluation.psr` / `psr_row`; XENA report layer `xen.xena.report_layer.psr_layer`.

---

## Powering-strip definitions (INFR-022 directive 3)

**Retained (the only powering-adjacent methods):**

- **Sample-size context.** Designs state expected per-stratum event counts and optional
  minimum-n notes for *primary-inference language*. Per N3/N10: rows are never hidden or
  dropped for low `n`; every row is reported with its count. Sample-size never becomes a
  resolve rule, pass mark, or ranking key.
- **Direct comparison against a pre-specified baseline model.** Estimate + uncertainty +
  counts of arm-vs-fixed-comparator. No threshold is applied to the estimate; the operator
  reads the numbers.

**Stripped (prohibited in live designs, code, artifacts and reports):**

- `MDE`, `mde_bps`/`mde_sigma`, `MDE_Z` (except the renamed validity constant in N6b, which
  must be called `INTEGRITY_Z`, never `MDE_Z`), floors (`2.8/√n`, `MDE_Z × SE` on research
  estimands), mechanism ceilings (`√p × Sharpe`), preflight power labels, power curves /
  end-to-end power calibration, "at power", "resolved/unresolved at this power",
  "below/above detection floor".
- Machine-assigned row labels: `UNPOWERED`, `WASH`, `CLEARS_FLOOR`, `FULLY_RESOLVING`,
  `NOT_RESOLVABLE_AT_THIS_FLOOR`, `CARRIES_MAGNITUDE`, `SUPPORTED`/`REFUTED`/`CONTRADICTED` as
  automated verdicts; band/resolution taxonomies as gates.
- `powered` booleans, `min_powered_seeds` floors, `n_legs_floor` vetoes, `at_or_above_p95`
  booleans, structural `UNPOWERED`/`CONTRADICTED` auto-labels.
- Any power quantity used as a pass mark, resolve rule, or gate on realised estimates.

Interpretation bands (STRONG / SUPPORTED / SUGGESTIVE / WASH and similar) remain
**operator-supplied tags only** under N11 — never machine-assigned, never gating.

**SPDR disposition language.** `INCONCLUSIVE` (or successor wording) means "event count and/or
interval width leave the estimate unresolved for the operator" — descriptive, not a negative
finding and not a hide rule. Characterisation contracts report sample-size metadata (event
count, effective count) as informative only.
