# Results: Experiment EXP-037 — Null Calibration of Frozen Reference Stack

## Summary

EXP-037 set out to measure the frozen EXP-036 closure stack's false-positive rate (FPR) and per-leg leak profile under a dependence-preserving κ=0 null, across return-stream block lengths L ∈ {20, 60, 240}. The harness is sound and faithfully reproduces the EXP-036 stack (the observed run reproduces EXP-036's `AGAINST` verdict field-for-field). **But no trusted FPR could be produced: the predeclared Part A null fails its own realism diagnostics on 100% of realizations (`DescriptorPass = 0/450`, `ReturnAutocorrPass = 0/450`), so the trusted second-order-holdout denominator is 0 for every block length.** This is the predeclared **"Evidence AGAINST measurement validity"** branch of `scope.md`. Critically, the failure is a **structural property of the null-construction method**, not a code defect and not a property of the market data — which means it is recoverable through a dated predeclared amendment to the null, to be decided at the mid-phase reflection. No trustworthy operating characteristic, and therefore no §5.6 passability ruling, can be issued from this run.

## Detailed Findings

### Finding 1 — The harness measures the right object (faithful transcription)

- **Observation**: With `seed_index = 0`, the harness's observed-stack verdict reproduces EXP-036 exactly.
- **Evidence**: `results/observed_verdict.json` vs `EXP-036/results/verdict.json`: `outcome = AGAINST`; `next_bar_neutral_and_control = {1h:[], 4h:[]}`; `four_bar_neutral_and_control = {1h:[XAUUSD], 4h:[]}`; control adjudicable on all 4 instruments at both timeframes (audit SC-1). Identical load/aggregate/feature/return/bootstrap path; per-cell bootstrap seed identical to EXP-036.
- **Interpretation**: The calibration target is the EXP-036 stack, not an approximation of it. Any FPR this harness *would* produce under a valid null would be attributable to that stack. This precondition for the whole Phase-006 programme is satisfied.

### Finding 2 — The descriptor null fails realism structurally (dominant cause)

- **Observation**: Every realization's descriptor stream violates the ±5% episode-count / ±10% length tolerances; all 16 descriptor cells fail in every realization.
- **Evidence**: `null_diagnostics.csv` / `realization_summary.csv`: `descriptor_max_count_rel_diff` ∈ [0.39, 0.56] (median 0.44), `descriptor_max_median_rel_diff` median 1.0, `descriptor_failed_cells = 16/16` always → `DescriptorPass = 0/450`. Audit SC-2 reproduced the mechanism with the live functions: a 978-episode stream resamples to 632 episodes (−35%), median length 3→4.
- **Interpretation**: Independent episode-block resampling (`_descriptor_indices`) draws whole episodes i.i.d. and concatenates. The observed bucket stream, being maximal runs, has **zero** adjacent same-bucket episodes by construction; i.i.d. block draws create them, and `_episode_ids` **merges** adjacent same-bucket blocks into one episode — collapsing the count and inflating lengths. This is deterministic given ~3 bucket states. The predeclared method (spec §3, "preserving the descriptor's own run/episode structure") does not, in fact, preserve that structure. The diagnostic is working correctly; it is the construction that is unrealistic.

### Finding 3 — The return autocorrelation gate is near-unpassable (independent second cause)

- **Observation**: `ReturnAutocorrPass = 0/450`, independent of the descriptor failure.
- **Evidence**: `_autocorr_compare` requires **zero** sign mismatches across 64 (instrument × timeframe × segment × horizon × lag∈{1,5}) cells; production shows median 12 mismatches (match rate ≈0.81; min 4). 
- **Interpretation**: Lag-1/lag-5 autocorrelations of bar returns are near zero, so their *signs* are noise and flip readily under any resample. A literal "all 64 signs unchanged" gate cannot pass even on a perfectly reasonable return null. Even if Finding 2 were resolved, this gate alone would keep the trusted envelope empty.

### Finding 4 — Empty trusted FPR envelope → predeclared invalidity

- **Observation**: No block length yields a trusted FPR.
- **Evidence**: `fpr_envelope.json`: `trusted_denominator = 0`, `fpr = null`, `valid = 0` for L = 20, 60, 240; `valid_block_lengths = []`. `rate_summary.csv`: every `diagnostic_pass` and `trusted_second_order` denominator is 0. Plot `01_fpr_envelope.png` shows no trusted points; `04_null_diagnostics.png` shows the descriptor and autocorr pass shares at 0 and cross-corr partial.
- **Interpretation**: The headline deliverable (a trusted FPR envelope) does not exist for this null family. Per `scope.md`, this is the **"Evidence AGAINST measurement validity"** outcome — reported as null-calibration invalidity, not as a stack FPR.

### Finding 5 — Untrusted raw behavior (descriptive only; not an FPR)

- **Observation**: Under the raw `all_realizations` set, the stack never false-passes at the full-stack level, while the matched-control leg leaks most at the cell level.
- **Evidence**: `realization_summary.csv`: full-stack `FOR = 0/450` (429 AGAINST, 20 INCONCLUSIVE, 1 STATE_DIFFERENTIATION_ONLY); `rate_summary.csv` full_stack_fpr `0/75` per cell (Wilson upper ≤ 0.049). `leg_rate_summary.csv` next-bar cell-level false-pass (denom 600 = 75 realizations × 8 cells): **control 4.7–6.0%**, **neutral 1.0–2.0%**, both-contrast 0.3–1.2%, roughly flat across L.
- **Interpretation (untrusted, bias-suspect — do NOT read as calibration)**: Two caveats make these numbers uninterpretable as operating characteristics. (a) **Direction bias**: the merged null has fewer, longer episodes → fewer independent bootstrap units → wider test CIs → systematically *harder* to clear "test CI lower > 0," biasing the full-stack FOR rate downward. The 0/450 cannot be read as "the stack has ~0% FPR." (b) **Control-leg structure leak**: `Delta_control = mean((d−c)·r)`; decoupling only the descriptor `d` leaves the control sign `c` paired with `r` in the same resampled block, so `Delta_control ≈ mean(d)·mean(r) − mean(c·r)`, and the preserved `mean(c·r)` (the returns' own momentum/reversal structure) can shift the control contrast off zero. The elevated control-leg cell rate (~5–6% vs the neutral leg's ~1–2%) is therefore plausibly the *control's own preserved structure*, not descriptor→return leakage. This is a **hypothesis for the reflection**, not a trusted finding.

## Hypothesis Verdict

**NOT SUPPORTED — predeclared outcome: null-calibration invalidity ("Evidence AGAINST measurement validity").**

The measurement-success hypothesis required at least one block length with trusted second-order-holdout realizations passing the null-validity gates and a complete trusted FPR. Zero block lengths qualify (Finding 4), driven by two independent realism failures (Findings 2–3). This is a clean predeclared outcome, not an "inconclusive" (the `Inconclusive` branch would require some diagnostics passing on development only; here none pass anywhere). For the experiment index this is best recorded as **REFUTED (measurement-validity branch: predeclared null could not yield a trusted FPR; harness validated, null construction invalid)**.

**§5.6 implication (stated carefully).** Stage A did **not** deliver a trustworthy FPR for the EXP-036 closure stack. The §5.6 question — *is the EXP-036 closure stack passable?* — therefore remains **unanswered by trusted calibration**. This is a **null-construction finding, not a stack-passability ruling**: the stack's only observed behavior here is under an unrealistic, bias-suspect null and cannot support any operating-characteristic claim. No power/MDE/successor-stack inference is made or implied.

## Limitations

- The trusted denominator is 0; all per-leg and verdict-ladder rates are untrusted and (for the full stack) plausibly downward-biased. They are descriptive context for the reflection only.
- A single predeclared null family was tested; its two realism gates both failed, so the experiment characterizes the *gates and the construction*, not the stack.
- Cross-instrument correlation realism partially held (`CrossCorrPass` 0.21→0.36 with L), confirming the return block bootstrap itself behaves sensibly; the failures are specific to the descriptor resampler and the autocorr-sign gate.
- The control-leg mechanism in Finding 5 is an analytic hypothesis, not a measured decomposition.

## Alternative Explanations

- **Could the empty envelope be a genuine "no realistic null exists"?** Unlikely: the merge (Finding 2) and the sign-gate brittleness (Finding 3) are properties of the *method*, not the data; the return-side cross-correlation diagnostic already passes substantially. A realistic null appears achievable with a redesigned descriptor resampler and a noise-aware return gate.
- **Could the 0/450 full-stack FOR reflect a genuinely strict stack?** Plausibly in part — the k=2-instrument conjunction collapses the ~0.5% per-cell both-contrast rate to 0 — but the downward bias (Finding 5a) confounds this, so it cannot be asserted.

## Recommended Next Steps

These are inputs to the **mid-phase reflection**, which (per the reference-stack-spec §6) owns any dated predeclared amendment. They are *not* in-place edits to EXP-037 and must be predeclared before re-running, to avoid post-hoc tuning.

1. **New EXP (amended descriptor null)**: redesign the descriptor resampler to preserve episode structure — e.g., resample episode *labels* under a first-order transition model that forbids same-bucket adjacency (or block the raw bucket sequence without snapping to episodes), then re-verify the ±5%/±10% diagnostics. Predeclare before running.
2. **New EXP (amended return-realism gate)**: replace the zero-mismatch autocorr-sign gate with a noise-floored or mismatch-budgeted criterion (e.g., compare signs only for autocorrelations whose observed magnitude exceeds a stated floor), with non-outcome-driven rationale.
3. **Construct-validity sub-check**: once a valid null exists, decompose `Delta_control` under the null to confirm or refute the Finding-5 control-leg structure hypothesis before reading any control-leg leak as descriptor→return leakage.

No conclusions are drawn about Stage B power, MDE, or any successor stack. The 30% global market holdout remains untouched; all returns are real-OHLC log returns.
