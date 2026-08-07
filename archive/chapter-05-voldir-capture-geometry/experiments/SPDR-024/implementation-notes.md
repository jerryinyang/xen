# SPDR-024 — implementation notes

Written by the implementer. This file records **judgement calls, measured facts and out-of-scope
observations**. It issues no verdict, ranks no arm and makes no tradability claim. Where a design
clause admitted more than one reading, the reading taken is stated here with the clause that settles
it, so the operator can ratify or overturn it.

```text
SPREAD-COST-DISCLOSURE (carried unchanged)
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

---

## 1. Judgement calls, and what settles each

### 1.1 The PRIMARY estimand's denominator is a fixed unit-capital base

Design §3 writes the denominator as "capital committed to that episode at entry (`risk_size` ×
notional at fill)". Read literally, that denominator scales with `risk_size` exactly as the numerator
does, so the two cancel and the estimand reduces to per-notional bps — reproducing the **structural
zero this experiment exists to escape** (the paired SIZE outcome delta was exactly `0.000000` on
1,400/1,400 rows in all six Step-3 cells).

**What settles it:** design §14 trace 1 is hand-derived and unambiguous — the halved arm must show a
**non-zero** PRIMARY delta for the same per-notional move, and "if the PRIMARY delta is also zero, E6
is not implemented".

**Implemented:** `capital_normalised_return_bps = outcome_bps × risk_size`, i.e. the episode's return
measured against the run's fixed unit-capital reference base.

**Verified:** golden trace 1 reproduces the design's numbers exactly — per-notional delta `0.0`,
capital-normalised delta `−50.0` bps.

**Operator action if this reading is wrong:** the estimand is one column and one line of code. But no
size-invariant denominator can answer OD-19. Recorded as **AMENDMENT-4, unsigned**.

### 1.2 Admission is the stop fill, not order creation

Design §2 OBJECT-IDENTITY binds it: "capital is committed at the stop fill, and every
availability/selection measure conditions on that same stop-fill state."

**Why it matters, measured.** An earlier build read admission at order creation. The eight
`PENDING_EXPIRY` arms act on how long a pending order lives, so at order creation they produce
exactly the comparator's order set and no declines at all — and were written off as having no
measurable population. At the fill they are not inert:

```
FIXED_NATIVE_BREAKOUT                          orders 5,738   fills 1,695
NAT_BREAKOUT_TAIL_RISK_PENDING_EXPIRY_DIRECT   orders 5,738   fills 1,808   (+6.7%)
```

**Implemented:** `admitted` is the fill; `order_created` is emitted beside it so the two events stay
separable; an order created and killed by its own expiry rule before filling is an
`EVALUATED_DECLINED_ORDER_EXPIRED` origin. All eight arms now carry 25–4,431 declined origins with
real counterfactuals.

### 1.3 Continuous sizing runs only where a component supplies a numeric scale

OD-14 requires both sizing forms be tested, and design §6C writes "each component × {continuous
`SCALE_NORMALISED`, discrete `STATE_HALVE_HIGH`}". The continuous rule is
`clip(median_scale / event_scale, 0.5, 2.0)` — it needs a numeric scale and its calibration median.
Six of the eight components are **categorical state flags** and the design declares no continuous
schedule for them; inventing one would be a new mechanism, which is a new experiment.

**Implemented:** the discrete state gate on all eight components; the continuous form on
`RANGE_SCALE` and `SWING_SCALE`. **Consequence, stated plainly:** this run compares the two sizing
forms on two components, not on eight. The coverage and its reason are emitted in
`analysis_summary.json`.

### 1.4 The safety ceiling is apparatus; the refuted hold device stays out

`UNCAPPED_HOLD_SAFETY_CEILING` carries device `NONE`. Its id contains the word HOLD, and an early
version of the lattice check flagged it as a refuted device on a name substring. The check now reads
the emitted `device` column instead.

---

## 2. The hold cap fell out as NOT_APPLICABLE — and why that was predictable

The design's cap rule is: the smallest value on the declared grid `{2, 4, 8, 12, 24, 48}` that binds
at most 5% of arm B's closed positions, on the duration distribution only.

**Measured (cTrader H1):** 382 closed arm-B positions; median = p99 = max = **120 domain bars**;
every grid candidate binds **100%**; the safety ceiling binds **100%** against its declared 2%
tolerance.

**Mechanism.** With the four capture devices excluded (OD-11 / OD-15), the breakout strategy has
**no exit of its own**. The baseline's one-bar exit *is* its holding rule, so removing the holding
cap leaves the safety ceiling as the only exit. Arm B cannot produce a spread of durations, and the
cap rule has nothing to select from.

**Applied as the design directs, not reinterpreted:** the cap is not set, the comparison arms keep
the declared one-bar hold, the ceiling bind rate is reported and flagged. `hold_cap_bars` is emitted
null and the self-check declares that null legitimate rather than demanding a value the rule declined
to set.

**Consequence for M4.** The shared cap exists so that absorbing devices become readable. This run
contains no absorbing device, so nothing needed fixing — but M4 is **untested apparatus** here, not
satisfied apparatus.

---

## 3. Out of scope — written down, not acted on

**The decay curve (H3) cannot be built from exit times on this arm set.** H3 asks for mean outcome as
a function of bars held. Arm B's exits are all at the ceiling, so the emitted curve is a single point
at 120 bars. The quantity H3 wants is a **mark-to-market path per bar held**, which this emission
does not carry and which is a new measurement rather than a new arm. If the operator wants the
successor's horizon calibrated from data, the cheapest route is per-bar MTM on arm B alone — one
column on one arm, no new arms, no change to any estimand.

**P-5 (i) is measurable only after execution.** The paired arm-difference dependence is
`outcome × weight` and no outcome exists before the run. The weight half is deterministic in the
causal features and is measured at preflight; the outcome half runs as the **first** post-execution
diagnostic, before any effect is read, so no variance treatment can be chosen to flatter a result.

---

## 4. Performance work and its parity proof

The SPDR-021/022/023 optimisations are **retained, not rewritten** (OD-6): per-symbol parallel
analysis, single-pass bootstrap per group, columnar schedule consumption, the frozen shared account,
streamed artifact hashing.

Changes to shared code were made for the domain and emission requirements, never for speed, and each
is guarded so the existing experiments' behaviour is unchanged:

| Change | Why | How parity is held |
|---|---|---|
| `_hourly_frame` → `_domain_frame(domain)` | H4 is a declared cell (OD-2) | H1 aggregation identical; default unchanged |
| `domain_ns` on the strategy and work unit | expiry and holds are declared in domain bars | defaults to one hour |
| `availability_shift_bars` on the feature panel | the leak tripwire needs an acausal twin | defaults to `0` = the causal panel, byte-identical |
| `hold_exit_reason` optional schedule column | the ceiling must be nameable in the ledger | absent for other experiments; tags fall back to `HOLD` |
| `_baseline_hold(experiment_id)` | SPDR-024 holds one bar | returns the same values as the branch it replaced |
| time derangement skipped for SPDR-024 | OD-17 removed it | other experiments still emit it |

**Evidence:** the full suite runs green with the SPDR-021/022/023 contract, entries, features,
policies, strategy, runner, analysis and integrity tests unchanged. Determinism is proven per cell by
an independent full replay at one worker compared against the three-worker run.

**Recorded caveat.** Re-running SPDR-021/022/023 on this code would add columns and a table, so
artifact hashes would differ even though every shared value is identical. Values were proven
identical by replaying both experiments under a worktree at HEAD; the hash caveat is recorded so
D11's "exact parity" is not read as covering hashes it does not cover.

---

## 5. Provenance caveat on the 2026-08-06 review round

An earlier version of this file cited `review.md`, `review-001.md`, `review-002.md` and an analyst
`analysis.md` as the sources of an 18-item correction list. **None of those four files exists in the
repository**, so that correction chain cannot be independently audited from artifacts. The fixes
themselves were re-verified against the emitted data during the 2026-08-07 review and are accurate;
the citations are recorded here as unresolvable rather than left to imply an audit trail that is not
there.

---

## 6. Two post-review corrections, and what was wrong each time

Both corrections were to the **analysis layer**, not the emission. The engine emissions were sound
and were not re-run; the analysis artifacts were regenerated from them.

### 6.1 First correction (AMENDMENT-5, 2026-08-06→07): the bias was mechanised in the band rule

A review found three independent defects that all pushed the same way — toward reading cells that
could not resolve as cells that had measured nothing.

| # | Defect | Evidence it was real |
|---|---|---|
| 1 | The band rule compared each cell's floor only to the TOP of the family's observed effect range (0.150 σ̂) | cTrader H1's governing floor is 0.084 σ̂ — blind to more than half the 0.022–0.150 range — and its nine sub-floor SIZE results were all banded `WASH` |
| 2 | The selection band had **no power guard at all** — only a 30-row minimum | all 96 selection contrasts sat 3–20× below their own floor and all were banded `WASH` |
| 3 | `admitted` was read at order creation, not the stop fill design §2 binds it to | §1.2 above — the eight `PENDING_EXPIRY` arms |

Five further apparatus defects were fixed in the same pass and all stand: the selection channel took
its interval from the block bootstrap and its floor from unblocked row counts; the gate-permutation
band cut at a fixed `p >= 0.05`; the structural-zero label was applied lens-blind; the regime-matched
contrast compared different row sets on its two sides; and the tripwire tested only that no shifted
edge exceeded its twin, never the collapse it is named for. **OD-3 was also not discharged at all** —
no baseline characterisation artifact existed — and `baseline_characterisation.parquet` was added.

**What that correction got wrong.** It fixed the mislabelling by *enriching the taxonomy*: it added
`NOT_RESOLVABLE_AT_THIS_FLOOR`, `MAGNITUDE_RESOLVED_DIRECTION_UNRESOLVED`,
`INERT_ARM_NO_GATE_FIRED_IN_STRATUM` and a `resolution_class` computed from the floor **before the
estimate was read**. That is more labelling, not less, and it made power the primary determinant of
how a row is described.

### 6.2 Second correction (AMENDMENT-6, 2026-08-07): no result labels at all

The programme standard does not permit a result label on an emitted row, and no operator directive
superseded the clauses that say so:

- `adaptive-management-design.md` §1 — "Event count, uncertainty and MDE are reported as context;
  **power labels do not decide which rows are shown or how they are described**."
- `adaptive-management-design.md` §9 — "Emit event count, effective count, CI and MDE for every row.
  These are informative diagnostics, **not verdict labels or pruning rules**."
- The SPDR-021/022/023 execution standard — "**Power is context only**"; report MDE "without making
  power a gate"; "no verdict, winner, **pass/fail-value** or top-N field exists"; "Report all strata.
  **No supported/refuted labels.**"

The precedent bears it out: SPDR-021/022/023 `analysis.md` contain **zero** occurrences of
`UNPOWERED`, `WASH`, `CONTRADICTED` or `NOT_RESOLVABLE`; `SUPPORTED` and `REFUTED` appear once each,
inside SPDR-021's boundary statement declining to use them. SPDR-021 §3 states the rule directly:
"No row anywhere below is dropped, trimmed, top-N pruned **or labelled because of its count or its
MDE**."

Applied:

| Change | Detail |
|---|---|
| Every result-label column removed | `band`, `governing_band`, `component_specific_band`, `resolution_class`, and the four `step3_*` / `floor_over_*` reference columns. `band_label`, `resolution_class`, `_selection_band`, `_band_or_identity`, `_control_band` and `_resolution_fields` are deleted, and a test asserts none is reintroduced |
| The seven named populations emitted on every row | `eligible_origin_n`, `entry_fill_n`, `close_n`, `common_fill_n`, `common_close_n`, `effective_origin_blocks`, `effective_trade_blocks` — null where one does not apply, never filled in from another population. This was the population-conflation defect that invalidated the SPDR-021/022/023 first pass |
| Design §11 rewritten | BANDS withdrawn; the reporting rule is estimate + uncertainty + population count + effective count + MDE and nothing else |
| `analysis.md` and `screen.md` replaced | rewritten to the SPDR-021 form: `ci+`/`ci−` tallies against median estimate and median MDE, every statement tagged **observed** or **inference**, observations split consistent / contrary / unresolved |
| Facts that survived as facts, not labels | `exact_zero_delta_share` (a measured share, and the lens plus gate rate distinguish the two cases it can mean); `rejected_population_empty` (a property of a rule's semantics, not of the sample); `control_applicable` with its stated reason (a permutation of a constant vector is the identity, so the control cannot move the statistic it exists to destroy) |

### 6.3 Third correction (2026-08-07): the tripwire criterion was too strict and failed a valid cell

Re-running the self-check after §6.2 exposed a defect in §6.1's own tripwire fix. The corrected
criterion required every arm carrying a causal edge to collapse **into** the noise floor and blocked
when one did not. On crypto H4 that produced a **false HARD failure**:

```
ADP_SWING_SCALE_SIZE_STATE_HALVE_HIGH
  causal_effect_sigma  = 0.0648   mde_sigma = 0.0626   (clears its floor by 3.5%)
  shifted_effect_sigma = 0.0656                        (statistically the same number)
  shifted_edge_survives = False   surviving_arms = []
```

A HARD failure declares the **emission invalid — fix the data**. That verdict would have been wrong:
no shifted arm outperformed its twin. Design §9's REJECT condition is "a **SURVIVING** edge under
the shift"; its "expected collapse fraction ~ 1.0" is stated as an expectation, not as the pass
rule, and §6.1 read the expectation as the rule.

The mechanism is structural and is the scale-invariance limit seen from the other side: a SIZE arm's
paired difference is dominated by the exposure term `(E[size] − 1) × E[outcome]`, and a one-bar
availability shift barely changes the **gate rate**, so the exposure term survives the shift almost
intact. Requiring collapse from an arm whose effect is mostly exposure arithmetic demands something
the shift structurally cannot produce.

**Fixed:** `pass` is `non_vacuous and not surviving` — §9's REJECT clause. Collapse behaviour is
reported per arm and in `arms_with_an_edge_that_did_not_collapse_into_noise` plus a
`non_collapse_note`, and gates nothing. A regression test carries the exact crypto H4 shape.

**What survives from §6.1's diagnosis.** The real defect was that the artifact reported "0 survivors"
as though it were a demonstrated collapse when there was nothing to collapse. The reporting fields —
`arms_with_a_causal_edge`, `collapsed_into_noise`, `collapse_fraction`, `informative`, `bite_note` —
are the right fix and stay. Turning non-collapse into a blocking gate was the overreach, and the
rerun is what caught it.

**What the corrected artifacts then showed**, which no version before this could: seven arm-cells
across the run carry an edge, and on six of the seven the shifted twin is the same size or larger.
The largest collapse fraction anywhere is 0.174. That is now stated in `analysis.md` §2 with both
readings it admits, neither resolved.

---

One latent bug surfaced during the rerun and was fixed: `pl.from_dicts` used the default 100-row
schema-inference window, so a column that is legitimately null on a long run of leading rows was
typed `Null` and failed on the first float. Whether that happened depended on how many symbols a
universe had — the analyser succeeded on three cells and failed on the fourth. All four call sites
now scan every row.

---

## 7. Artifact map

```
python/experiments/SPDR-024/
├── screen_code/
│   ├── run_screen.py      # TRAIN-only runner: --domain, --phase, --future-shift
│   ├── run_cell.py        # one cell end to end, in the order the design requires
│   ├── preflight.py       # P-1 / P-2 / P-3 / P-5, all computed from TRAIN data
│   ├── cap_rule.py        # design section 7 CAP-RULE, duration basis only
│   ├── golden_traces.py   # the three design section 14 traces
│   └── selfcheck.py       # 17 HARD checks, count asserted, reconciled by name
├── analysis_code/analyse.py
├── design.md · screen.md · analysis.md · implementation-notes.md
└── results/
    ├── preflight/         ├── performance/     ├── selfcheck/
    ├── golden_traces.json ├── *_cap_rule.json  ├── estimand_validation_*.json
    ├── runs/              └── analysis/
```

---

## 8. MDE / floor apparatus — AMENDMENT-7 (2026-08-07)

**Binding decision:**  
`docs/experiments-docs/checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/mde-floor-defect-spdr024.md`
§12 (independent validation) and **§13 (OPERATOR DECISION — clean fix, artefact purge, full
re-emission)**.

**Design:** AMENDMENT-7 in `design.md` §10 / §11 / §15 — R1–R5 in one package; **SIGNED** by
§13 / 2026-08-07. Supersedes: `2.8/√blocks` as row floor; Step-3 0.022–0.150 as gate/resolve bar;
order-only preflight magnitude passes; silent dual-σ̂ ladder. Retains: A4 unit-capital PRIMARY;
A5 admission-at-fill; A6 no result labels + seven populations.

**Code contract (post-A7):**

| Remedy | Where | Rule |
|---|---|---|
| R1 | `preflight.py` + optional analysis context | mechanism ceiling = √p × \|μ\|/σ from baseline fills |
| R2 | `spdr024_analysis.clustered_interval` / selection interval | `mde = MDE_Z × bootstrap_SE` |
| R3 | emission schema + prose | no pass-mark / no power labels |
| R4 | scale vs selection rows | `sigma_denominator` = `paired_delta` / `outcome_level_bps` |
| R5 | `preflight.py` | fills or `PROVISIONAL_FILL_RATE_ADJUSTED`; same R1 endpoint |

**Execution handoff:**  
`docs/superpowers/plans/2026-08-07-spdr-024-mde-floor-fix-execution-handoff.md`

**Claude pre-run review (Task 5):**  
`docs/superpowers/plans/reviews/2026-08-07-spdr-024-mde-floor-claude-review.md`  
Verdict `READY_FOR_PURGE_AND_FULL_RUN`; gate CLEARED 2026-08-07.

**Re-emission (2026-08-07):** pre-fix artefacts purged; all four cells re-ran TRAIN-only with
`blocking_pass=true` and HARD count 17. Fresh `analysis.md` / `screen.md` use power as context
only. AMENDMENT-7 in force.
