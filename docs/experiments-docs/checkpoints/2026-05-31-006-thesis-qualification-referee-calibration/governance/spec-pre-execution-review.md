# Pre-Execution Governance Review — Deliverable #2 (Reference-Stack Specification)

**Artifact reviewed:** `docs/experiments-docs/checkpoints/2026-05-31-006-thesis-qualification-referee-calibration/reference-stack-spec.md`
**Phase:** 006 — Thesis-Qualification Referee Calibration
**Gate:** Spec-before-experiment (design.md phase gate 1) — the spec must pass this before any EXP-037 scope is written.
**Date:** 2026-05-31
**Framework:** `research-pipeline/references/governance-constraints.md` + charter §5 binding constraints.

---

## VERDICT: REVISE

```
VERDICT: REVISE
FAILING_ARTIFACT: reference-stack-spec.md
REQUIRED_SKILL: (author) — spec revision; then independent re-review
CYCLES_ALLOWED: 2
```

The spec is a strong scaffold — faithful, line-cited transcription of the EXP-036 stack; clean admissibility/evidentiary separation (constraint 9); an explicit harness stopping rule (constraint 7); species-tagging (constraint 1). **But it cannot be frozen as a pre-registration in its current form.** Five issues are Critical: if locked as written they would bake in either *incoherent* gate arithmetic (C1/C2), a *self-undermining* null (C3), a *tautological* blind-spot result (C4), or a *post-hoc* founding verdict (C5). Predeclaration is only worth something if what is predeclared is sound; these must be fixed *before* the lock, not patched after.

**Independence caveat.** This review was produced by the same agent that drafted the spec. Treat it as a self-adversarial pass, not an independent gate. The `[REVIEW]` values and this verdict still require Jerry's (or a second reviewer's) sign-off — recorded as m3.

---

## Critical issues (block the freeze)

### C1 — Economic-materiality cost is charged against a *contrast*, not a strategy P&L (§2.1)
`Delta_neutral` and `Delta_control` are **differences**, not tradable P&L. The proposed rule `Delta_neutral^net = Delta_neutral − κ` (round-trip cost κ) is a category error:
- `Delta_control = mean((d − c)·r)` is a difference of two direction strategies that **both** pay κ per round trip, so the realistic cost *differential* is ≈ 0 — subtracting a full κ **over-charges** and will reject economically-real marginal edges.
- `Delta_neutral` measures "beats the measured middle-bucket drift," not "is profitable." Subtracting κ conflates *superiority over baseline* with *net-of-cost profitability*.

Constraint 11 / T4 ask for a **minimum economically meaningful effect net of frictions** — that is a property of the **strategy return** `mean(d·r) − κ`, not of the neutral/control contrast.
**Required fix:** define materiality on the strategy's executable P&L (`mean(d·r)` net of κ) as a **separate** gate with its own predeclared floor; do not shift the transcribed contrasts by κ.

### C2 — The materiality rule silently modifies the frozen stack, breaking the §5.6 claim (§0 & Part 1 vs §2.1)
§0 and Part 1 promise the four new constructs are added **"around the frozen stack, never into it."** §2.1 then rewrites the pass condition (a κ-shifted CI-exclusion test) — which *is* altering evidentiary leg E5. The stack that closed Phases 003–005 had **no** cost gate; calibrating a cost-augmented stack means you are not calibrating *the* existing stack, and the §5.6 ruling ("were the three closures sound?") no longer attaches to the object that issued those closures.
**Required fix:** the frozen stack's verdict is computed at **κ = 0** (exactly as transcribed) and is the primary calibration object; net-of-cost survival (per C1's separate gate) is reported as an **additional, separately-labelled axis**, never folded into the frozen verdict.

### C3 — The null construction destroys the episode structure the stack's own inference depends on (§3)
The proposed null "permutes the descriptor labels relative to returns." But the stack's inference unit is the **episode** = a maximal run of consecutive identical buckets (admissibility layer; floors E1; the two-sample episode bootstrap E4). Permuting bucket labels **randomises run lengths**, changing the *number and size of episodes* — precisely the quantities the floors gate on and the episode bootstrap resamples. A null that alters the episode distribution does **not** "break conditioning while preserving dependence" (charter §3); it changes the test's denominator, and the resulting FPR is for a different inference problem. This corrupts the *trustworthy* half, whose trust the charter stakes on null realism.
**Required fix:** resample the **joint** `(bucket, return)` process with a dependence-preserving block/stationary bootstrap that breaks the state→return *conditioning* (e.g. by independently block-resampling the return series against a separately block-resampled state series) while leaving each series' own run/episode structure intact; predeclare a diagnostic that the null's **episode-length distribution matches the real series** (per instrument), and fail any null that distorts it.

### C4 — Synthetic mechanisms 3–4 (timing, sizing) are not operationalized into the OHLC the stack reads — making EXP-039's blind-spot result tautological (§4)
The stack's metric is the **next-open → next-close direction-adjusted log return** (and the 4-bar variant). Therefore:
- **Timing improvement** ("same total move, better entry within the bar window") is *invisible* to an open-to-close metric.
- **Sizing information** (magnitude without sign-predictability) has **zero** direction-adjusted mean by construction.

Planting these and running the unchanged stack yields ≈ 0 power **regardless of the stack's stringency or the planting fidelity**. That conflates the §5.6 question — *is the stack blind to a kind of edge?* (stringency) — with T5 — *is the metric the wrong construct for that edge?* A guaranteed-zero result is not a measurement.
**Required fix:** for **each** mechanism, predeclare exactly how it manifests in the `(open, high, low, close)` the stack consumes, and predeclare the attribution: a zero-power outcome must be classifiable as *gate stringency* vs *metric construct-mismatch*. Mechanisms the metric provably cannot observe are either re-specified to be observable or dropped from the H0/H1 sensitivity statistic (and reported only as a construct-validity finding).

### C5 — The founding decision rule is unquantified (§4; design Phase Thesis)
The whole H0/H1 verdict turns on "MDE **stable** vs **moves materially** across the family." §4 says "the spread across mechanisms is the H0/H1 statistic" — it names the statistic but **never defines the cutoff**. With no predeclared threshold, the verdict is decided after seeing the spread: the exact researcher-DoF / forking-path failure the programme exists to eliminate (constraints 7–8; governance constraint 3 "concrete criteria").
**Required fix:** predeclare (a) the sensitivity metric (e.g. max/min MDE ratio across mechanisms, or CV of MDE), and (b) the **numeric cutoff** separating H1-stable from H0-moves-materially — both fixed before any planting, with the rationale for the cutoff stated.

---

## Major issues

### M1 — Reducing the inner bootstrap to B = 2,000 changes the object under test (§2.4 vs E4)
E4 freezes **B = 10,000** as part of the stack. The compute-budget downscale to B = 2,000 for the calibration loop injects Monte-Carlo noise into the 2.5/97.5 CI endpoints, perturbing pass/fail near the `test_lo > 0` boundary — so the calibrated FPR/power is for a noisier-CI variant, not the frozen stack.
**Required fix:** keep B = 10,000 (and re-derive the budget around it), **or** predeclare and report the boundary-perturbation induced by B-reduction and demonstrate it is immaterial to FPR.

### M2 — The compute budget is asserted, not derived (§2.4)
2,000 nulls × (stack run: inner bootstrap × ~16 instrument×tf×contrast cells × block-length grid {20,60,240}) is tens of millions of inner statistic evaluations for Part A alone; "≤ 12 CPU-hours" has no back-of-envelope. Constraints 1 and 6 require the arithmetic *and* a bounded, **stated** budget.
**Required fix:** show the derivation. If it does not close within budget, the diversity-over-replication downscale must be applied **in the spec now**, not discovered mid-run.

### M3 — "Plant into real *or* null-resampled series" is an unresolved fork (§4)
Power-on-real conflates the planted effect with any **latent real edge** (the very thing §5.6 interrogates); power-on-null conditions power on the null's realism too. Governance constraint 3 requires a single defined method.
**Required fix:** choose one and justify; if real, predeclare how latent structure is netted out of the power estimate.

### M4 — "Per-leg false-pass rate" is ill-defined for the aggregate legs (§3 outputs)
E6 (≥ 2 instruments) is a function of E2/E3/E5 *across* instruments and has no per-cell false-pass meaning; E5 is itself a conjunction. Listing E1/E2/E3/E5/E6 as five comparable "per-leg" rates is not coherent.
**Required fix:** define per-cell false-pass for the cell-level legs (E1/E2/E3) and a **separate aggregate** false-pass for the E5∧E6 replication conjunction.

### M5 — Second-order holdout partitioned by instrument collides with the k = 2 floor (§2.3)
Reserving {USTEC, BTCUSD} as the trusted battery leaves **exactly two** instruments, but the qualifying rule is "≥ 2 of N distinct instruments." With N = 2 on the holdout, the only pass is *both* — the "≥2 of 4" behaviour the stack actually uses **cannot be observed** on the trusted set, distorting trusted FPR/power. The spec flags the partition as a review item but misses this interaction.
**Required fix:** partition on an axis that keeps **N ≥ 3** instruments on the holdout (e.g. by time block and/or seed, retaining all four instruments), or explicitly justify estimating a "≥2 of N" gate on a degenerate N = 2 reserve.

---

## Minor issues

- **m1 — Block-length authority (§3).** FPR is reported per L ∈ {20,60,240} with no predeclared rule for which L the §5.6 ruling believes. Predeclare a selection diagnostic (e.g. the L whose null best matches the real series' measured dependence) or report the FPR **envelope** as the headline.
- **m2 — Proxy-cost κ unsigned-off (§2.1).** The four-instrument κ grid remains `[REVIEW]`; XAUUSD/BTCUSD stress values are order-of-magnitude guesses. Blocking sign-off item (independent of C1/C2's structural fix).
- **m3 — Independence.** Author == reviewer. A second (human) sign-off is required before the spec is frozen, especially on all `[REVIEW]` values.

---

## What is sound (carry forward unchanged)
- Part 1 transcription with line provenance — faithful, verifiable, correctly frozen.
- Two-layer admissibility/evidentiary split, with calibration holding admissibility fixed (constraint 9).
- The harness-DoF **stopping rule** (§2.2): run the fixed family once; sensitivity *is* the finding; no meta-generator. This is the right anti-regress stance.
- Species-tagging of every error rate (constraint 1) and the second-order-holdout *principle* (constraint 10) — the *principle* is correct; only the *partition axis* (M5) needs rework.
- Holdout discipline: no path touches the 30% global market reserve (governance constraint 5) — **clean**.

## Required before re-review
Fix C1–C5 (Critical) and M1–M5 (Major); address m1–m3. The most consequential reframings: **(i)** materiality becomes a separate net-of-cost P&L gate at κ=0-frozen-stack-primary (C1+C2); **(ii)** the null preserves episode structure and is validated against it (C3); **(iii)** every mechanism is operationalized into observable OHLC with a stringency-vs-construct attribution (C4); **(iv)** the H0/H1 sensitivity cutoff is predeclared numerically (C5). Then route to an independent reviewer for the freeze.

**No EXP-037 scope may be created until this artifact reaches APPROVE.**
