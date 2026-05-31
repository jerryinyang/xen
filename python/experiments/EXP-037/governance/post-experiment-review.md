# Post-Experiment Governance Review: EXP-037

**Experiment:** EXP-037 — Null Calibration of Frozen Reference Stack
**Artifacts reviewed:**

- `python/experiments/EXP-037/audit.md`
- `python/experiments/EXP-037/results.md`
- `python/experiments/EXP-037/report.md`
- `python/experiments/INDEX.md` (EXP-037 row)
- `docs/experiments-docs/INDEX.md` (EXP-037 section + checkpoint status row)

**Reference constraints:** `.claude/skills/research-pipeline/references/governance-constraints.md`; `reference-stack-spec.md`.

## VERDICT: APPROVE

```text
VERDICT: APPROVE
```

One Warning-level issue was found and corrected within this review cycle (see "Revision cycle 1" below); the corrected package passes all checks.

## Constraint Review

- **Holdout exclusion:** PASS. The audit verified `load_analysis_timebars` slices the first 70% by `CloseTime`; null resampling only permutes holdout-excluded rows. No artifact references or inspects the final 30%.
- **Look-ahead / temporal alignment:** PASS. Causal prior-range features (`shift(1)`), forward returns within segment (`shift(-1).over("Segment")`); resampling permutes already-causal observations. No bar-index alignment (no cross-view comparison in scope).
- **Real-price / synthetic-price discipline:** PASS. All returns are real-OHLC log returns; no HA/Renko/Line Break construction price anywhere.
- **Single hypothesis / no scope creep:** PASS. The interpretation and report defer all null-construction amendments to the mid-phase reflection and make no Stage B power, MDE, successor-stack, or closed-thesis-rescue claim.
- **No goalpost moving:** PASS. The outcome is mapped to the predeclared `scope.md` "Evidence AGAINST measurement validity" branch and reported honestly as REFUTED / null-calibration invalidity, not rationalized into a partial success. The untrusted raw rates are explicitly labelled untrusted and bias-suspect, never reported as an FPR.
- **Determinism:** PASS. All RNG seeded from `seed_index`/`block_length`; no wall-clock in the data path.

## Artifact-Specific Review

- **audit.md:** PASS. Thorough (correctness, holdout, look-ahead, NaN/zero-denominator, synthetic-price, faithful transcription); evidence-backed (SC-1..SC-4 with line refs + live reproduction); severity classified (0 Critical / 3 Warning / 5 Info); verdict PASS justified.
- **results.md:** PASS. Honest; quantifies uncertainty and sample sizes; separates evidence from the (clearly-labelled) control-leg hypothesis; verdict supported and mapped to predeclared criteria; §5.6 implication stated as a null-construction finding, not a stack ruling; next steps framed as new experiments via the reflection.
- **report.md:** PASS (after revision). Self-contained; 4 plots embedded with captions; limitations honest; artifacts linked by relative path.
- **Index updates:** PASS. `python/experiments/INDEX.md` row and `docs/experiments-docs/INDEX.md` five-field section are accurate and consistent with `results.md`/`audit.md`; the checkpoint status row documents EXP-037 completion and the routing to the mid-phase reflection without overstating it.

## Revision cycle 1 (resolved)

- **FAILING_ARTIFACT:** `python/experiments/EXP-037/report.md`
- **REQUIRED_SKILL:** experiment-documenter
- **ISSUE (Warning):** "Recommended Next Experiments" reused IDs **EXP-038** and **EXP-039**, which `reference-stack-spec.md` §5 reserves for the Stage B power mechanisms (directional-drift; structural-blindness). This violated the no-reuse ID principle and risked conflating the proposed null-construction fixes with the reserved Stage B power experiments.
- **RESOLUTION:** The recommendations were reworded as unnumbered proposals with an explicit note that the reserved Stage B IDs are not reused and that ID assignment belongs to the reflection. Consistent with `results.md`, which already used unnumbered "New EXP" phrasing. No other artifact reused the reserved IDs.

## Decision

EXP-037 is complete and approved. The experiment correctly reports its predeclared "measurement-validity failure" branch: the harness is validated and faithful to EXP-036, but the predeclared κ=0 null fails its realism diagnostics, so no trusted FPR exists and §5.6 remains unanswered by trusted calibration. Next step is the Phase 006 mid-phase reflection (dated predeclared null-construction amendment) — outside this experiment's scope.
