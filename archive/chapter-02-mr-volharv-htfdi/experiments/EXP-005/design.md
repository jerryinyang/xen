# EXP-005 — E5 DET-Adjudication + FREEZE (+ folded Q4 form-check) (referee renew, D-referee)

**Branch:** `main`. **Checkpoint:** Phase-001 §E5 (ladder:138; binding D0:101-106,108-115;
DET-dominance:104-106; success O1:78-80). **Consumes:** E3a (EXP-003, A1) — the as-built
`gate_stack_adaptive` + `adaptive_row` (§10.3a, studentized∧bps sub-pop L5, L1 rigid); E4 (EXP-004) —
FREEZE LICENSED (RANGE-BOUNDED), safe q\* range {0.7,0.75}, R3 skew-FPR refuted, the recorded
single-draw FPR-label precondition; the E2 substrate + the EXP-003/EXP-004 3-arm DET harness.
**Classification:** **analysis-only** (synthetic substrates + frozen primitives + the E3a adaptive
legs + the new variant-c verdict path; no price→signal). **Reads/slots:** 0 TEST reads, 0 candidate
slots; global holdout sealed. **Does NOT** adjudicate CF-MR-002, touch L1, retune any frozen constant,
sweep q\* (E4 did that — E5 freezes at the validated q\*=0.75), or touch the global holdout.

**E5 is the terminal D-referee rung: it adjudicates the composite *form* then FREEZES + hash-pins the
renewed referee** (the artifact D-benchmark adjudicates CF-MR-002 against). Per the L-12 governance
constraint the new gate must be **frozen before any live read** and **never tuned on CF-MR-002**
(absent here).

## Question (one, falsifiable)

**On the E2/E3a substrate (32 strata × 4 shapes, q\*=0.75), does the §10.3a validity→economics
composite (the as-built `adaptive_row`: L1+coverage admissibility ∧ power-aware L3 ∧ studentized-subpop
L5) DET-MATCH-OR-BEAT the single-statistic variant-c (L1+coverage admissibility ∧ a single binding
economic statistic = incremental-net vs-naive CI-lower > 0; L5/sub-pop demoted to reported
diagnostics) — per stratum: `MDE_§10.3a ≤ MDE_variant-c` on every shape at FPR not worse under the
E4-derived less-brittle rule — licensing the FREEZE of §10.3a at q\*=0.75 as the renewed referee; OR
does variant-c strictly DET-dominate, so the winner is frozen instead?**

Binding endpoint **per stratum** (L-03). Predeclared primary = §10.3a (D0 Q4, :112); variant-c is the
"also-evaluate" reported variant; the **one** predeclared selection criterion (DET-dominance) controls
the 2-way form multiplicity. **Freeze §10.3a iff it matches-or-beats variant-c; else freeze the
winner. Variant-c is recorded as the rejected alternative either way.**

## What variant-c is (the BUILD)

A new verdict-assembly function `adaptive_row_variant_c` in `python/src/xen/referee_adaptive.py`
(assessment §10.3(c): *"single sufficient statistic + power guards — the incremental net edge is the
verdict; the others become reported diagnostics, not gates"*). It **reuses the exact same
`gate_stack_adaptive` core** (identical split / block bootstrap / neutral+naive CI pair / per-episode
sub-pop dists — already computed) and changes **only the verdict assembly**:

| Leg | §10.3a (`adaptive_row`, freeze candidate) | variant-c (`adaptive_row_variant_c`) |
|---|---|---|
| **L1 readiness + coverage** | rigid admissibility gate | **identical — rigid admissibility gate** |
| **economic decision** | power-aware **L3** (neutral CI>0 ∧ vs-naive CI>0) ∧ power-aware **L5** (pooled-material OR studentized-subpop-material); `PASS iff L1 ∧ no-FAIL ∧ ≥1 powered-PASS` | **single statistic**: `PASS iff L1 ∧ coverage ∧ (vs-naive incremental-net CI-lower > 0)`; power-aware **ABSTAIN** if `n_naive == 0` |
| **L5 materiality (pooled + studentized sub-pop)** | **binding** (the STATE-recovery path) | **reported diagnostic — NOT a gate** |
| **L3 neutral CI** | binding (part of L3) | reported diagnostic |

**No new free knob, no new threshold, no new module constant.** variant-c's single statistic is the
incremental net edge over the naive-momentum control (the assessment's named statistic), already
present in the core as `ci_naive.lower`. The economic-leg discriminator between the two forms is the
**studentized sub-pop L5 recovery path**: §10.3a carries a latent-sub-state (STATE / diluted) edge via
that path; variant-c, deciding on the pooled incremental mean alone, structurally cannot. **Honest
prior:** §10.3a matches-or-beats variant-c (ties DENSE/TAIL, beats on STATE), so §10.3a freezes and
variant-c is recorded as the rejected alternative that loses STATE recovery — but E5 *runs* the
comparison, it does not assert it.

## The E4-derived less-brittle freeze-adjudication FPR rule (binding precondition, candidate-blind)

E4 surfaced that the A1.3 verdict rule (`wilson_lower(passes,draws) > frozen≡0`) is single-draw
brittle: a lone `1/162` noise pass gives `wilson_lower(1,162)=0.0011>0` → spurious FPR_BROKEN, though
the gate's true FPR ≤0.62% ≪ control. E5 adopts the recorded remedy **in the adjudication harness only
(the gate `adaptive_row` is UNCHANGED)**:

> A form's dogfood-FPR is **FPR-ACCEPTABLE** iff `passes < MIN_FPR_PASSES` **OR**
> `wilson_lower(passes, draws) ≤ FPR_CONTROL_BOUND`, with **`MIN_FPR_PASSES = 2`** and
> **`FPR_CONTROL_BOUND = 2α = 0.10`**. A form's FPR is "worse than" another's only when it is **not**
> FPR-ACCEPTABLE while the other is. FPR_BROKEN ⇔ `passes ≥ 2 ∧ wilson_lower(passes,draws) > 2α`.

`MIN_FPR_PASSES=2` (retire the single-draw artifact) and `2α` (the pre-existing control budget) are
derived from α + the draw structure — **not from any E4/E5 outcome** (Q5/candidate-blind). This
retires the 6 single-`1/162` labels E4 flagged; with true FPR ≤0.62% everywhere, all forms are
trivially FPR-ACCEPTABLE, so the rule changes *labels*, never the freeze decision.

## Method — 3-form DET comparison (per stratum × shape), reusing the EXP-003/EXP-004 harness

Reuse the EXP-004 driver scaffolding (`mde_of`, `dogfood_fpr`, `no_plant_passrate`,
`future_destroyed_passrate`, the substrate, the nulls) **unchanged in logic**, at the single validated
operating point `(q*=0.75, N_BOOTSTRAP=500, seed_off=0, standard nulls)` — E5 is the freeze, not a
sweep. Three gate **forms** on identical draws/seeds/split/bootstrap per (stratum, shape):

1. **frozen** (`gate_stack_core` + `gate_stack_row`, per-held) — the baseline DET reference (the
   regression-anchor target; reproduces E3a/E4).
2. **§10.3a** (`gate_stack_adaptive` + `adaptive_row`) — **the freeze candidate** (= E4 baseline arm).
3. **variant-c** (`gate_stack_adaptive` + `adaptive_row_variant_c`) — **the rejected-alternative
   candidate**. Same core, single-statistic verdict.

Per (stratum, shape, form): **MDE** = DETECTED_FLOOR (first `e>0` at ≥`POWER_TARGET=0.50` detection;
inf=UNPOWERED). Per (stratum, form): dogfood-FPR over the 3 null families (Wilson; the new rule).

**Binding metric (per stratum, non-pooled — L-03):**
`Δform(shape) = MDE_variant-c − MDE_§10.3a`. **§10.3a-MATCHES-OR-BEATS (per stratum)** ⇔
`MDE_§10.3a ≤ MDE_variant-c` on every shape **AND** §10.3a FPR-ACCEPTABLE wherever variant-c is.
**VARIANT-C-DOMINATES (per stratum)** ⇔ `MDE_variant-c ≤ MDE_§10.3a` every shape ∧ strictly `<` on ≥1
shape ∧ §10.3a not better elsewhere ∧ variant-c FPR-ACCEPTABLE. Pooled counts disclosure-only. Each
form is **also** reported vs frozen (the §10.3a-vs-frozen leg = the E3a/E4 regression anchor).

## Regression anchor (binding correctness gate)

At `(q*=0.75, N_BOOTSTRAP=500, seed_off=0, standard nulls)` the §10.3a form **must reproduce EXP-003
(A1) / EXP-004-anchor per stratum**: 32/32 §10.3a-vs-frozen DET_DOMINANT, STATE ΔMDE median 7.5 (range
4.0–23.5), §10.3a dogfood FPR 0/32, future-destroy 0. A mismatch ⇒ adding `adaptive_row_variant_c`
perturbed the §10.3a path or the harness is mis-wired ⇒ **fix + rerun before any adjudication**
(adding the variant must be purely additive — `adaptive_row` / `gate_stack_adaptive` / every frozen
constant byte-unchanged; verified by the anchor + a git diff showing additions only).

## Leak tripwire(s) — retained from E3a/E4, applied to BOTH adaptive forms

1. **Future-destroy collapse (critical):** plant STATE edge, block-permute returns, re-run **both**
   §10.3a and variant-c — detection (incl. §10.3a's studentized sub-pop and variant-c's incremental
   statistic) **must collapse to FPR**. A surviving future-destroyed pass in **either** form =
   noise-mining → **REJECT-class** (that form is not freezable). variant-c is a NEW verdict path → it
   ships its own future-destroy check.
2. **No-plant guard:** no drift ⇒ both forms' PASS rate ≈ FPR on every shape.
3. **Dogfood-FPR control (binding, new less-brittle rule):** both forms FPR-ACCEPTABLE on the 3 null
   families.

## The FREEZE (the deliverable — enacted on the adjudicated winner)

Once adjudicated (expected: §10.3a matches-or-beats → freeze §10.3a), **FREEZE + hash-pin the renewed
referee**, recorded in `results/freeze_manifest.json` + the report:
- **composite form** = §10.3a `adaptive_row` (or variant-c if it dominates);
- **frozen constants:** `q*=0.75`, `Q_STUD_MIN=Φ⁻¹(0.75)=0.6744897501960817`, `MATERIALITY_BPS` map
  (1.5/3.0), `ROUND_TRIP_COST_BPS_17` map, return basis open-to-open `≤t-1`, `ALPHA=0.05`,
  `MIN_EPISODES_SUBPOP=5`, the E5 adjudication FPR rule (`MIN_FPR_PASSES=2`, `2α`);
- **provenance:** `sha256(referee_adaptive.py)` + git commit; rejected alternative (variant-c) named.

The freeze manifest is what **D-benchmark** loads to adjudicate CF-MR-002 on the renewed referee in
parallel with the retained frozen Chapter-01 suite. **No frozen Chapter-01 constant changes**;
`referee_calibration.py` stays byte-frozen.

## Predeclared interpretation criteria

- **FREEZE §10.3a (primary success):** §10.3a matches-or-beats variant-c on all 32 strata (≤ MDE every
  shape, not-worse FPR), regression anchor reproduces, both forms leak-clean (future-destroy
  collapses). → freeze §10.3a at q\*=0.75 + hash-pin; record variant-c as the rejected alternative
  (loses STATE recovery — quantify the STATE ΔMDE gap variant-c forgoes).
- **FREEZE variant-c (alternative success):** variant-c strictly DET-dominates §10.3a (≤ MDE every
  shape, `<` on ≥1, not-worse FPR). → freeze variant-c instead, record §10.3a as the rejected
  alternative. (Honest prior: unlikely — variant-c lacks the sub-pop recovery path → expected to lose
  STATE.)
- **Shape-aware read:** STATE is the discriminating shape (sub-pop recovery vs single-stat dilution);
  DENSE/TAIL expected to tie (location edges both forms see); SPARSE governed by rigid L1 in both.
  Report `Δform` per shape; the STATE gap is the freeze rationale's headline.
- **Failure:** regression-anchor mismatch (harness/additivity bug → fix+rerun); OR a future-destroyed
  edge survives in either form (REJECT-class → fix+rerun); the freeze does not proceed until leak-clean
  and the anchor reproduces.
- **Inconclusive:** bootstrap/seed noise swamps the §10.3a-vs-variant-c MDE boundary on STATE → report
  the bound, raise resamples (E4 showed stability at 500/1000 → unlikely).

## Data views / substrate (reuse E2/E3a/E4 exactly)

16 inst × {1h,4h} (DE30 absent — no 5-year-era file) = 32 strata; open-to-open `≤t-1` (E0); first-70%
slice + domain fence; holdout sealed. Shapes DENSE/TAIL/SPARSE/STATE (matched-magnitude). Null
families: block-permute returns; reblock-random positions; causally-lagged dogfood (Donchian-20 + MA
20/50, lagged ≤t-1). Fixed `(q*=0.75, N_BOOTSTRAP=500, seed_off=0)` — the E4-validated operating point.

## Complexity budget

- **New code modules: 1** — `adaptive_row_variant_c` in `referee_adaptive.py` (additive verdict path;
  reuses the `gate_stack_adaptive` core unchanged) + the E5 harness in `code/` (reuses the EXP-004
  3-arm driver, swapping the 3rd arm to variant-c and the classify to the new FPR rule + the
  §10.3a-vs-variant-c adjudication + the freeze-manifest writer). `referee_calibration.py` byte-frozen.
- **Stat work:** MDE per (32 × 4 shapes × 3 forms) + dogfood-FPR per (32 × 3 forms) + the per-stratum
  adjudication. Within comparative (2–4).
- **Visualisations: 3** — (1) **§10.3a-vs-variant-c DET map** (MDE per stratum × shape, both forms;
  annotate the adjudication verdict); (2) **STATE MDE comparison** (the discriminating shape: §10.3a
  sub-pop recovery vs variant-c single-stat, ΔMDE per stratum); (3) **dogfood-FPR both forms vs
  control** (Wilson bars, the new less-brittle rule annotated). Within comparative (3–5).
- **One falsifiable question** (which form to freeze) + the freeze act. Fits one rung.

## Metric denominators / zero-baseline

MDE in bps on `EDGE_GRID_BPS` (UNPOWERED=inf, reported never failed); FPR Wilson-bounded over stated
draws under the new rule (`passes/draws`, `MIN_FPR_PASSES=2`, `2α`); sub-pop denominator = episodes.
`Δform` NaN where either form UNPOWERED on that shape. No-plant / `e=0` = the null guard. No
percentage-of-zero metrics.

## Implementation safety constraints (developer)

- **variant-c is additive + reuses the §10.3a core unchanged.** `adaptive_row_variant_c` consumes the
  same `gate_stack_adaptive(...)` core dict; it must **not** edit `adaptive_row`, `gate_stack_adaptive`,
  or any module constant (verified by the regression anchor + an additions-only git diff).
  `referee_calibration.py` byte-frozen. L1+coverage identical (rigid admissibility) in both forms.
- **variant-c single statistic** = `ci_naive.lower > 0.0` (incremental net vs the naive-momentum
  control), power-aware **ABSTAIN** if `n_naive == 0`. L5 pooled + studentized sub-pop and the L3
  neutral CI are emitted as **non-binding diagnostics** in `leg_results` (so the DET map can show what
  variant-c forgoes). No materiality floor on variant-c (faithful single-statistic form).
- **E5 adjudication FPR rule** lives in the harness's `classify` (not the gate): `MIN_FPR_PASSES=2`,
  reuse `FPR_CONTROL_BOUND=2α`; candidate-blind constants.
- `q*=0.75` fixed; `N_BOOTSTRAP=500`, `seed_off=0` (the E4 anchor). Open-to-open `≤t-1`; first-70% +
  domain fence; never the final 30%; `CloseTime` ordering. `tqdm` on the (form × stratum) loop;
  ProcessPool seed-deterministic (strata independent). Bound `N_PLANT=20`, `N_NULL=80`.
- **The FREEZE:** after a leak-clean, anchor-reproducing adjudication, write
  `results/freeze_manifest.json` (form, all frozen constants, `sha256(referee_adaptive.py)`, git
  commit, rejected alternative). The variant-c addition is made **before** the freeze; the manifest
  names §10.3a (`adaptive_row`) as the frozen referee verdict path. Do **not** hand-edit
  `referee_adaptive.py` after the freeze hash is recorded.
- The adaptive gate is **not tuned on CF-MR-002** (absent here); E5 freezes it **before** D-benchmark.

This experiment adjudicates the Q4 composite form (§10.3a vs variant-c) by DET-dominance, adopts the
E4-derived less-brittle freeze-adjudication FPR rule, and FREEZES + hash-pins the renewed referee at
q\*=0.75 before D-benchmark. It does not adjudicate CF-MR-002, touch L1, retune any frozen constant,
sweep q\*, or touch the global holdout.

---

## GATE: APPROVE (orchestrator inline pre-exec, 2026-06-29)

Checked against `references/governance-constraints.md` + binding D0 (:101-115) + the checkpoint E5
ladder (:138) + the E4 freeze license:
- **Single falsifiable question** — which composite form to freeze, by DET-dominance (§10.3a
  matches-or-beats variant-c → freeze §10.3a, else freeze the winner). The freeze is the *act*, not a
  second question. One rung. ✓
- **D0 Q4 honored** (:112) — primary §10.3a + single-statistic variant-c, **one** predeclared selection
  criterion (DET-dominance) controls the 2-way form multiplicity; soft-vote stays dropped. variant-c
  faithfully built per assessment §10.3(c) (single sufficient statistic = incremental-net vs-naive
  CI-lower; others demoted to diagnostics). ✓
- **D0 hard guards** (:144) — L1+coverage rigid admissibility in **both** forms; q\*=0.75 is the
  E4-validated point (no sweep); `referee_calibration.py` byte-frozen; variant-c **additive** (must
  not edit `adaptive_row`/`gate_stack_adaptive`/any constant — enforced by the regression anchor + an
  additions-only diff); freeze **before** D-benchmark; **not tuned on CF-MR-002** (absent). ✓
- **Gate-threshold calibration (scrutinized)** — the E4-derived less-brittle FPR rule
  (`MIN_FPR_PASSES=2`, `2α`) is **candidate-blind**, derived from α + the draw structure, **not** from
  any E4/E5 outcome (Q5); it lives in the **adjudication harness only** — the gate `adaptive_row` is
  byte-unchanged. No magic constant; no new gate knob/threshold/module constant. ✓
- **Regression anchor** — §10.3a must reproduce EXP-003(A1)/EXP-004-anchor (32/32, STATE ΔMDE median
  7.5, FPR 0/32, FD 0) before any adjudication; proves the variant-c addition is purely additive and
  the new FPR rule leaves the clean baseline unmoved. ✓
- **Leak tripwires** — future-destroy collapse on **both** forms (variant-c ships its own; a survivor
  in either = REJECT-class), no-plant guard, the new-rule dogfood-FPR control. ✓
- **Per-stratum binding** (L-03); pooled disclosure-only; STATE is the predeclared discriminating
  shape; shape-aware `Δform` read. ✓
- **Classification** analysis-only; `referee_calibration.py` byte-frozen; holdout sealed; 0 reads / 0
  slots; methodological (screens **no** candidate — no slot/TEST-read precondition beyond the existing
  registered E5 row). ✓
- **Budget** — 1 new src verdict path (variant-c) + harness; 3 tests; 3 plots; within comparative. ✓

**Operator-awareness note (non-blocking):** E5 enacts the **FREEZE + hash-pin of the renewed referee**
— the keystone programme commitment that lets the gate adjudicate CF-MR-002 at D-benchmark. It is
fully predeclared (G0/D0 :138) and E4-licensed, analysis-only, 0 reads, holdout sealed, so it runs
autonomously; the freeze manifest (form, constants, `sha256`, rejected alternative) is surfaced for
operator review at the post-exec gate before D-benchmark proceeds.

No REVISE issues. Proceed to Stage 2 (build `adaptive_row_variant_c` in `referee_adaptive.py` +
the E5 3-form DET + adjudication + freeze-manifest harness in `code/`, reusing the EXP-004 driver).
