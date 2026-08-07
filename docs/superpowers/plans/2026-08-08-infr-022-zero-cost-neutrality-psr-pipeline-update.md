# INFR-022 — Programme-wide update: zero-cost model, neutrality standard, powering-strip, PSR

> **For agentic workers:** this is the single execution ledger for the update. Tasks use
> checkbox syntax so execution can resume at the first unchecked item. This is a
> **conventions-and-code update**, not an experiment: no Nautilus run, no emission, no
> read, no family action is authorised by this plan. Operator gates: Task 0 (approve
> scope + decisions), Task 5 (review), final sign-off (Task 6).

**Goal:** enforce four operator directives programme-wide (all lanes — XENA, SPDR, EXP):

1. **Zero cost model** — no spread, commission, or swap enters any calculation in any
   experiment type, unless an explicit operator directive requests costs. Every report,
   analysis and results artifact carries the zero-cost caveat.
2. **Neutrality standard** — codify the analysis/report standards extracted from the
   chapter-05 SPDR-021/022/023/024 executions (no labels, no biases, non-gated reports,
   sample-size reduced to informative-only context) as binding skill + spec language.
3. **Complete strip of MDE-type and every other powering method.** Retained methods only:
   sample-size *context* (never a hide/drop rule), and DIRECT comparisons against a
   pre-specified baseline model. No arbitrary thresholds or gates on realised estimates.
4. **PSR** — Probabilistic Sharpe Ratio reported alongside the average-trade (bps) figure
   in all analyses and emissions, on the same trade series and population.

**Authority:** operator directive 2026-08-08 (INFR-022). Supersedes, within the live
programme: the AMENDMENT-7 / L-56 detection-floor apparatus (power floors), the
`PARTIAL_FEES_FUNDING_ONLY` cost scope, `spread_scale_route` T1 decidability routing, the
XENA A-4 dual gate (gross binding + net informational), and the SPDR money-unit floor.
Archived chapter-05 artifacts keep their historical text for reproducibility; live
governance, skills and code are rewritten.

**Skill tree:** edit **only** `.agents/skills/`. `.grok/skills` is a symlink to
`.agents/skills` — do not maintain a second copy.

**Archive SoT:** chapter-05 handoffs and experiment docs under
`archive/chapter-05-voldir-capture-geometry/` are the neutrality source of truth.
Copies under `docs/superpowers/plans/` are convenience mirrors only.

---

## 0. Sources of truth read before this plan

| Source | Used for |
|---|---|
| `archive/chapter-05-.../superpowers/plans/2026-07-30-spdr-021-023-stages-8-execution-handoff.md` | neutrality directives: non-gated reads, no labels, all strata visible, population separation, fresh-context analysts, controls informative |
| `archive/chapter-05-.../superpowers/plans/2026-08-07-spdr-024-mde-floor-fix-execution-handoff.md` | AMENDMENT-7 R1–R5 (now superseded), label ban, floor honesty, preflight discipline, Claude-review gate pattern |
| `archive/chapter-05-.../experiments/SPDR-021..024/design.md` (4) | SPREAD-COST-DISCLOSURE block, POWER-as-context declarations, fixed-comparator design |
| `archive/chapter-05-.../experiments/SPDR-021..024/analysis.md` (4) | the neutrality standard in its realised form (§1 below) |
| `_pipeline-config.md`, all pipeline skills + `quant-designer/references/design-requirements.md`, `data-analyst/references/interrogation-protocol.md`, `research-pipeline/references/governance-constraints.md` | live text to rewrite |
| `python/src/xen/evaluation.py`, `adjudication.py`, `estimand_validation.py`, `nautilus/adjudication_shim.py`, `xen/xena/*.py` | live cost + MDE machinery to retire/rewrite |
| `docs/references/{xena-lane,spdr-lane,architecture,dataset-reference,chapter-06-governance}.md` | live specs to rewrite |
| `docs/knowledge-base/{INDEX,evaluation-framework,lessons-and-amendments,pitfalls-ledger,methodology-canon}.md`, `docs/knowledge-base/memory/*`, `docs/experiments-docs/INDEX.md` | canon + memory updates |
| `chapter-rollover/references/extract-checklist.md` | stop freezing MDE maps into chapter extract |

---

## 1. The neutrality standard (directive 2 — extracted canon, to be codified verbatim)

Extracted from the four chapter-05 analysis records and both execution handoffs. This is
the **binding text** for the new `docs/references/neutrality-standard.md` and for the
skill updates:

**N1 — No-verdict boundary.** Every analysis record opens with a boundary statement:
it issues no verdict, names no winner, ranks no arm, claims no tradability/deployability,
and gates no companion experiment or family action. The word "pass" appears only as the
literal name of an integrity field (`blocking_pass`, `row_accounting.pass`), never as a
judgement on a measured value.

**N2 — Observed vs inference.** Every observation is labelled **observed** (read directly
from an emitted artifact) or **inference** (a mechanism reading of observed numbers that is
not itself measured). Mechanism inferences that change the reading of a number are stated
next to the number.

**N3 — Counts and sample-size are context, never gates and never hide rules.** No row is
dropped, trimmed, top-N pruned, relabelled, promoted, demoted, or omitted from the report
because of its count, its interval width, or any sample-size quantity. Small-count rows
are **always reported next to their counts**. A design may pre-declare a minimum `n` for
*primary-inference language* (e.g. "below design minimum for primary inference") — that
tag is descriptive only; the row, estimate, interval, and `n` still appear. "A wide
interval is reported as a wide interval, not as an absence."

**N4 — Direct comparisons only.** Every adaptive/conditioned arm is read against a
**pre-specified declared comparator** (the fixed baseline), never against another adaptive
arm and never against a threshold. Comparisons are direct estimate + uncertainty +
counts. No arbitrary threshold, band, or gate decides anything for any row.

**N5 — Populations named and separated.** Every estimate row carries the population it
describes (`eligible_origin_n`, `entry_fill_n`, `close_n`, `common_fill_n`,
`common_close_n`, effective blocks) with null (never a borrowed number) where a population
does not apply. Uncertainty is derived from the **matching** population. Lenses
(origin-inclusive vs common-close-trade; scale vs selection) are never merged, never
summed, never ranked on one ladder; per-stratum separation (universe, entry variant,
domain) is never pooled as a headline (pooled = disclosure-only).

**N6 — Controls are informative, gate nothing (value path).** Every control names its
population, comparator, estimate, interval, count and effective count; undefined rows
carry an explicit `undefined_reason`. No control converts collapse, sign, or interval
behaviour into pass/fail/supported/refuted language.

**N6b — Validity-path exception (leak tripwire only).** The future-destroying leak
tripwire remains the only control class with **blocking** authority (validity of the
emission, not value of the edge). Its integrity bite scale is **not** an MDE, not a
detection floor, and must not use `MDE` / `MDE_Z` / `UNPOWERED` vocabulary. Binding
replacement: a pre-declared **SE-family integrity scale** —
`integrity_bite = INTEGRITY_Z × bootstrap_SE` of the **same estimator** as that control's
CI (default `INTEGRITY_Z = 2.8` unless the design names another constant). Document the
constant in the design's integrity section. This is a validity threshold on a planted
leak contrast, not a powering method for research estimands.

**N7 — Symmetric evidence.** Observations are reported symmetrically: consistent /
contrary-concentrated / unresolved, with equal rigor on both sides. Each record ends
with a "what would make the headline numbers wrong" section and a hand-off that names
probes runnable against the existing emission.

**N8 — Analyst independence.** `analysis.md` is written by a fresh-context analyst per
experiment, reading raw emissions and canonical artifacts only; no analyst reads another
analyst's prose, no analyst mutates emissions, no analyst issues an experiment or family
verdict. `screen.md` is a neutral quantification record — run IDs, integrity status,
counts, control availability, cost caveat, links to complete tables — with **no economic
conclusion**.

**N9 — Cost caveat on every document.** Every money-bearing report, analysis, screen and
results artifact carries the zero-cost caveat (directive 1 text, §3.1). "Pass" of
integrity never implies any economic statement.

**N10 — Completeness.** Every stratum, population and row that exists in the emission
exists in the report; nothing is hidden behind a pooled count; reproduction manifests
(hash equality of analysis passes) are persisted where the lane requires them.

**N11 — Value labels are operator-only.** Machine code and automated report layers never
assign `WASH`, `SUPPORTED`, `REFUTED`, `CONTRADICTED`, `STRONG`, `SUGGESTIVE`,
`UNPOWERED`, or synonyms as row verdicts. The operator may optionally tag a report layer
with plain-language interpretation after reading numbers; those tags never gate, never
drop rows, and never appear as machine fields on emission rows.

---

## 2. Directive 3 — what "powering strip" means (binding definitions)

**Retained (the only powering-adjacent methods):**

- **Sample-size context.** Designs state expected per-stratum event counts and optional
  minimum-n notes for *primary-inference language*. Per N3/N10: rows are **never** hidden
  or dropped for low `n`; every row is reported with its count. Sample-size never becomes
  a resolve rule, pass mark, or ranking key.
- **Direct comparison against a pre-specified baseline model.** Estimate + uncertainty +
  counts of arm-vs-fixed-comparator, as in the SPDR-021/022/023/024 shape. No threshold is
  applied to the estimate; the operator reads the numbers.

**Stripped (prohibited in live designs, code, artifacts and reports):**

- `MDE`, `mde_bps`/`mde_sigma`, `MDE_Z` (except the renamed validity constant in N6b,
  which must be called `INTEGRITY_Z`, never `MDE_Z`), floors (`2.8/√n`, `MDE_Z × SE` on
  research estimands), mechanism ceilings (`√p × Sharpe`), preflight power labels, power
  curves / end-to-end power calibration, "at power", "resolved/unresolved at this power",
  "below/above detection floor".
- Machine-assigned row labels: `UNPOWERED`, `WASH`, `CLEARS_FLOOR`, `FULLY_RESOLVING`,
  `NOT_RESOLVABLE_AT_THIS_FLOOR`, `CARRIES_MAGNITUDE`, `SUPPORTED`/`REFUTED`/`CONTRADICTED`
  as automated verdicts; band/resolution taxonomies as gates.
- `powered` booleans, `min_powered_seeds` floors, `n_legs_floor` vetoes, `at_or_above_p95`
  booleans (already retired), structural `UNPOWERED`/`CONTRADICTED` auto-labels.
- Any power quantity used as a pass mark, resolve rule, or gate on realised estimates.

Interpretation bands (STRONG / SUPPORTED / SUGGESTIVE / WASH and similar) remain **operator-
supplied tags only** under N11 — never machine-assigned, never gating (INFR-016 retained,
minus power labels and machine structural labels).

**SPDR disposition language.** `INCONCLUSIVE` (or successor wording) means "event count
and/or interval width leave the estimate unresolved for the operator" — descriptive, not
a negative finding and not a hide rule. Characterisation contracts report sample-size
metadata (event count, effective count) as informative only.

---

## 3. Directive 1 — zero-cost model (binding definitions)

### 3.1 Canonical caveat text (must appear verbatim on every report/analysis/results doc)

```text
ZERO-COST-DISCLOSURE
  cost_model: NO_COST_CHARGED
  spread: not modeled
  commissions: not modeled
  swaps/funding: not modeled
  implication: every figure in this document is gross and cost-free; no spread,
    commission, or swap enters any calculation. Realised results would differ
    (likely worse) under any real cost schedule.
  prohibited_claims: fully-net, cost-complete, tradable, deployable
  lifting: only an explicit operator directive may introduce a cost model for a
    scoped experiment; the directive is recorded in that experiment's design.md.
```

### 3.2 Semantics

- All three lanes (XENA, SPDR, EXP) default to zero cost. No cost function is called in any
  live path; `cost_bps`/`charge_costs`/`spread_*` parameters are inert (pinned 0 / False)
  and enforced by code asserts where they exist.
- "Zero" is a *model*, not a measurement: absence of cost is not represented as
  "measured zero cost" anywhere; the caveat text above is mandatory instead.
- A cost directive is experiment-scoped: it may not be inferred from any other
  experiment's directive, and it is recorded in the design before execution (QA traces it).
- Deployability/tradability claims remain refused by rule (unchanged) — the zero-cost
  model does not loosen them.

### 3.3 XENA economics integrity contract (before → after)

Highest-risk inversion. Live `xen.xena.economics` currently treats **`cost_bps == 0` as
placeholder incomplete** and refuses search until non-zero pins exist under
`PROGRAMME_COST_SCOPE = PARTIAL_FEES_FUNDING_ONLY`. That logic is replaced wholesale.

| Surface | Before (live) | After (INFR-022) |
|---|---|---|
| Default cost model | Partial fees/funding; spread never charged | `NO_COST_CHARGED` — nothing charged |
| `cost_bps == 0` | Incomplete (placeholder) → search refused | **Compliant** (zero-cost pin) |
| `cost_bps` missing / non-finite | Incomplete | Incomplete **or** treat as 0 if field absent and model is zero-cost (prefer: absent allowed when `cost_model=NO_COST_CHARGED`) |
| `cost_bps > 0` without directive | Allowed / required for search | **Refuse** search/gate unless `operator_cost_directive` present + design clause |
| `cost_scope` | Must be `PARTIAL_FEES_FUNDING_ONLY` or undeclared | Must be absent, `NO_COST_CHARGED`, or `ZERO_COST_MODEL`; any fees/funding/spread scope without directive → refuse |
| `money_per_unit` | Required finite > 0 | **Still required** (position sizing / capital units — not a cost) |
| Function name | `check_cost_map_integrity` | `check_zero_cost_compliance` (keep thin alias that calls the new check if tests need a transition) |
| Constant | `PROGRAMME_COST_SCOPE = PARTIAL_FEES_FUNDING_ONLY` | `ZERO_COST_MODEL` / `NO_COST_CHARGED` |
| Net-from-pin disclosure | `gross_mean_bps - cost_bps_pin` | **Removed** from default path; gross-only disclosure; net block only under directive |
| Routing strings | `proceed_deployability_search`, characterisation_only, do_not_search | Reword: e.g. `proceed_search`, `characterisation_only`, `do_not_search` — **no deployability language** |
| Search/gate precondition | Complete non-placeholder cost map | Zero-cost compliance (or directive-backed cost map) |
| Artifacts | economics disclosure with cost pins | Carry `cost_model: NO_COST_CHARGED` + zero-cost caveat fields |

Manifests that still pin non-zero fees without a directive fail compliance. Fixtures that
already ship `cost_bps=0` become the normal case.

### 3.4 Cost directive mechanism

- Design clause in `design.md` naming the directive, functions, and scope.
- Run-dir file `operator_cost_directive.json` (operator-signed reason string + scope).
- QA traces both. Estimand `--cost-bps != 0` fails without the file. Oracle
  `charge_costs=True` raises without the directive object/path.

---

## 4. Directive 4 — PSR (binding definitions)

### 4.1 Definition

Probabilistic Sharpe Ratio (Bailey & López de Prado, 2012) with the skew/kurtosis-adjusted
variance term, computed from the **same per-trade series and population** as the average
trade (bps) it accompanies:

`PSR(SR*) = Φ( (SR_hat − SR*) · √(n−1) / √(1 − γ3·SR_hat + (γ4−1)/4 · SR_hat²) )`

where `γ3`/`γ4` are empirical skewness/kurtosis of the per-trade bps series, `SR_hat` the
**per-trade** Sharpe (`mean/std` of that series — **not annualised**; designs that want an
annualised SR must declare the annualisation and compute PSR from that series instead),
`n` the number of trades in that population. Empirical moments only — no normality
assumption. Default `SR* = 0` (design may override). PSR is **evidence, never a gate**.

`n < 2` or non-finite moments → `psr = NaN` with `psr_n` stated; row still reported (N3).

### 4.2 Pairing rule

Wherever a mean trade / mean leg return in **bps** is reported, PSR + `n` sit beside it:

| Lane / surface | Mean column (existing or alias) | PSR columns |
|---|---|---|
| Generic analysis tables | `avg_trade_bps` (canonical name when writing new columns) | `psr`, `psr_n` |
| XENA economics / fill_basis | `gross_mean_bps` (keep name; pair in-place) | `psr`, `psr_n` |
| XENA report layers | observed mean on the layer | via `psr_layer` |
| Estimand validation | `gross_mean_bps` / physicality means | `psr_summary` block |
| SPDR analysis parquets / device tables | whatever mean-bps column the design already emits for that population | `psr`, `psr_n` on the same row |
| EXP / shared adjudication | mean of `RealizedBps` (or NetBps only under directive) | `psr`, `psr_n` |

**Series identity:** PSR uses the exact vector that produced the mean (same population mask:
e.g. common-close trades for a common-close mean; never borrow another population's `n`).

**Sample-size note:** always emit `psr` + `psr_n` when the mean is emitted; if `n` is below
a design minimum, still emit numbers (or NaN) and counts — do not suppress PSR to imply
absence (N3).

### 4.3 Code location

- `xen.evaluation.psr(per_trade_bps, *, sr_star=0.0) -> {"psr", "n", "sr_hat", "skew", "kurt"}`
- `psr_row(...)` helper for dataframe / dict rows.
- `xen.xena.report_layer.psr_layer(candidate_id, *, avg_trade_bps, psr, n)`.

### 4.4 Emission vs analysis

- Prefer computing PSR at **analysis / report** time from the trade vector so emission
  schemas stay thin.
- Where an emission already materialises a mean-bps column without the trade vector
  downstream, also materialise `psr` + `psr_n` at emission (experiment-developer contract).
- Task 4 smoke must cover: (1) unit tests on `psr()`, (2) XENA report-layer pairing on
  `gross_mean_bps`, (3) at least one synthetic multi-row analysis artifact with
  mean + `psr` + `psr_n` aligned.

---

## 5. Workstream A — Code changes (`python/src/xen/`)

> All changes TDD: failing test first, minimum fix, regression pass. Full suite must stay
> green; archive-frozen modules are untouched. Forward-only: never re-run or rewrite
> archived chapter emissions.

### Caller inventory (must stay green or be updated)

| Symbol / behaviour | Primary callers |
|---|---|
| `mde`, `powered_label`, cost helpers | `evaluation.py`; `tests/test_evaluation.py` |
| `spread_scale_route` | `tests/test_estimand_validation_v2.py` |
| `bybit_round_trip_cost_bps` | `xena/calibration_bybit.py`, `calibration_bybit15.py`; tests |
| `power_layer`, `structural_label` | `report_layer.py`, `controls.py`, `tests/test_xena_infr016.py` |
| `min_powered_seeds` | `controls.py` + infr016 tests |
| `check_cost_map_integrity` / economics | `search.py`, `tests/test_xena_economics.py`, infr009 |
| `charge_costs=True` | `oracle.py` default; `certify.py` net_cfg; `final_gate.py` NET run; `calibration_p3b/p3d`; `tests/test_xena_infr015.py`, fold-parity corpus, oracle/final_gate tests |
| `cost_bps` assemble path | `adjudication.py`, `estimand_validation.py`, `nautilus/adjudication_shim.py` |
| `NetMoney` / `net=True` score | `score.py`, certify companion |

### Tasks

- [ ] **A1 `evaluation.py`**
  - [ ] A1.1 Remove `mde()`, `powered_label()`; remove `cost_sensitivity()` (cost reads
        retired; `block_sensitivity` stays as dependence read). Module docstring:
        "informative evidence only; no MDE; no cost; PSR + sample-size context only".
  - [ ] A1.2 Move cost constants/functions to `xen/evaluation_cost_legacy.py` with banner
        "ARCHIVED — not callable from any live research path; only an operator cost
        directive may re-enable, and the directive must be recorded":
        `FTMO_COSTS`, `round_trip_cost_bps`, `usd_notional_per_lot`, `BYBIT_USDT_PERP_FEES`,
        `BYBIT_FUNDING_CONSERVATIVE_BPS_PER_8H`, `bybit_fee_bps_per_side`,
        `count_bybit_funding_stamps`, `t1_round_trip_spread_bps`,
        `SPREAD_SCALE_ROUTING_MULTIPLIER`, `spread_scale_route`,
        `bybit_round_trip_cost_bps`. Keep `verify_chapter05_spread_quarantine` in live
        evaluation (data provenance).
  - [ ] A1.3 Add `ZERO_COST_DISCLOSURE` dict + `zero_cost_caveat()` (text §3.1) +
        `assert_zero_cost(**kwargs)` raising if any cost parameter ∉ {0, None, False}.
  - [ ] A1.4 Add `psr` + `psr_row` (§4); tests: normal series → PSR ≈ Φ(√(n−1)·SR̂), n<2 →
        NaN, skew/kurt correction sign, determinism, same-series pairing helper.
- [ ] **A2 `adjudication.py` + `nautilus/adjudication_shim.py`** — keep `cost_bps` parameter
      for API stability; live callers pass 0; docstring zero-cost model; add
      `check_no_cost_charged(positions, cis)` for non-zero commission/cost columns;
      shim defaults `cost_bps=0` and asserts under §3.2.
- [ ] **A3 `estimand_validation.py`**
  - [ ] A3.1 `--cost-bps` default 0; non-zero requires `operator_cost_directive` in run dir.
  - [ ] A3.2 Blocking check `no_cost_charged` (non-zero fee/commission columns → fail);
        HARD inventory + count reconciliation.
  - [ ] A3.3 Optional informative `psr_summary` beside gross means (§4).
- [ ] **A4 `xena/oracle.py`** — `charge_costs` default **`False`**; `True` raises unless
      directive; docstring: gross selection and gross gate only. Update every in-repo
      caller that passed `True` (certify, final_gate, calibration_p3*, tests, fold corpus).
- [ ] **A5 `xena/economics.py`** — implement §3.3 contract exactly:
      `check_zero_cost_compliance`, `ZERO_COST_MODEL` / `NO_COST_CHARGED`, drop
      placeholder-zero refusal, refuse non-zero without directive, keep `money_per_unit`
      validation, remove default net-from-pin, reword routing (no deployability).
- [ ] **A6 `xena/search.py`** — call zero-cost compliance; refuse with clear error text.
- [ ] **A7 `xena/certify.py`** — remove NET companion (`net_cfg` / `charge_costs=True`);
      gross evidence package only; artifact `cost_model: NO_COST_CHARGED`.
- [ ] **A8 `xena/score.py`** — remove `net=True` / `NetMoney` score path; keep `g_gross_*`.
- [ ] **A9 `xena/final_gate.py`** — remove NET informational run (A-4 dual gate retired);
      single gross gate; `cost_model: NO_COST_CHARGED`; keep operator-facing `passed`
      field (D5).
- [ ] **A10 `xena/ingest.py`, `xena/high_cadence_null.py`** — `cost_bps` default 0 + assert.
- [ ] **A11 `xena/report_layer.py`**
  - [ ] A11.1 Replace `power_layer` with `sample_size_layer` (n_legs, per-leg vol, design
        minimum-n **note** — no MDE, no `powered` boolean, no UNPOWERED label, no hide).
  - [ ] A11.2 Delete `structural_label` and machine auto-assignment. Document operator-only
        tags under N11 (STRONG/SUPPORTED/SUGGESTIVE/WASH may exist as free-text operator
        tags only — never machine fields).
  - [ ] A11.3 Add `psr_layer` (§4).
- [ ] **A12 `xena/controls.py`** — `sign_battery`: drop `min_powered_seeds` / `powered` /
      `structural_label`; report effect + one-sided p + CI + n only;
      `attribution_derangement` unchanged.
- [ ] **A13 Calibration modules**
  - [ ] A13.1 `calibration_bybit.py` / `calibration_bybit15.py`: **rewire imports** of
        `bybit_round_trip_cost_bps` to `evaluation_cost_legacy` (or stop calling and hard-
        pin zero under banner). Banner: legacy CAL apparatus; not bindable on live research
        path without a post-INFR-022 CAL redesign. Do not leave broken imports.
  - [ ] A13.2 Other `calibration*.py`: banners for power-curve / MDE content; any live
        import of removed symbols fixed.
- [ ] **A14 Tests (full blast radius)** — update at least:
      `test_evaluation.py`, `test_estimand_validation_v2.py`, `test_xena_economics.py`,
      `test_xena_infr009.py`, `test_xena_infr015.py`, `test_xena_infr016.py`,
      `test_xena_final_gate.py`, `test_xena_oracle.py`, `test_xena_fold_parity.py`,
      `test_xena_p3b.py`, `test_xena_p3d.py`, `gen_xena_fold_parity_corpus.py` as needed.
      New tests: zero-cost compliance, non-zero-without-directive refusal, PSR unit +
      pairing, sample_size_layer, no-cost estimand check, final_gate single-run artifact.
      Full suite + ruff + `git diff --check` green.

---

## 6. Workstream B — Skills (`.agents/skills/` only)

`.grok/skills` → symlink; edit this tree once.

- [ ] **B1 `research-pipeline/_pipeline-config.md`**
  - [ ] §Data architecture: T1 lane cell → zero-cost model + caveat on every report.
  - [ ] Add binding § *Zero-cost model* (§3.1) and § *Neutrality standard* (link
        `docs/references/neutrality-standard.md`, N1–N11 binding).
  - [ ] Analysis modules table: drop MDE/UNPOWERED/cost curves/floors; add PSR +
        `evaluation_cost_legacy` archived; XENA: `sample_size_layer`, single gross gate,
        zero-cost economics.
  - [ ] INFR-016 value-read list: remove cost floor, leg-power MDE, cost/funding
        sensitivity, spread-scale routing, net deployability → sample-size layer + PSR +
        gross-only reads.
  - [ ] Programme principles: Cost lines + PSR empirical-moments note.
- [ ] **B2 `research-pipeline/SKILL.md` + `references/governance-constraints.md`**
  - [ ] Hard-constraints: zero-cost + neutrality N1–N11; SPDR money-unit floor retired;
        XENA single gross gate.
  - [ ] Governance-constraints: replace MDE/unpowered honesty rows with sample-size
        context + direct baseline comparison + N6b integrity scale language.
- [ ] **B3 `quant-designer/SKILL.md` + `references/design-requirements.md` + `methods-catalog.md`**
  - [ ] §6 → **Sample-size statement**: expected counts, optional minimum-n for
        primary-inference language (never hide), declared fixed comparator; no MDE/Z/floors.
  - [ ] §5 bands: operator tags only (N11); remove machine `unpowered` band.
  - [ ] §4 control validity: non-vacuity + sufficient statistic must move; N6b for leak
        tripwire (`INTEGRITY_Z × bootstrap_SE`); no research MDE.
  - [ ] §10 → ZERO-COST-DISCLOSURE (§3.1); §11 cost interpretation → cost-directive clause.
  - [ ] XENA constraints: zero-cost + PSR in analysis plan.
  - [ ] methods-catalog: remove MDE methods; add PSR; keep bootstrap CI, block-sensitivity,
        trimmed mean, collapse fraction.
- [ ] **B4 `data-analyst/SKILL.md` + `references/interrogation-protocol.md`**
  - [ ] Bind N1–N11 as the analysis contract. Replace Detection floors (AMENDMENT-7) with
        **§ Sample-size + direct comparison**: always report n/effective n; never hide rows;
        every estimate vs declared fixed comparator; no floor/MDE/Z on value path; no
        machine-assigned WASH/UNPOWERED/CLEARS_FLOOR (operator tags only, N11).
  - [ ] Phase 1: zero-cost verification + PSR pairing question (PSR + n beside every mean
        trade/leg bps read, same series).
  - [ ] Phase 0: `no_cost_charged` on integrity gate list.
  - [ ] Template: §0 boundary (N1), observed/inference, symmetric sections, "what would
        make these numbers wrong", probe hand-off.
  - [ ] `power_layer` → `sample_size_layer`; sign_battery without min_powered; PSR layer.
- [ ] **B5 `qa-compliance/SKILL.md`** — ZERO-COST-DISCLOSURE present; no live
      `PARTIAL_FEES_FUNDING_ONLY`; no research MDE/power clauses (denylist §10); PSR
      pairing in analysis plan; cost-directive when costs requested; F07 → sample-size
      notes only (never hide).
- [ ] **B6 `experiment-developer/SKILL.md`** — zero-cost in-engine and analysis; emissions
      carry `cost_model: NO_COST_CHARGED`; PSR columns when mean-bps is materialised without
      a recoverable trade vector.
- [ ] **B7 `experiment-documenter/SKILL.md`** — report template: zero-cost caveat + PSR
      beside mean-bps tables; N1/N7/N9; verdict remains operator's.
- [ ] **B8 `chapter-rollover/references/extract-checklist.md`** — evaluation-framework
      extract: freeze sample-size + direct-comparison + PSR + zero-cost; **do not** freeze
      per-domain MDE maps as live apparatus (historical mention only).

---

## 7. Workstream C — Specs and knowledge base (`docs/`)

- [ ] **C1 NEW `docs/references/neutrality-standard.md`** — N1–N11 + PSR pairing + §2
      powering-strip definitions + N6b integrity scale.
- [ ] **C2 `docs/references/xena-lane.md`** — Cost policy → zero-cost + §3.3; A-4 dual gate
      → single gross; retire `spread_scale_route`; leg-power → sample_size_layer; CAL power
      table → historical note; PSR; INFR-016 list.
- [ ] **C3 `docs/references/spdr-lane.md`** — remove money-unit floor + cost-floor
      graduation; disposition language per §2; sample-size metadata informative only;
      delete per-stratum UNPOWERED; add N1–N11 + PSR to analyst stage.
- [ ] **C4 `docs/references/architecture.md`** — zero-cost model; T1 cell; directive
      mechanism.
- [ ] **C5 `docs/references/dataset-reference.md`** — zero-cost + directive; keep
      mean-price-skew quarantine (provenance, not cost).
- [ ] **C6 `docs/references/chapter-06-governance.md`** — §2 → zero-cost (§3.1); remove
      live power-plan / block-MDE standing rules; add neutrality + PSR; leave
      AMENDMENT-S1 etc. untouched.
- [ ] **C7 `docs/references/chapter-05-cost-data-preflight.md` + `...-qa.md`** — add top
      banner: **HISTORICAL (chapter-05)** — not binding on live programme after INFR-022;
      do not use as cost policy. Do not rewrite body (reproducibility).
- [ ] **C8 `docs/knowledge-base/evaluation-framework.md`** — Detection floors → Sample-size
      requirements and direct comparison; MDE content flagged legacy; PSR documented.
- [ ] **C9 `docs/knowledge-base/methodology-canon.md`** — align cost + powering language
      with this plan; historical clauses marked superseded-for-live-use.
- [ ] **C10 `docs/knowledge-base/lessons-and-amendments.md`** — **L-62** zero-cost model;
      **L-63** powering reduced to sample-size context + direct baseline comparison;
      **L-64** PSR standard; **L-65** neutrality N1–N11. Mark L-56 / AMENDMENT-7
      superseded-for-live-use (history retained under `historical:` framing).
- [ ] **C11 `docs/knowledge-base/pitfalls-ledger.md`** — rows: re-introducing MDE as row
      floor/resolve rule; charging cost without directive; missing zero-cost caveat;
      machine-assigned value/power labels; hiding rows for low n.
- [ ] **C12 `docs/knowledge-base/memory/`** — update `MEMORY.md`,
      `detection-floor-must-share-scale.md`, `unit-pin-money-floor.md`,
      `frozen-suite-floors.md`: supersession banners pointing at L-62..65 and this plan;
      live instruction = zero-cost + sample-size context + direct comparison + PSR.
      Do not leave active "must use MDE floor" memory without a historical tag.
- [ ] **C13 `docs/knowledge-base/INDEX.md` + `docs/experiments-docs/INDEX.md`** — standing
      constraints: zero-cost + no research powering + PSR + neutrality; INFR-022 row.
- [ ] **C14 `python/experiments/INDEX.md`** — infra row for INFR-022.

---

## 8. Operator decisions (locked defaults — Task 0 confirms)

| # | Decision | Locked default (operator-approved 2026-08-08 review) |
|---|---|---|
| D1 | INFR-022 ID + plan acceptance | Accept as INFR-022 |
| D2 | Cost functions in `evaluation.py` | **Move** to `evaluation_cost_legacy.py` (reproducibility; FTMO/EXP-019 evidence) |
| D3 | CAL power curves / cost stack | **Banner + rewire imports** to legacy module (or hard-pin zero); full strip deferred to next CAL design |
| D4 | PSR reference Sharpe | `SR* = 0` default; design may override |
| D5 | XENA final gate `passed` field | **Keep** (operator-facing gate artifact); remove only NET costed leg |
| D6 | Cost directive mechanism | **File** `operator_cost_directive.json` **+** design.md clause |
| D7 | Small-n rows | **Always show** with counts; sample-size tags descriptive only (N3/N10) |
| D8 | Skill trees | Edit **`.agents/skills` only** (`.grok/skills` is symlink) |
| D9 | Value labels (WASH etc.) | **Operator-only** (N11); never machine-assigned; denylist targets machine-assignment patterns, not the bare word in N11 docs |
| D10 | Integrity tripwire scale | **N6b**: `INTEGRITY_Z × bootstrap_SE` (same SE family); not called MDE |
| D11 | PSR series + annualisation | Per-trade series matching the reported mean; **not annualised** by default; columns `psr` + `psr_n` beside the mean column used on that surface |

Task 0 is confirmation of this locked table, not an open design session — reopen only if
the operator rejects a row.

---

## 9. Execution order and gates

```
Task 0 ... operator confirms D1–D11 locked table (GATE)
Task 1 ... code workstream A (TDD; economics §3.3 first or with oracle default flip)
           → verify: full pytest + ruff + git diff --check
Task 2 ... skills workstream B (.agents/skills only)
           → verify: denylist clean under allowlist rules (§10)
Task 3 ... specs/KB workstream C
           → verify: denylist + historical banners on chapter-05 preflight + memory
Task 4 ... PSR end-to-end smoke (§4.4): unit + XENA layer + synthetic analysis artifact
           → verify: mean and psr/psr_n co-present, same n
Task 5 ... operator review of diff + boundary searches (GATE)
Task 6 ... sign-off; L-62..65; indexes; commit (GATE)
```

**Ordering rules:** code (A) first — skills/docs cite final symbols. Skills (B) before
specs (C). Within A: prefer A1 → A5/A4 (zero-cost + charge_costs default) before final_gate
/ certify / score NET removal so tests fail for the right reason. PSR smoke (Task 4) before
sign-off.

**Risk order (highest first):** (1) economics integrity inversion §3.3, (2) oracle
`charge_costs` default + certify/final_gate NET removal, (3) evaluation symbol moves +
calibration import rewires, (4) report_layer / controls label strip, (5) docs/skills sweep.

**Effort sketch:** ~15–25 code/test files, ~12–18 skill/reference files, ~15 doc/KB files,
1 new neutrality standard. Expect one full-suite iteration after economics + oracle.

---

## 10. Verification and boundary searches

```bash
# after Task 1
cd python && PYTHONPATH=. .venv/bin/pytest tests -q \
  && .venv/bin/ruff check src/xen tests \
  && git diff --check

# after Tasks 2–3 — live denylist (machine / policy vocabulary)
# NOTE: do not use a bare "wash" token — N11 docs may mention WASH as operator-only.
rg -n -i \
  'mde_z|\bmde\b|powered_label|power_layer|clears_floor|fully_resolving|not_resolvable_at_this_floor|min_powered_seeds|n_legs_floor|at_or_above_p95|PARTIAL_FEES_FUNDING_ONLY|spread_scale_route|bybit_round_trip_cost_bps|round_trip_cost_bps|money-unit floor|cost floor|proceed_deployability' \
  .agents/skills docs/references docs/knowledge-base docs/experiments-docs python/src/xen python/experiments/INDEX.md \
  --glob '!**/__pycache__/**'
```

**Allowlist (expected residual hits — must be one of):**

1. Explicit `historical:` / `HISTORICAL (chapter-05)` / `superseded-for-live-use` banners
   and the body under those banners (lessons L-56, chapter-05 preflight docs, memory
   supersession notes).
2. Legacy module banners in `evaluation_cost_legacy.py` and calibration banners listing
   retired names.
3. This plan and `neutrality-standard.md` forbidden-vocabulary lists.
4. N6b / N11 prose that names retired terms only to ban them.

Any other hit → fix in Task 2/3 before sign-off.

```bash
# PSR pairing spot-check (test or small script): every analysis/report surface that emits
# a mean-bps field also emits psr + psr_n with matching n
```

**Determinism:** PSR and zero-cost asserts are pure; no new RNG. Existing determinism
guarantees unchanged.

---

## 11. Stop conditions

1. Any live experiment/emission would be invalidated by a code change → keep the change
   forward-only; never re-run archived chapters.
2. Full test suite not green after Task 1.
3. Denylist finds a live hit outside the §10 allowlist that is not fixed in Task 2/3.
4. Skill text contradicts code reality (e.g. PSR function name mismatch) — fix the wrong
   one; do not ship both.
5. Operator rejects a locked D1–D11 row — amend this plan and stop.
6. Economics §3.3 contract incomplete (e.g. zero still refused, or non-zero still allowed
   without directive) — do not proceed to Task 2.

---

## 12. Appendix — key paths

```text
Plan:            docs/superpowers/plans/2026-08-08-infr-022-zero-cost-neutrality-psr-pipeline-update.md
New standard:    docs/references/neutrality-standard.md
Code:            python/src/xen/evaluation.py | evaluation_cost_legacy.py (new)
                 adjudication.py | nautilus/adjudication_shim.py | estimand_validation.py
                 xena/{oracle,economics,search,certify,score,final_gate,ingest,
                 high_cadence_null,report_layer,controls,calibration*}.py
Skills (only):   .agents/skills/   # .grok/skills → symlink here
                 research-pipeline/{SKILL.md,_pipeline-config.md,references/governance-constraints.md}
                 quant-designer/{SKILL.md,references/design-requirements.md,methods-catalog.md}
                 data-analyst/{SKILL.md,references/interrogation-protocol.md}
                 qa-compliance | experiment-developer | experiment-documenter
                 chapter-rollover/references/extract-checklist.md
Specs/KB:        docs/references/{neutrality-standard,xena-lane,spdr-lane,architecture,
                 dataset-reference,chapter-06-governance,chapter-05-cost-data-preflight*}.md
                 docs/knowledge-base/{evaluation-framework,methodology-canon,
                 lessons-and-amendments,pitfalls-ledger,INDEX,memory/*}.md
                 docs/experiments-docs/INDEX.md | python/experiments/INDEX.md
Archive SoT:     archive/chapter-05-voldir-capture-geometry/
```
